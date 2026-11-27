"""Paper ingestion: identifier resolution, deduplication, PDF/LaTeX retrieval, text extraction,
candidate scanning. Each stage is idempotent so an interrupted job can simply be re-run."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from collections.abc import Callable
from datetime import date

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.extraction.candidates import detect_candidates
from app.models import CandidatePassage, Paper, PaperPage, PaperStatus
from app.pdf.extract import extract_pdf, fetch_arxiv_source
from app.sources.base import PaperRecord, SourceError
from app.sources.identifiers import normalize_title, parse_identifier
from app.sources.registry import SOURCES, merge_records

log = logging.getLogger(__name__)
MAX_PDF_BYTES = 60_000_000

Progress = Callable[[str, dict | None], None]


class IngestError(Exception):
    pass


# ------------------------------------------------------------------------------------------
# Resolution
# ------------------------------------------------------------------------------------------
def resolve_identifier(raw: str) -> PaperRecord:
    ident = parse_identifier(raw)
    if ident.kind == "arxiv":
        rec = SOURCES["arxiv"].get(ident.value)
        if not rec:
            raise IngestError(f"arXiv has no paper with id {ident.value}")
        try:  # enrich with OpenAlex (citation graph, references, venue)
            oa = SOURCES["openalex"].find_arxiv(ident.value, rec.title)
            if oa:
                merge_records(rec, oa)
                rec.openalex_id = oa.openalex_id
        except SourceError as e:
            rec.raw["enrichment_error"] = str(e)
        return rec
    if ident.kind == "doi":
        rec = None
        errors = []
        for src in ("openalex", "crossref"):
            try:
                r = SOURCES[src].get_by_doi(ident.value) if src == "openalex" else SOURCES[src].get(ident.value)
            except SourceError as e:
                errors.append(str(e))
                continue
            if r:
                rec = merge_records(rec, r) if rec else r
        if not rec:
            raise IngestError(f"DOI {ident.value} not found ({'; '.join(errors) or 'no source returned it'})")
        if rec.arxiv_id:
            a = SOURCES["arxiv"].get(rec.arxiv_id)
            if a:
                rec = merge_records(a, rec)
        return rec
    if ident.kind == "openalex":
        rec = SOURCES["openalex"].get(ident.value)
        if not rec:
            raise IngestError(f"OpenAlex has no work {ident.value}")
        return rec
    if ident.kind == "url":
        # A direct link to a PDF (or something else). We only accept it if it serves a PDF.
        return PaperRecord(source="url", title="", landing_url=ident.value, pdf_url=ident.value,
                           is_open_access=None, raw={"submitted_url": ident.value})
    raise IngestError("Could not recognise the identifier. Use an arXiv ID (e.g. 1009.3304), an arXiv/doi.org "
                      "URL, a DOI (10.xxxx/...), an OpenAlex ID (W...), or a direct PDF URL.")


# ------------------------------------------------------------------------------------------
# Dedup + upsert
# ------------------------------------------------------------------------------------------
def find_existing(db: Session, rec: PaperRecord) -> Paper | None:
    conds = []
    if rec.doi:
        conds.append(Paper.doi == rec.doi)
    if rec.arxiv_id:
        conds.append(Paper.arxiv_id == rec.arxiv_id)
        conds.append(Paper.doi == f"10.48550/arxiv.{rec.arxiv_id}")
    if rec.openalex_id:
        conds.append(Paper.openalex_id == rec.openalex_id)
    if rec.semantic_scholar_id:
        conds.append(Paper.semantic_scholar_id == rec.semantic_scholar_id)
    if rec.title:
        conds.append(Paper.normalized_title == normalize_title(rec.title))
    if rec.pdf_url and rec.source == "url":
        conds.append(Paper.pdf_url == rec.pdf_url)
    if not conds:
        return None
    return db.scalars(select(Paper).where(or_(*conds)).limit(1)).first()


def upsert_paper(db: Session, rec: PaperRecord, discovered_via: str) -> tuple[Paper, bool]:
    """Returns (paper, created). Existing papers get missing fields filled, never overwritten."""
    existing = find_existing(db, rec)
    fields = dict(
        title=rec.title, authors=rec.authors, abstract=rec.abstract, doi=rec.doi, arxiv_id=rec.arxiv_id,
        openalex_id=rec.openalex_id, semantic_scholar_id=rec.semantic_scholar_id,
        published_date=rec.published_date, venue=rec.venue, categories=rec.categories,
        landing_url=rec.landing_url, pdf_url=rec.pdf_url, is_open_access=rec.is_open_access,
        license=rec.license, cited_by_count=rec.cited_by_count, references=rec.references,
    )
    if existing:
        for k, v in fields.items():
            cur = getattr(existing, k)
            if v not in (None, "", []) and cur in (None, "", []):
                # Unique identifiers: only fill if no other row already owns them.
                if k in ("doi", "arxiv_id", "openalex_id", "semantic_scholar_id") and db.scalar(
                        select(Paper.id).where(getattr(Paper, k) == v, Paper.id != existing.id)):
                    continue
                setattr(existing, k, v)
        if existing.title and not existing.normalized_title:
            existing.normalized_title = normalize_title(existing.title)
        meta = dict(existing.source_metadata or {})
        meta.setdefault("sources", [])
        for s in rec.raw.get("merged_sources", [rec.source]):
            if s not in meta["sources"]:
                meta["sources"].append(s)
        existing.source_metadata = meta
        return existing, False
    title = rec.title or "(untitled — pending PDF metadata)"
    p = Paper(**{k: v for k, v in fields.items() if v is not None or k in ("abstract",)},
              normalized_title=normalize_title(title), discovered_via=discovered_via,
              source_metadata={"sources": rec.raw.get("merged_sources", [rec.source]),
                               **{k: v for k, v in rec.raw.items() if k != "merged_sources"}})
    p.title = title
    p.authors = rec.authors or []
    p.categories = rec.categories or []
    p.references = rec.references or []
    db.add(p)
    db.flush()
    return p, True


# ------------------------------------------------------------------------------------------
# Processing stages
# ------------------------------------------------------------------------------------------
def download_pdf(paper: Paper) -> None:
    if paper.pdf_path:
        return
    if not paper.pdf_url:
        paper.status = PaperStatus.NO_PDF
        paper.processing_error = "No open-access PDF location is known for this paper."
        return
    if paper.is_open_access is False:
        paper.status = PaperStatus.NO_PDF
        paper.processing_error = "Paper is not open access; PDF not retrieved."
        return
    s = get_settings()
    try:
        with httpx.stream("GET", paper.pdf_url, headers={"User-Agent": s.http_user_agent},
                          timeout=90, follow_redirects=True) as r:
            if r.status_code != 200:
                raise IngestError(f"PDF download failed: HTTP {r.status_code} from {paper.pdf_url}")
            chunks, total = [], 0
            for chunk in r.iter_bytes():
                total += len(chunk)
                if total > MAX_PDF_BYTES:
                    raise IngestError("PDF exceeds 60 MB limit")
                chunks.append(chunk)
    except httpx.HTTPError as e:
        raise IngestError(f"PDF download failed: {e}") from e
    blob = b"".join(chunks)
    if not blob.startswith(b"%PDF"):
        raise IngestError(f"URL did not return a PDF (got {blob[:20]!r}...). It may be a landing page or paywall.")
    path = s.pdf_dir / f"{paper.id}.pdf"
    path.write_bytes(blob)
    paper.pdf_path = str(path)
    paper.pdf_sha256 = hashlib.sha256(blob).hexdigest()
    paper.status = PaperStatus.PDF_DOWNLOADED


def extract_text(db: Session, paper: Paper) -> dict:
    from pathlib import Path

    if page_texts(db, paper.id):
        return {"sections": (paper.source_metadata or {}).get("sections", [])}
    ex = extract_pdf(Path(paper.pdf_path))
    for i, t in enumerate(ex.pages, 1):
        db.add(PaperPage(paper_id=paper.id, page_number=i, text=t))
    paper.page_count = len(ex.pages)
    paper.text_extractor = ex.extractor
    paper.source_metadata = {**(paper.source_metadata or {}), "sections": ex.sections}
    if paper.title.startswith("(untitled") and ex.pages:
        first = next((ln.strip() for ln in ex.pages[0].splitlines() if len(ln.strip()) > 10), None)
        if first:
            paper.title = first[:300]
            paper.normalized_title = normalize_title(paper.title)
            paper.source_metadata = {**paper.source_metadata, "title_guessed_from_pdf": True}
    paper.status = PaperStatus.TEXT_EXTRACTED
    db.flush()
    return {"sections": ex.sections}


def fetch_latex(paper: Paper) -> None:
    if not paper.arxiv_id or paper.latex_source or (paper.source_metadata or {}).get("latex_checked"):
        return
    try:
        tex, names = fetch_arxiv_source(paper.arxiv_id)
    except SourceError as e:
        paper.source_metadata = {**(paper.source_metadata or {}), "latex_error": str(e)}
        return
    paper.latex_source = tex
    paper.latex_files = names
    paper.source_metadata = {**(paper.source_metadata or {}), "latex_checked": True}


def page_texts(db: Session, paper_id: str) -> list[str]:
    return list(db.scalars(select(PaperPage.text).where(PaperPage.paper_id == paper_id).order_by(PaperPage.page_number)))


def scan_candidates(db: Session, paper: Paper) -> int:
    pages = page_texts(db, paper.id)
    sections = (paper.source_metadata or {}).get("sections", [])
    found = detect_candidates(pages, paper.latex_source, sections, paper.abstract)
    existing = {(c.origin, c.char_start): c for c in db.scalars(
        select(CandidatePassage).where(CandidatePassage.paper_id == paper.id, CandidatePassage.detector == "heuristic"))}
    n = 0
    for c in found:
        prev = existing.get((c.origin, c.char_start))
        if prev:  # re-scan: fill in location data that may have been unavailable before
            prev.page_number = prev.page_number or c.page_number
            prev.section = prev.section or c.section
            continue
        db.add(CandidatePassage(
            paper_id=paper.id, page_number=c.page_number, section=c.section, origin=c.origin, label=c.label,
            char_start=c.char_start, passage=c.passage, context_before=c.context_before,
            context_after=c.context_after, trigger=c.trigger, kind=c.kind, detector="heuristic", score=c.score,
        ))
        n += 1
    paper.status = PaperStatus.SCANNED
    db.flush()
    return n


def process_paper(db: Session, paper_id: str, progress: Progress) -> dict:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise IngestError(f"paper {paper_id} not found")
    paper.processing_error = None
    progress("downloading_pdf", None)
    try:
        download_pdf(paper)
    except IngestError as e:
        paper.processing_error = str(e)
        paper.status = PaperStatus.FAILED if paper.status != PaperStatus.NO_PDF else paper.status
        db.commit()
    db.commit()
    if paper.pdf_path and Path(paper.pdf_path).exists():
        progress("extracting_text", None)
        extract_text(db, paper)
        db.commit()
    progress("fetching_latex", None)
    fetch_latex(paper)
    db.commit()
    progress("scanning_candidates", None)
    has_pages = bool(page_texts(db, paper.id))
    n = scan_candidates(db, paper) if (has_pages or paper.latex_source or paper.abstract) else 0
    if not has_pages and paper.status == PaperStatus.SCANNED and paper.processing_error:
        paper.status = PaperStatus.NO_PDF
    db.commit()
    return {"paper_id": paper.id, "pages": paper.page_count, "latex": bool(paper.latex_source),
            "new_candidates": n, "status": paper.status, "error": paper.processing_error}


def record_from_dict(d: dict) -> PaperRecord:
    d = dict(d)
    if d.get("published_date"):
        d["published_date"] = date.fromisoformat(d["published_date"])
    d.pop("raw", None)
    d.setdefault("source", "search")
    allowed = PaperRecord.__dataclass_fields__.keys()
    return PaperRecord(**{k: v for k, v in d.items() if k in allowed})
