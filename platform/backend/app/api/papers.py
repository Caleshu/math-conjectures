from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.jobs.queue import enqueue
from app.llm.registry import available_providers
from app.models import CandidatePassage, Job, Paper, PaperPage
from app.serialize import CANDIDATE_LIST_EXCLUDE, PAPER_DETAIL_EXCLUDE, paper_brief, row
from app.services.papers import find_existing, record_from_dict, upsert_paper
from app.sources.base import SearchQuery
from app.sources.identifiers import parse_identifier
from app.sources.registry import SOURCES, federated_search

router = APIRouter(prefix="/api", tags=["papers"], dependencies=[Depends(current_user)])


# ------------------------------------------------------------------------------------------
# Discovery search
# ------------------------------------------------------------------------------------------
class SearchIn(BaseModel):
    text: str = ""
    subject: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    sources: list[str] = Field(default_factory=lambda: ["arxiv", "openalex", "crossref", "semantic_scholar"])
    limit: int = Field(20, ge=1, le=100)


@router.post("/discovery/search")
def search(body: SearchIn, db: Session = Depends(get_db)):
    if not body.text.strip() and not body.subject and not (body.from_date or body.to_date):
        raise HTTPException(422, "Provide keywords, a subject, or a date range.")
    unknown = [s for s in body.sources if s not in SOURCES]
    if unknown:
        raise HTTPException(422, f"Unknown sources: {unknown}. Available: {list(SOURCES)}")
    recs, errors = federated_search(
        SearchQuery(text=body.text, subject=body.subject, from_date=body.from_date, to_date=body.to_date,
                    limit=body.limit), body.sources)
    out = []
    for r in recs:
        d = r.to_dict()
        d["merged_sources"] = r.raw.get("merged_sources", [r.source])
        existing = find_existing(db, r)
        d["indexed_paper_id"] = existing.id if existing else None
        out.append(d)
    return {"results": out, "source_errors": errors, "count": len(out)}


class ImportIn(BaseModel):
    records: list[dict]
    process: bool = True


@router.post("/discovery/import")
def import_records(body: ImportIn, db: Session = Depends(get_db)):
    """Add search results to the index and queue them for PDF retrieval + scanning."""
    out = []
    for d in body.records:
        rec = record_from_dict(d)
        if not rec.title:
            continue
        paper, created = upsert_paper(db, rec, "search")
        job_id = None
        if body.process and not paper.pages:
            job_id = enqueue(db, "process_paper", {"paper_id": paper.id}, subject_type="paper", subject_id=paper.id).id
        out.append({"paper_id": paper.id, "created": created, "job_id": job_id, "title": paper.title})
    db.commit()
    return {"imported": out}


class SubmitIn(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=2000)


@router.post("/papers/submit")
def submit(body: SubmitIn, db: Session = Depends(get_db)):
    ident = parse_identifier(body.identifier)
    if ident.kind == "unknown":
        raise HTTPException(422, "Unrecognised identifier. Use an arXiv ID or URL, a DOI or doi.org URL, an "
                                 "OpenAlex work ID (W…), or a direct PDF URL.")
    job = enqueue(db, "ingest_identifier", {"identifier": body.identifier, "discovered_via": "manual"},
                  subject_type="identifier")
    db.commit()
    return {"job_id": job.id, "parsed": {"kind": ident.kind, "value": ident.value}}


