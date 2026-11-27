from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CandidatePassage, Conjecture, ConjectureEvent, ConjectureStatus

FIELDS = ["graph_theory", "combinatorics", "extremal_combinatorics", "discrete_mathematics", "number_theory",
          "algebra", "geometry", "other"]
DIFFICULTIES = ["accessible", "moderate", "hard", "very_hard", "unknown"]
EDITABLE = {"title", "field", "subfields", "normalized_statement", "definitions", "notation", "known_results",
            "potential_approaches", "relevant_theorems", "difficulty_estimate", "difficulty_rationale", "problem_type",
            "source_section", "source_page"}
# These describe provenance and must not change after creation.
IMMUTABLE = {"original_statement", "source_paper_id", "source_passage", "source_candidate_id", "created_by"}


class ConjectureError(Exception):
    pass


def slugify(db: Session, title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80] or "conjecture"
    slug, i = base, 2
    while db.scalar(select(Conjecture.id).where(Conjecture.slug == slug)):
        slug, i = f"{base}-{i}", i + 1
    return slug


def create_conjecture(db: Session, data: dict, *, actor: str, candidate: CandidatePassage | None = None) -> Conjecture:
    if not data.get("original_statement", "").strip():
        raise ConjectureError("original_statement is required (verbatim wording from the source)")
    if not data.get("normalized_statement", "").strip():
        raise ConjectureError("normalized_statement is required")
    if data.get("field") not in FIELDS:
        raise ConjectureError(f"field must be one of {FIELDS}")
    if data.get("difficulty_estimate") and data["difficulty_estimate"] not in DIFFICULTIES:
        raise ConjectureError(f"difficulty_estimate must be one of {DIFFICULTIES}")
    c = Conjecture(
        slug=slugify(db, data["title"]), title=data["title"], field=data["field"],
        subfields=data.get("subfields") or [], problem_type=data.get("problem_type") or "conjecture",
        original_statement=data["original_statement"], normalized_statement=data["normalized_statement"],
        definitions=data.get("definitions") or [], notation=data.get("notation"),
        source_paper_id=data.get("source_paper_id") or (candidate.paper_id if candidate else None),
        source_passage=data.get("source_passage") or (candidate.passage if candidate else None),
        source_page=data.get("source_page") or (candidate.page_number if candidate else None),
        source_section=data.get("source_section") or (candidate.section if candidate else None),
        source_candidate_id=candidate.id if candidate else None,
        known_results=data.get("known_results") or [], potential_approaches=data.get("potential_approaches") or [],
        relevant_theorems=data.get("relevant_theorems") or [],
        status=ConjectureStatus.UNVERIFIED, difficulty_estimate=data.get("difficulty_estimate"),
        difficulty_rationale=data.get("difficulty_rationale"), created_by=actor,
        extraction_details=data.get("extraction_details") or {},
    )
    db.add(c)
    db.flush()
    db.add(ConjectureEvent(
        conjecture_id=c.id, event_type="created", actor=actor, new_status=c.status,
        summary="Conjecture record created" + (f" from candidate passage ({candidate.detector})" if candidate else ""),
        details={"candidate_id": candidate.id if candidate else None},
    ))
    if candidate:
        candidate.review_status = "accepted"
        candidate.conjecture_id = c.id
    return c


def update_conjecture(db: Session, c: Conjecture, changes: dict, *, actor: str, note: str | None) -> Conjecture:
    bad = set(changes) & IMMUTABLE
    if bad:
        raise ConjectureError(f"These fields record provenance and cannot be edited: {sorted(bad)}")
    unknown = set(changes) - EDITABLE
    if unknown:
        raise ConjectureError(f"Unknown or non-editable fields: {sorted(unknown)}")
    if "field" in changes and changes["field"] not in FIELDS:
        raise ConjectureError(f"field must be one of {FIELDS}")
    if changes.get("difficulty_estimate") and changes["difficulty_estimate"] not in DIFFICULTIES:
        raise ConjectureError(f"difficulty_estimate must be one of {DIFFICULTIES}")
    diff = {}
    for k, v in changes.items():
        old = getattr(c, k)
        if old != v:
            diff[k] = {"from": old, "to": v}
            setattr(c, k, v)
    if diff:
        db.add(ConjectureEvent(conjecture_id=c.id, event_type="edit", actor=actor,
                               summary=note or f"Edited {', '.join(diff)}", details={"changes": diff}))
    return c


def set_status(db: Session, c: Conjecture, status: str, *, actor: str, rationale: str, evidence: list,
               manual: bool, confidence: float | None = None) -> Conjecture:
    if status not in ConjectureStatus.ALL:
        raise ConjectureError(f"status must be one of {ConjectureStatus.ALL}")
    if not rationale.strip():
        raise ConjectureError("A status change requires an explanation")
    if status == ConjectureStatus.VERIFIED_OPEN and not evidence and not manual:
        raise ConjectureError("VERIFIED_OPEN requires evidence; absence of a found solution is not enough")
    prev = c.status
    c.status = status
    c.status_is_manual_override = manual
    if confidence is not None:
        c.verification_confidence = confidence
    db.add(ConjectureEvent(conjecture_id=c.id, event_type="override" if manual else "status_change", actor=actor,
                           previous_status=prev, new_status=status, summary=rationale, evidence=evidence,
                           details={"confidence": confidence}))
    return c
