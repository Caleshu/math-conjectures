from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import get_settings, integration_status
from app.db import get_db
from app.llm.registry import available_providers, default_provider
from app.models import (CandidatePassage, Conjecture, ConjectureEvent, ConjectureStatus, Experiment, Job, LLMUsage, Paper,
                        ResearchRun, SourceRequestLog)
from app.serialize import row

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: dict = Depends(current_user)):
    count = lambda stmt: db.scalar(stmt) or 0  # noqa: E731
    status_counts = dict(db.execute(select(Conjecture.status, func.count()).group_by(Conjecture.status)).all())
    recent = db.scalars(select(Conjecture).order_by(Conjecture.created_at.desc()).limit(6)).all()
    events = db.execute(select(ConjectureEvent, Conjecture.title, Conjecture.slug)
                        .join(Conjecture, Conjecture.id == ConjectureEvent.conjecture_id)
                        .order_by(ConjectureEvent.created_at.desc()).limit(12)).all()
    jobs = db.scalars(select(Job).order_by(Job.updated_at.desc()).limit(10)).all()
    return {
        "counts": {
            "papers_indexed": count(select(func.count(Paper.id))),
            "papers_with_text": count(select(func.count(Paper.id)).where(Paper.page_count > 0)),
            "conjectures": count(select(func.count(Conjecture.id))),
            "candidates_pending": count(select(func.count(CandidatePassage.id)).where(CandidatePassage.review_status == "pending")),
            "awaiting_verification": status_counts.get(ConjectureStatus.UNVERIFIED, 0),
            "active_research_runs": count(select(func.count(ResearchRun.id)).where(ResearchRun.status.in_(["queued", "running"]))),
            "completed_research_runs": count(select(func.count(ResearchRun.id)).where(ResearchRun.status == "completed")),
            "experiments": count(select(func.count(Experiment.id))),
            "jobs_active": count(select(func.count(Job.id)).where(Job.status.in_(["queued", "running"]))),
        },
        "status_breakdown": status_counts,
        "recent_conjectures": [{"id": c.id, "slug": c.slug, "title": c.title, "field": c.field, "status": c.status,
                                "created_at": c.created_at.isoformat()} for c in recent],
        "activity": [{"id": e.id, "type": e.event_type, "summary": e.summary, "actor": e.actor,
                      "created_at": e.created_at.isoformat(), "conjecture_title": t, "conjecture_slug": s}
                     for e, t, s in events],
        "jobs": [row(j, exclude={"payload"}) for j in jobs],
    }


@router.get("/jobs")
def list_jobs(status: str | None = None, subject_id: str | None = None, limit: int = Query(50, le=200),
              db: Session = Depends(get_db), _: dict = Depends(current_user)):
    stmt = select(Job)
    if status:
        stmt = stmt.where(Job.status == status)
    if subject_id:
        stmt = stmt.where(Job.subject_id == subject_id)
    return {"items": [row(j) for j in db.scalars(stmt.order_by(Job.created_at.desc()).limit(limit))]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    j = db.get(Job, job_id)
    if not j:
        raise HTTPException(404, "Job not found")
    return row(j)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    j = db.get(Job, job_id)
    if not j:
        raise HTTPException(404, "Job not found")
    if j.status != "queued":
        raise HTTPException(409, f"Only queued jobs can be cancelled (job is {j.status})")
    j.status = "cancelled"
    db.commit()
    return row(j)


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    j = db.get(Job, job_id)
    if not j:
        raise HTTPException(404, "Job not found")
    if j.status not in ("failed", "cancelled"):
        raise HTTPException(409, f"Only failed or cancelled jobs can be retried (job is {j.status})")
    j.status, j.attempts, j.error, j.locked_by = "queued", 0, None, None
    j.progress = {"stage": "queued (manual retry)"}
    db.commit()
    return row(j)


@router.get("/settings")
def settings(_: dict = Depends(current_user)):
    s = get_settings()
    return {
        "integrations": integration_status(),
        "llm": {"available_providers": available_providers(), "default_provider": default_provider() or "none",
                "anthropic_model": s.anthropic_model, "claude_code_model": s.claude_code_model, "openai_model": s.openai_model, "budget_usd": s.llm_budget_usd},
        "sandbox": {"default_timeout_s": s.sandbox_default_timeout_s, "max_timeout_s": s.sandbox_max_timeout_s,
                    "default_memory_mb": s.sandbox_default_memory_mb},
        "auth": {"require_auth": s.require_auth, "supabase_configured": bool(s.supabase_url or s.supabase_jwt_secret)},
        "worker": {"embedded": s.run_embedded_worker},
    }


@router.get("/usage")
def usage(db: Session = Depends(get_db), _: dict = Depends(current_user)):
    by_model = db.execute(select(LLMUsage.provider, LLMUsage.model, LLMUsage.purpose, func.count(),
                                 func.sum(LLMUsage.input_tokens), func.sum(LLMUsage.output_tokens),
                                 func.sum(LLMUsage.cost_usd))
                          .group_by(LLMUsage.provider, LLMUsage.model, LLMUsage.purpose)).all()
    sources = db.execute(select(SourceRequestLog.source, func.count(),
                                func.sum(case((SourceRequestLog.status_code >= 400, 1),
                                              (SourceRequestLog.status_code.is_(None), 1), else_=0)))
                         .group_by(SourceRequestLog.source)).all()
    total = db.scalar(select(func.coalesce(func.sum(LLMUsage.cost_usd), 0.0))) or 0.0
    return {
        "llm_total_usd": round(float(total), 4), "llm_budget_usd": get_settings().llm_budget_usd,
        "llm": [{"provider": p, "model": m, "purpose": pu, "calls": n, "input_tokens": i or 0, "output_tokens": o or 0,
                 "cost_usd": round(float(c or 0), 4)} for p, m, pu, n, i, o, c in by_model],
        "sources": [{"source": s, "requests": n, "errors": int(e or 0)} for s, n, e in sources],
    }


@router.get("/research/runs")
def research_runs(db: Session = Depends(get_db), _: dict = Depends(current_user)):
    runs = db.scalars(select(ResearchRun).order_by(ResearchRun.created_at.desc())).all()
    return {"items": [row(r, exclude={"checkpoint", "report_markdown"}) for r in runs],
            "orchestrator_available": False,
            "note": "The multi-agent research orchestrator is Milestone 4 and is not implemented yet."}