# ------------------------------------------------------------------------------------------
# Papers
# ------------------------------------------------------------------------------------------
@router.get("/papers")
def list_papers(q: str | None = None, status: str | None = None, limit: int = Query(50, le=200),
                offset: int = 0, db: Session = Depends(get_db)):
    stmt = select(Paper)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Paper.title).like(like), Paper.arxiv_id == q.strip(),
                              Paper.doi == q.strip().lower()))
    if status:
        stmt = stmt.where(Paper.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    papers = db.scalars(stmt.order_by(Paper.created_at.desc()).limit(limit).offset(offset)).all()
    counts = dict(db.execute(select(CandidatePassage.paper_id, func.count()).where(
        CandidatePassage.paper_id.in_([p.id for p in papers])).group_by(CandidatePassage.paper_id)).all())
    items = []
    for p in papers:
        d = paper_brief(p)
        d["candidate_count"] = counts.get(p.id, 0)
        items.append(d)
    return {"items": items, "total": total}


def _paper_or_404(db: Session, paper_id: str) -> Paper:
    p = db.get(Paper, paper_id)
    if not p:
        raise HTTPException(404, "Paper not found")
    return p


@router.get("/papers/{paper_id}")
def get_paper(paper_id: str, db: Session = Depends(get_db)):
    p = _paper_or_404(db, paper_id)
    d = row(p, exclude=PAPER_DETAIL_EXCLUDE)
    d["has_latex"] = bool(p.latex_source)
    from app.extraction.latex_macros import extract_macros

    d["latex_macros"] = extract_macros(p.latex_source)
    d["candidates"] = [row(c) for c in sorted(p.candidates, key=lambda c: (c.detector == "heuristic", -(c.score or 0)))]
    d["jobs"] = [row(j) for j in db.scalars(select(Job).where(Job.subject_id == paper_id).order_by(Job.created_at.desc()).limit(10))]
    d["llm_available"] = available_providers()
    return d


@router.get("/papers/{paper_id}/pages/{page_number}")
def get_page(paper_id: str, page_number: int, db: Session = Depends(get_db)):
    pg = db.scalars(select(PaperPage).where(PaperPage.paper_id == paper_id, PaperPage.page_number == page_number)).first()
    if not pg:
        raise HTTPException(404, "Page not extracted")
    return {"paper_id": paper_id, "page_number": page_number, "text": pg.text}


@router.get("/papers/{paper_id}/pdf")
def get_pdf(paper_id: str, db: Session = Depends(get_db)):
    p = _paper_or_404(db, paper_id)
    if not p.pdf_path or not Path(p.pdf_path).exists():
        raise HTTPException(404, "PDF not stored for this paper")
    return FileResponse(p.pdf_path, media_type="application/pdf", filename=f"{p.arxiv_id or p.id}.pdf")


@router.get("/papers/{paper_id}/latex", response_class=PlainTextResponse)
def get_latex(paper_id: str, db: Session = Depends(get_db)):
    p = _paper_or_404(db, paper_id)
    if not p.latex_source:
        raise HTTPException(404, "No LaTeX source stored for this paper")
    return p.latex_source


@router.post("/papers/{paper_id}/process")
def reprocess(paper_id: str, db: Session = Depends(get_db)):
    _paper_or_404(db, paper_id)
    job = enqueue(db, "process_paper", {"paper_id": paper_id}, subject_type="paper", subject_id=paper_id)
    db.commit()
    return {"job_id": job.id}


class ExtractIn(BaseModel):
    provider: str | None = None


@router.post("/papers/{paper_id}/extract")
def llm_extract(paper_id: str, body: ExtractIn, db: Session = Depends(get_db)):
    p = _paper_or_404(db, paper_id)
    providers = available_providers()
    if not providers:
        raise HTTPException(409, "No AI provider available. Install and log in to Claude Code (uses your "
                                 "Claude subscription), or set ANTHROPIC_API_KEY / OPENAI_API_KEY, then restart the API.")
    if body.provider and body.provider not in providers:
        raise HTTPException(409, f"Provider '{body.provider}' is not configured. Configured: {providers}")
    if not (p.pages or p.latex_source):
        raise HTTPException(409, "Paper has no extracted text yet. Process the paper first.")
    job = enqueue(db, "llm_extract", {"paper_id": paper_id, "provider": body.provider}, subject_type="paper",
                  subject_id=paper_id, max_attempts=2)
    db.commit()
    return {"job_id": job.id}


# ------------------------------------------------------------------------------------------
# Candidates
# ------------------------------------------------------------------------------------------
@router.get("/candidates")
def list_candidates(review_status: str | None = "pending", paper_id: str | None = None, kind: str | None = None,
                    min_score: float = 0.0, limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    stmt = select(CandidatePassage, Paper.title, Paper.arxiv_id, Paper.latex_source).join(Paper, Paper.id == CandidatePassage.paper_id)
    if review_status:
        stmt = stmt.where(CandidatePassage.review_status == review_status)
    if paper_id:
        stmt = stmt.where(CandidatePassage.paper_id == paper_id)
    if kind:
        stmt = stmt.where(CandidatePassage.kind == kind)
    stmt = stmt.where(func.coalesce(CandidatePassage.score, 0) >= min_score)
    rows = db.execute(stmt.order_by(CandidatePassage.score.desc(), CandidatePassage.created_at.desc()).limit(limit)).all()
    from app.extraction.latex_macros import extract_macros

    out, macro_cache = [], {}
    for c, title, arxiv_id, latex in rows:
        d = row(c, exclude=CANDIDATE_LIST_EXCLUDE)
        d["paper_title"], d["paper_arxiv_id"] = title, arxiv_id
        if c.paper_id not in macro_cache:
            macro_cache[c.paper_id] = extract_macros(latex)
        d["paper_macros"] = macro_cache[c.paper_id]
        out.append(d)
    return {"items": out}


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    c = db.get(CandidatePassage, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    d = row(c)
    d["paper"] = paper_brief(c.paper, macros=True)
    return d


class RejectIn(BaseModel):
    note: str | None = None


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(candidate_id: str, body: RejectIn, db: Session = Depends(get_db)):
    c = db.get(CandidatePassage, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    c.review_status = "rejected"
    c.review_note = body.note
    db.commit()
    return row(c)


@router.get("/papers/{paper_id}/citing")
def citing_works(paper_id: str, limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    """Works citing this paper, from the OpenAlex citation graph. Also checks the published
    (non-arXiv) version when OpenAlex lists one under the same title, since citations are often
    attached to the journal record rather than the preprint."""
    p = _paper_or_404(db, paper_id)
    oa = SOURCES["openalex"]
    ids: list[str] = []
    if p.openalex_id:
        ids.append(p.openalex_id)
    from app.sources.base import SourceError
    from app.sources.identifiers import normalize_title
    errors = []
    try:
        data = oa.search(SearchQuery(text=p.title, limit=10))
        ids += [r.openalex_id for r in data if r.openalex_id and normalize_title(r.title) == p.normalized_title
                and r.openalex_id not in ids]
    except SourceError as e:
        errors.append(str(e))
    results, seen = [], set()
    for wid in ids:
        try:
            for r in oa.citing_works(wid, limit):
                key = r.doi or r.openalex_id
                if key in seen:
                    continue
                seen.add(key)
                d = r.to_dict()
                existing = find_existing(db, r)
                d["indexed_paper_id"] = existing.id if existing else None
                d["via"] = f"openalex:{wid}"
                results.append(d)
        except SourceError as e:
            errors.append(str(e))
    s2_ident = f"arXiv:{p.arxiv_id}" if p.arxiv_id else (f"DOI:{p.doi}" if p.doi else None)
    if s2_ident:
        try:
            for r in SOURCES["semantic_scholar"].citations(s2_ident, limit):
                key = r.doi or r.semantic_scholar_id
                if key in seen or (r.title and any(normalize_title(r.title) == normalize_title(x["title"]) for x in results)):
                    continue
                seen.add(key)
                d = r.to_dict()
                existing = find_existing(db, r)
                d["indexed_paper_id"] = existing.id if existing else None
                d["via"] = "semantic_scholar"
                results.append(d)
        except SourceError as e:
            errors.append(str(e))
    return {"paper_id": paper_id, "openalex_ids_checked": ids, "results": results, "errors": errors,
            "note": "OpenAlex citation coverage for mathematics is incomplete; absence of citing works is not evidence "
                    "that the problem is open."}
