from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.models import (CandidatePassage, Claim, Conjecture, ConjectureEvent, ConjectureStatus, Experiment, Paper,
                        ProofAttempt, Relationship, ResearchRun)
from app.serialize import EXPERIMENT_LIST_EXCLUDE, paper_brief, row
from app.services import conjectures as svc

router = APIRouter(prefix="/api", tags=["conjectures"])


def _actor(user: dict) -> str:
    return f"user:{user.get('email') or user.get('id')}"


def _get(db: Session, ident: str) -> Conjecture:
    c = db.get(Conjecture, ident) or db.scalars(select(Conjecture).where(Conjecture.slug == ident)).first()
    if not c:
        raise HTTPException(404, "Conjecture not found")
    return c


@router.get("/conjectures/meta")
def meta(_: dict = Depends(current_user)):
    return {"fields": svc.FIELDS, "statuses": ConjectureStatus.ALL, "difficulties": svc.DIFFICULTIES,
            "relation_types": ["equivalent_to", "implies", "implied_by", "generalizes", "special_case_of",
                               "disproved_by", "related_to"]}


@router.get("/conjectures")
def list_conjectures(q: str | None = None, field: list[str] | None = Query(None), status: list[str] | None = Query(None),
                     difficulty: list[str] | None = Query(None), from_date: date | None = None, to_date: date | None = None,
                     activity: str | None = Query(None, pattern="^(any|none|experiments)$"),
                     sort: str = Query("updated", pattern="^(updated|created|title|published)$"),
                     db: Session = Depends(get_db), _: dict = Depends(current_user)):
    stmt = select(Conjecture, Paper).outerjoin(Paper, Paper.id == Conjecture.source_paper_id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Conjecture.title).like(like), func.lower(Conjecture.normalized_statement).like(like),
                              func.lower(Conjecture.original_statement).like(like), func.lower(Paper.title).like(like)))
    if field:
        stmt = stmt.where(Conjecture.field.in_(field))
    if status:
        stmt = stmt.where(Conjecture.status.in_(status))
    if difficulty:
        stmt = stmt.where(Conjecture.difficulty_estimate.in_(difficulty))
    if from_date:
        stmt = stmt.where(Paper.published_date >= from_date)
    if to_date:
        stmt = stmt.where(Paper.published_date <= to_date)
    exp_counts = dict(db.execute(select(Experiment.conjecture_id, func.count()).group_by(Experiment.conjecture_id)).all())
    run_counts = dict(db.execute(select(ResearchRun.conjecture_id, func.count()).group_by(ResearchRun.conjecture_id)).all())
    order = {"updated": Conjecture.updated_at.desc(), "created": Conjecture.created_at.desc(),
             "title": Conjecture.title.asc(), "published": Paper.published_date.desc()}[sort]
    items = []
    for c, p in db.execute(stmt.order_by(order)).all():
        n_exp, n_run = exp_counts.get(c.id, 0), run_counts.get(c.id, 0)
        if activity == "none" and (n_exp or n_run):
            continue
        if activity == "any" and not (n_exp or n_run):
            continue
        if activity == "experiments" and not n_exp:
            continue
        d = row(c, exclude={"extraction_details", "source_passage"})
        d["source_paper"] = {"id": p.id, "title": p.title, "authors": p.authors, "published_date":
                             p.published_date.isoformat() if p.published_date else None, "arxiv_id": p.arxiv_id} if p else None
        d["experiment_count"], d["research_run_count"] = n_exp, n_run
        items.append(d)
    return {"items": items, "total": len(items)}


