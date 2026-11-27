"""Research Lab API: launch, monitor, cancel/resume research runs; reports (JSON + Markdown)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.jobs.queue import enqueue
from app.llm.registry import available_providers, default_provider
from app.models import (AgentTask, Claim, Conjecture, ConjectureEvent, Experiment, Job, LLMUsage, ProofAttempt,
                        ResearchRun)
from app.research.agents import AGENTS
from app.research.orchestrator import DEFAULT_LIMITS, LIMIT_BOUNDS, normalize_limits
from app.research.report import build_report, to_markdown
from app.serialize import row

router = APIRouter(prefix="/api/research", tags=["research"])


def _usage(db, run_id):
    calls, tin, tout = db.execute(select(func.count(LLMUsage.id), func.coalesce(func.sum(LLMUsage.input_tokens), 0),
                                         func.coalesce(func.sum(LLMUsage.output_tokens), 0))
                                  .where(LLMUsage.subject_id == run_id)).one()
    n_exp = db.scalar(select(func.count(Experiment.id)).where(Experiment.research_run_id == run_id))
    return {"model_calls": int(calls), "tokens": int(tin) + int(tout), "experiments": int(n_exp or 0)}


def _brief(db, r: ResearchRun) -> dict:
    c = db.get(Conjecture, r.conjecture_id)
    d = row(r, exclude={"report_markdown"})
    d["conjecture"] = {"id": c.id, "slug": c.slug, "title": c.title, "status": c.status} if c else None
    d["usage"] = _usage(db, r.id)
    d["claim_count"] = db.scalar(select(func.count(Claim.id)).where(Claim.research_run_id == r.id))
    return d


@router.get("/meta")
def meta(_: dict = Depends(current_user)):
    return {"agents": [{"role": k, "name": v["name"], "description": v["short"]} for k, v in AGENTS.items()],
            "default_limits": DEFAULT_LIMITS, "limit_bounds": LIMIT_BOUNDS,
            "providers": available_providers(), "default_provider": default_provider()}


@router.get("/runs")
def list_runs(conjecture_id: str | None = None, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    q = select(ResearchRun).order_by(ResearchRun.created_at.desc())
    if conjecture_id:
        q = q.where(ResearchRun.conjecture_id == conjecture_id)
    return {"items": [_brief(db, r) for r in db.scalars(q)], "orchestrator_available": True,
            "providers": available_providers()}


class LaunchIn(BaseModel):
    conjecture_id: str
    limits: dict = {}


@router.post("/runs")
def launch(body: LaunchIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    c = db.get(Conjecture, body.conjecture_id) or db.scalar(select(Conjecture).where(Conjecture.slug == body.conjecture_id))
    if not c:
        raise HTTPException(404, "conjecture not found")
    if not available_providers():
        raise HTTPException(409, "No AI provider available. Install and log in to Claude Code, or set ANTHROPIC_API_KEY.")
    limits = normalize_limits(body.limits)
    if limits.get("provider") and limits["provider"] not in available_providers():
        raise HTTPException(409, f"provider {limits['provider']} is not configured")
    active = db.scalar(select(ResearchRun).where(ResearchRun.conjecture_id == c.id,
                                                 ResearchRun.status.in_(["queued", "running", "cancelling"])))
    if active:
        raise HTTPException(409, f"A research run is already active for this conjecture ({active.id}).")
    run = ResearchRun(conjecture_id=c.id, status="queued", limits=limits, checkpoint={"phase": "queued"})
    db.add(run)
    db.flush()
    job = enqueue(db, "research_run", {"research_run_id": run.id}, subject_type="research_run", subject_id=run.id,
                  max_attempts=2)
    run.checkpoint = {"phase": "queued", "job_id": job.id}
    db.add(ConjectureEvent(conjecture_id=c.id, event_type="research_run", actor=f"user:{user.get('id', 'local')}",
                           summary="Research run launched", details={"research_run_id": run.id, "limits": limits}))
    db.commit()
    return _brief(db, run)


def _run_or_404(db, run_id) -> ResearchRun:
    r = db.get(ResearchRun, run_id)
    if not r:
        raise HTTPException(404, "research run not found")
    return r


@router.get("/runs/{run_id}")
def detail(run_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    r = _run_or_404(db, run_id)
    d = _brief(db, r)
    d["tasks"] = [row(t) for t in db.scalars(select(AgentTask).where(AgentTask.research_run_id == r.id)
                                             .order_by(AgentTask.iteration, AgentTask.created_at))]
    d["claims"] = [row(x) for x in db.scalars(select(Claim).where(Claim.research_run_id == r.id).order_by(Claim.created_at))]
    d["proof_attempts"] = [row(x) for x in db.scalars(select(ProofAttempt).where(ProofAttempt.research_run_id == r.id)
                                                      .order_by(ProofAttempt.created_at))]
    d["experiments"] = [row(x, exclude={"code", "stdout", "stderr", "parameters"}) for x in db.scalars(
        select(Experiment).where(Experiment.research_run_id == r.id).order_by(Experiment.created_at))]
    jid = (r.checkpoint or {}).get("job_id")
    j = db.get(Job, jid) if jid else None
    d["job"] = row(j, exclude={"payload"}) if j else None
    d["agents"] = {k: {"name": v["name"], "description": v["short"]} for k, v in AGENTS.items()}
    return d


@router.post("/runs/{run_id}/cancel")
def cancel(run_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    r = _run_or_404(db, run_id)
    if r.status == "queued":
        jid = (r.checkpoint or {}).get("job_id")
        j = db.get(Job, jid) if jid else None
        if j and j.status == "queued":
            j.status = "cancelled"
        r.status = "cancelled"
    elif r.status == "running":
        r.status = "cancelling"  # the orchestrator stops at its next checkpoint and still writes a report
    else:
        raise HTTPException(409, f"run is {r.status}")
    db.commit()
    return _brief(db, r)


@router.post("/runs/{run_id}/resume")
def resume(run_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    r = _run_or_404(db, run_id)
    if r.status not in ("failed", "cancelled"):
        raise HTTPException(409, f"only failed or cancelled runs can be resumed (run is {r.status})")
    r.status, r.error, r.finished_at = "queued", None, None
    r.checkpoint = {**(r.checkpoint or {}), "first_started_at": (r.checkpoint or {}).get("first_started_at") or (r.started_at.isoformat() if r.started_at else None)}
    r.started_at = None  # restart the runtime clock on resume
    job = enqueue(db, "research_run", {"research_run_id": r.id}, subject_type="research_run", subject_id=r.id,
                  max_attempts=2)
    cp = {k: v for k, v in (r.checkpoint or {}).items() if k not in ("stop_reason", "agent_errors", "usage")}
    r.checkpoint = {**cp, "phase": "resuming", "job_id": job.id,
                    "resumed_after": (r.checkpoint or {}).get("stop_reason")}
    db.commit()
    return _brief(db, r)


@router.get("/runs/{run_id}/report")
def report(run_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    return build_report(db, _run_or_404(db, run_id))


@router.get("/runs/{run_id}/report.md", response_class=PlainTextResponse)
def report_md(run_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    r = _run_or_404(db, run_id)
    md = to_markdown(build_report(db, r))
    return PlainTextResponse(md, media_type="text/markdown; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="research-report-{r.id[:8]}.md"'})
