"""Persistent research knowledge base.

Design notes
- Every row that represents a mathematical assertion keeps *who* produced it (`created_by`),
  *what evidence* supports it, and a *verification status*. Nothing is stored as bare fact.
- Original wording and normalized statements are separate columns and the original is never
  rewritten after creation (enforced in the service layer).
- Tables for Milestones 3-6 (claims, proof attempts, research runs, agent tasks, relations) exist
  now so the schema supports the knowledge graph from the start.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, JSONType


def _uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


# ------------------------------------------------------------------------------------------
# Papers
# ------------------------------------------------------------------------------------------
class PaperStatus:
    METADATA = "metadata_only"
    PDF_DOWNLOADED = "pdf_downloaded"
    TEXT_EXTRACTED = "text_extracted"
    SCANNED = "scanned"  # candidate passages detected
    FAILED = "failed"
    NO_PDF = "no_pdf_available"


class Paper(TimestampMixin, Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    authors: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    openalex_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    semantic_scholar_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    abstract: Mapped[str | None] = mapped_column(Text)
    published_date: Mapped[date | None] = mapped_column(Date)
    venue: Mapped[str | None] = mapped_column(Text)
    categories: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    landing_url: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    pdf_path: Mapped[str | None] = mapped_column(Text)
    pdf_sha256: Mapped[str | None] = mapped_column(String(64))
    is_open_access: Mapped[bool | None] = mapped_column(Boolean)
    license: Mapped[str | None] = mapped_column(Text)
    references: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    cited_by_count: Mapped[int | None] = mapped_column(Integer)
    discovered_via: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PaperStatus.METADATA, nullable=False)
    processing_error: Mapped[str | None] = mapped_column(Text)
    text_extractor: Mapped[str | None] = mapped_column(String(64))
    page_count: Mapped[int | None] = mapped_column(Integer)
    # arXiv LaTeX source (main .tex content, flattened). Gives exact wording of statements.
    latex_source: Mapped[str | None] = mapped_column(Text)
    latex_files: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    source_metadata: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    pages: Mapped[list[PaperPage]] = relationship(
        back_populates="paper", cascade="all, delete-orphan", order_by="PaperPage.page_number"
    )
    candidates: Mapped[list[CandidatePassage]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )


class PaperPage(Base):
    __tablename__ = "paper_pages"
    __table_args__ = (UniqueConstraint("paper_id", "page_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-indexed PDF page
    text: Mapped[str] = mapped_column(Text, nullable=False)

    paper: Mapped[Paper] = relationship(back_populates="pages")


# ------------------------------------------------------------------------------------------
# Candidate passages: possible open problems detected in a paper, awaiting review
# ------------------------------------------------------------------------------------------
class CandidatePassage(TimestampMixin, Base):
    __tablename__ = "candidate_passages"
    __table_args__ = (UniqueConstraint("paper_id", "origin", "char_start", "detector"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(16), default="pdf", nullable=False)  # pdf | latex | abstract
    label: Mapped[str | None] = mapped_column(Text)  # e.g. "Conjecture 5.1" or LaTeX \label
    char_start: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passage: Mapped[str] = mapped_column(Text, nullable=False)  # exact text from the paper
    context_before: Mapped[str | None] = mapped_column(Text)
    context_after: Mapped[str | None] = mapped_column(Text)
    trigger: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    # "heuristic" or "llm:<provider>:<model>"
    detector: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    # pending | accepted | rejected
    review_status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text)
    llm_assessment: Mapped[dict | None] = mapped_column(JSONType)
    conjecture_id: Mapped[str | None] = mapped_column(ForeignKey("conjectures.id", ondelete="SET NULL"))

    paper: Mapped[Paper] = relationship(back_populates="candidates")


# ------------------------------------------------------------------------------------------
# Conjectures
# ------------------------------------------------------------------------------------------
class ConjectureStatus:
    VERIFIED_OPEN = "VERIFIED_OPEN"
    LIKELY_OPEN = "LIKELY_OPEN"
    UNVERIFIED = "UNVERIFIED"
    SOLVED = "SOLVED"
    DISPROVED = "DISPROVED"
    SUPERSEDED = "SUPERSEDED"
    ALL = [VERIFIED_OPEN, LIKELY_OPEN, UNVERIFIED, SOLVED, DISPROVED, SUPERSEDED]


class Conjecture(TimestampMixin, Base):
    __tablename__ = "conjectures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    field: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subfields: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    problem_type: Mapped[str] = mapped_column(String(32), default="conjecture", nullable=False)
    # Verbatim wording from the source. Immutable after creation.
    original_statement: Mapped[str] = mapped_column(Text, nullable=False)
    # LaTeX-capable restatement; may be edited, edits are logged in history.
    normalized_statement: Mapped[str] = mapped_column(Text, nullable=False)
    definitions: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)  # [{term, definition}]
    notation: Mapped[str | None] = mapped_column(Text)

    source_paper_id: Mapped[str | None] = mapped_column(ForeignKey("papers.id", ondelete="SET NULL"), index=True)
    source_passage: Mapped[str | None] = mapped_column(Text)
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_section: Mapped[str | None] = mapped_column(Text)
    source_candidate_id: Mapped[str | None] = mapped_column(String(36))

    # [{statement, source_paper_id?, citation, evidence_passage?, page?, reproduced: bool, note?}]
    known_results: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    potential_approaches: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    relevant_theorems: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)

    status: Mapped[str] = mapped_column(String(24), default=ConjectureStatus.UNVERIFIED, nullable=False, index=True)
    verification_confidence: Mapped[float | None] = mapped_column(Float)
    status_is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    difficulty_estimate: Mapped[str | None] = mapped_column(String(32))
    difficulty_rationale: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[str] = mapped_column(String(128), default="user", nullable=False)
    extraction_details: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    source_paper: Mapped[Paper | None] = relationship(foreign_keys=[source_paper_id])
    events: Mapped[list[ConjectureEvent]] = relationship(
        back_populates="conjecture", cascade="all, delete-orphan", order_by="ConjectureEvent.created_at"
    )


class ConjectureEvent(Base):
    """Research history: status changes (with evidence), manual overrides, edits, runs, experiments."""
    __tablename__ = "conjecture_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conjecture_id: Mapped[str] = mapped_column(ForeignKey("conjectures.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)  # created|status_change|override|edit|experiment|note
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(24))
    new_status: Mapped[str | None] = mapped_column(String(24))
    evidence: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    details: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    conjecture: Mapped[Conjecture] = relationship(back_populates="events")


class Relationship(TimestampMixin, Base):
    """Edges of the future knowledge graph between conjectures, claims and external theorems."""
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # equivalent_to | implies | implied_by | generalizes | special_case_of | disproved_by | related_to
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_type: Mapped[str] = mapped_column(String(16), nullable=False)  # conjecture | claim | paper
    from_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    to_type: Mapped[str] = mapped_column(String(16), nullable=False)  # conjecture | claim | paper | external
    to_id: Mapped[str | None] = mapped_column(String(36), index=True)
    to_external: Mapped[str | None] = mapped_column(Text)
    source_paper_id: Mapped[str | None] = mapped_column(ForeignKey("papers.id", ondelete="SET NULL"))
    created_by: Mapped[str] = mapped_column(String(128), default="user", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(24), default="unverified", nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


# ------------------------------------------------------------------------------------------
# Claims, proof attempts, research runs (schema for Milestones 3-6)
# ------------------------------------------------------------------------------------------
class ValidationLevel:
    IDEA = 1
    EXPERIMENTAL_EVIDENCE = 2
    FINITE_COMPUTATIONAL_RESULT = 3
    WRITTEN_PROOF_ATTEMPT = 4
    INDEPENDENTLY_REVIEWED_PROOF = 5
    FORMALLY_VERIFIED_PROOF = 6  # only set when Lean accepts the theorem


class Claim(TimestampMixin, Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conjecture_id: Mapped[str | None] = mapped_column(ForeignKey("conjectures.id", ondelete="CASCADE"), index=True)
    research_run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"))
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(32), nullable=False)  # lemma|observation|counterexample|reduction|bound|...
    validation_level: Mapped[int] = mapped_column(Integer, default=ValidationLevel.IDEA, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(24), default="unverified", nullable=False)
    evidence: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    source_paper_id: Mapped[str | None] = mapped_column(ForeignKey("papers.id", ondelete="SET NULL"))
    experiment_id: Mapped[str | None] = mapped_column(ForeignKey("experiments.id", ondelete="SET NULL"))
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)


class ProofAttempt(TimestampMixin, Base):
    __tablename__ = "proof_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conjecture_id: Mapped[str] = mapped_column(ForeignKey("conjectures.id", ondelete="CASCADE"), nullable=False, index=True)
    research_run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"))
    strategy: Mapped[str] = mapped_column(Text, nullable=False)
    argument: Mapped[str] = mapped_column(Text, nullable=False)
    lemma_claim_ids: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    known_gaps: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    reviewer_feedback: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    validation_level: Mapped[int] = mapped_column(Integer, default=ValidationLevel.WRITTEN_PROOF_ATTEMPT, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    lean_artifact: Mapped[dict | None] = mapped_column(JSONType)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)


class ResearchRun(TimestampMixin, Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conjecture_id: Mapped[str] = mapped_column(ForeignKey("conjectures.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False)  # queued|running|completed|failed|cancelled
    limits: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checkpoint: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    report_markdown: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentTask(TimestampMixin, Base):
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    research_run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_role: Mapped[str] = mapped_column(String(48), nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    current_task: Mapped[str | None] = mapped_column(Text)
    input: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSONType)
    report_markdown: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)


# ------------------------------------------------------------------------------------------
# Experiments
# ------------------------------------------------------------------------------------------
class Experiment(TimestampMixin, Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conjecture_id: Mapped[str | None] = mapped_column(ForeignKey("conjectures.id", ondelete="SET NULL"), index=True)
    research_run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    code_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    library_script: Mapped[str | None] = mapped_column(String(128))
    parameters: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)  # timeout, memory
    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False)  # queued|running|succeeded|failed|timeout
    exit_code: Mapped[int | None] = mapped_column(Integer)
    stdout: Mapped[str | None] = mapped_column(Text)
    stderr: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSONType)
    runtime_seconds: Mapped[float | None] = mapped_column(Float)
    environment: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)  # versions, isolation used
    # finite_computation | heuristic_search | exploratory ; never "proof"
    result_kind: Mapped[str] = mapped_column(String(32), default="finite_computation", nullable=False)
    interpretation: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(128), default="user", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ------------------------------------------------------------------------------------------
# Jobs & usage
# ------------------------------------------------------------------------------------------
class Job(TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_status_run_after", "status", "run_after"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_type: Mapped[str] = mapped_column(String(48), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False)  # queued|running|succeeded|failed|cancelled
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    progress: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONType)
    error: Mapped[str | None] = mapped_column(Text)
    locked_by: Mapped[str | None] = mapped_column(String(128))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    subject_type: Mapped[str | None] = mapped_column(String(32))
    subject_id: Mapped[str | None] = mapped_column(String(36), index=True)


class LLMUsage(Base):
    __tablename__ = "llm_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    job_id: Mapped[str | None] = mapped_column(String(36))
    subject_id: Mapped[str | None] = mapped_column(String(36))
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SourceRequestLog(Base):
    """External API call log (rate-limit debugging and usage tracking)."""
    __tablename__ = "source_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