@router.get("/conjectures/{ident}")
def get_conjecture(ident: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    c = _get(db, ident)
    d = row(c)
    d["source_paper"] = paper_brief(c.source_paper, macros=True) if c.source_paper else None
    d["events"] = [row(e) for e in c.events]
    d["experiments"] = [row(e, exclude=EXPERIMENT_LIST_EXCLUDE) for e in db.scalars(
        select(Experiment).where(Experiment.conjecture_id == c.id).order_by(Experiment.created_at.desc()))]
    d["claims"] = [row(x) for x in db.scalars(select(Claim).where(Claim.conjecture_id == c.id))]
    d["proof_attempts"] = [row(x) for x in db.scalars(select(ProofAttempt).where(ProofAttempt.conjecture_id == c.id))]
    d["research_runs"] = [row(x, exclude={"checkpoint", "report_markdown"}) for x in db.scalars(
        select(ResearchRun).where(ResearchRun.conjecture_id == c.id))]
    rels = db.scalars(select(Relationship).where(or_(Relationship.from_id == c.id, Relationship.to_id == c.id))).all()
    titles = dict(db.execute(select(Conjecture.id, Conjecture.title)).all())
    d["relationships"] = [{**row(r), "from_title": titles.get(r.from_id), "to_title": titles.get(r.to_id)} for r in rels]
    # Other open problems in the same source paper (for "related literature").
    if c.source_paper_id:
        d["siblings"] = [{"id": x.id, "slug": x.slug, "title": x.title, "status": x.status} for x in db.scalars(
            select(Conjecture).where(Conjecture.source_paper_id == c.source_paper_id, Conjecture.id != c.id))]
        d["source_candidates"] = [row(x, exclude={"context_before", "context_after"}) for x in db.scalars(
            select(CandidatePassage).where(CandidatePassage.paper_id == c.source_paper_id,
                                           CandidatePassage.review_status == "pending"))]
    return d


class ConjectureIn(BaseModel):
    title: str = Field(..., min_length=3)
    field: str
    subfields: list[str] = []
    problem_type: str = "conjecture"
    original_statement: str
    normalized_statement: str
    definitions: list[dict] = []
    notation: str | None = None
    source_paper_id: str | None = None
    source_passage: str | None = None
    source_page: int | None = None
    source_section: str | None = None
    known_results: list[dict] = []
    potential_approaches: list[str] = []
    relevant_theorems: list[str] = []
    difficulty_estimate: str | None = None
    difficulty_rationale: str | None = None


@router.post("/conjectures")
def create(body: ConjectureIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    if body.source_paper_id and not db.get(Paper, body.source_paper_id):
        raise HTTPException(422, "source_paper_id does not exist")
    try:
        c = svc.create_conjecture(db, body.model_dump(), actor=_actor(user))
    except svc.ConjectureError as e:
        raise HTTPException(422, str(e)) from e
    db.commit()
    return row(c)


@router.post("/candidates/{candidate_id}/accept")
def accept_candidate(candidate_id: str, body: ConjectureIn, db: Session = Depends(get_db),
                     user: dict = Depends(current_user)):
    cand = db.get(CandidatePassage, candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")
    if cand.review_status == "accepted":
        raise HTTPException(409, "Candidate already accepted")
    data = body.model_dump()
    data["source_paper_id"] = cand.paper_id
    if cand.llm_assessment and cand.detector.startswith("llm:"):
        data["extraction_details"] = {"extracted_by": cand.detector, "assessment": cand.llm_assessment}
    else:
        data["extraction_details"] = {"extracted_by": "heuristic+human", "trigger": cand.trigger}
    try:
        c = svc.create_conjecture(db, data, actor=_actor(user), candidate=cand)
    except svc.ConjectureError as e:
        raise HTTPException(422, str(e)) from e
    db.commit()
    return row(c)


class PatchIn(BaseModel):
    changes: dict
    note: str | None = None


@router.patch("/conjectures/{ident}")
def patch(ident: str, body: PatchIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    c = _get(db, ident)
    try:
        svc.update_conjecture(db, c, body.changes, actor=_actor(user), note=body.note)
    except svc.ConjectureError as e:
        raise HTTPException(422, str(e)) from e
    db.commit()
    return row(c)


class StatusIn(BaseModel):
    status: str
    rationale: str = Field(..., min_length=10)
    evidence: list[dict] = []
    confidence: float | None = Field(None, ge=0, le=1)


@router.post("/conjectures/{ident}/status")
def override_status(ident: str, body: StatusIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    c = _get(db, ident)
    try:
        svc.set_status(db, c, body.status, actor=_actor(user), rationale=body.rationale, evidence=body.evidence,
                       manual=True, confidence=body.confidence)
    except svc.ConjectureError as e:
        raise HTTPException(422, str(e)) from e
    db.commit()
    return row(c)


class NoteIn(BaseModel):
    text: str = Field(..., min_length=3)


@router.post("/conjectures/{ident}/notes")
def add_note(ident: str, body: NoteIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    c = _get(db, ident)
    ev = ConjectureEvent(conjecture_id=c.id, event_type="note", actor=_actor(user), summary=body.text)
    db.add(ev)
    db.commit()
    return row(ev)


class RelationIn(BaseModel):
    relation_type: str
    to_conjecture_id: str | None = None
    to_external: str | None = None
    note: str | None = None
    source_paper_id: str | None = None


@router.post("/conjectures/{ident}/relationships")
def add_relation(ident: str, body: RelationIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    c = _get(db, ident)
    types = {"equivalent_to", "implies", "implied_by", "generalizes", "special_case_of", "disproved_by", "related_to"}
    if body.relation_type not in types:
        raise HTTPException(422, f"relation_type must be one of {sorted(types)}")
    if not body.to_conjecture_id and not (body.to_external or "").strip():
        raise HTTPException(422, "Give either to_conjecture_id or to_external")
    if body.to_conjecture_id and not db.get(Conjecture, body.to_conjecture_id):
        raise HTTPException(422, "to_conjecture_id does not exist")
    r = Relationship(relation_type=body.relation_type, from_type="conjecture", from_id=c.id,
                     to_type="conjecture" if body.to_conjecture_id else "external", to_id=body.to_conjecture_id,
                     to_external=body.to_external, note=body.note, source_paper_id=body.source_paper_id,
                     created_by=_actor(user))
    db.add(r)
    db.add(ConjectureEvent(conjecture_id=c.id, event_type="edit", actor=_actor(user),
                           summary=f"Added relationship: {body.relation_type} {body.to_external or body.to_conjecture_id}"))
    db.commit()
    return row(r)
