"""Job handlers. Each takes (job_id, payload, progress) and returns a JSON-serialisable result.
Raise `NonRetryable` for failures that retrying cannot fix (bad input, missing credentials)."""
from __future__ import annotations

import hashlib
from collections.abc import Callable

from app.config import get_settings
from app.db import SessionLocal, session_scope
from app.llm.base import LLMBudgetExceeded, LLMUnavailable
from app.models import ConjectureEvent, Experiment, utcnow
from app.sandbox.runner import run_python
from app.services import papers as paper_service
from app.sources.base import SourceError


class NonRetryable(Exception):
    pass


def ingest_identifier(job_id: str, payload: dict, progress: Callable) -> dict:
    progress("resolving_identifier", {"identifier": payload["identifier"]})
    try:
        rec = paper_service.resolve_identifier(payload["identifier"])
    except paper_service.IngestError as e:
        raise NonRetryable(str(e)) from e
    with session_scope() as db:
        paper, created = paper_service.upsert_paper(db, rec, payload.get("discovered_via", "manual"))
        pid = paper.id
    progress("paper_recorded", {"paper_id": pid, "created": created})
    db = SessionLocal()
    try:
        out = paper_service.process_paper(db, pid, progress)
    finally:
        db.close()
    out["created"] = created
    return out


def process_paper(job_id: str, payload: dict, progress: Callable) -> dict:
    db = SessionLocal()
    try:
        return paper_service.process_paper(db, payload["paper_id"], progress)
    except SourceError as e:
        raise RuntimeError(str(e)) from e
    finally:
        db.close()


def llm_extract(job_id: str, payload: dict, progress: Callable) -> dict:
    from app.extraction.llm_extractor import extract_with_llm

    progress("calling_model", None)
    db = SessionLocal()
    try:
        return extract_with_llm(db, payload["paper_id"], job_id=job_id, provider=payload.get("provider"))
    except (LLMUnavailable, LLMBudgetExceeded, ValueError) as e:
        raise NonRetryable(str(e)) from e
    finally:
        db.close()


def run_experiment(job_id: str, payload: dict, progress: Callable) -> dict:
    eid = payload["experiment_id"]
    with session_scope() as db:
        exp = db.get(Experiment, eid)
        if exp.status in ("succeeded", "failed", "timeout"):
            return {"experiment_id": eid, "status": exp.status, "note": "already finished"}
        exp.status = "running"
        exp.started_at = utcnow()
        code, params, settings = exp.code, dict(exp.parameters), dict(exp.settings)
        if hashlib.sha256(code.encode()).hexdigest() != exp.code_sha256:
            raise NonRetryable("stored code hash mismatch; refusing to run modified code")
    progress("executing_in_sandbox", None)
    s = get_settings()
    res = run_python(code, params, s.experiments_dir / eid,
                     timeout_s=settings.get("timeout_s", s.sandbox_default_timeout_s),
                     memory_mb=settings.get("memory_mb", s.sandbox_default_memory_mb))
    with session_scope() as db:
        exp = db.get(Experiment, eid)
        exp.status = res.status
        exp.exit_code = res.exit_code
        exp.stdout = res.stdout
        exp.stderr = res.stderr
        exp.result = res.result
        exp.runtime_seconds = res.runtime_seconds
        exp.environment = res.environment
        exp.finished_at = utcnow()
        if exp.conjecture_id:
            db.add(ConjectureEvent(
                conjecture_id=exp.conjecture_id, event_type="experiment", actor=exp.created_by,
                summary=f"Experiment '{exp.title}' {res.status} in {res.runtime_seconds:.1f}s",
                details={"experiment_id": eid, "status": res.status,
                         "summary": (res.result or {}).get("summary") if isinstance(res.result, dict) else None}))
    return {"experiment_id": eid, "status": res.status, "runtime_seconds": res.runtime_seconds}


def research_run(job_id: str, payload: dict, progress: Callable) -> dict:
    from app.research.orchestrator import Orchestrator
    rid = payload["research_run_id"]
    with session_scope() as db:
        from app.models import ResearchRun
        r = db.get(ResearchRun, rid)
        if r is None:
            raise NonRetryable("research run no longer exists")
        if r.status in ("completed", "cancelled"):
            return {"research_run_id": rid, "status": r.status, "note": "already finished"}
    return {"research_run_id": rid, **Orchestrator(rid, job_id, progress).run()}


HANDLERS: dict[str, Callable] = {
    "research_run": research_run,
    "ingest_identifier": ingest_identifier,
    "process_paper": process_paper,
    "llm_extract": llm_extract,
    "run_experiment": run_experiment,
}
