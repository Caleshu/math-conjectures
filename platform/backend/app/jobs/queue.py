"""A small durable job queue stored in the application database.

Why not Celery/RQ: those need Redis or RabbitMQ. Jobs here are few and long-running, and keeping
them in Postgres means one fewer service, transactional enqueueing, and trivially resumable work:
a job whose worker died (no heartbeat for JOB_STALE_AFTER_SECONDS) is put back in the queue.

Claiming uses an optimistic `UPDATE ... WHERE status='queued'` and checks the row count, which is
safe on both Postgres and SQLite with several workers.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import session_scope
from app.models import Job, utcnow


def enqueue(db: Session, job_type: str, payload: dict, *, subject_type: str | None = None,
            subject_id: str | None = None, max_attempts: int = 3) -> Job:
    job = Job(job_type=job_type, payload=payload, subject_type=subject_type, subject_id=subject_id,
              max_attempts=max_attempts, progress={"stage": "queued"})
    db.add(job)
    db.flush()
    return job


def claim_next(worker_id: str, job_types: list[str] | None = None) -> str | None:
    with session_scope() as db:
        q = select(Job.id).where(Job.status == "queued", Job.run_after <= utcnow())
        if job_types:
            q = q.where(Job.job_type.in_(job_types))
        candidates = db.scalars(q.order_by(Job.created_at).limit(5)).all()
        for jid in candidates:
            res = db.execute(
                update(Job).where(Job.id == jid, Job.status == "queued").values(
                    status="running", locked_by=worker_id, heartbeat_at=utcnow(), started_at=utcnow(),
                    attempts=Job.attempts + 1)
            )
            if res.rowcount == 1:
                return jid
    return None


def heartbeat(job_id: str, stage: str | None = None, info: dict | None = None) -> None:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if not job:
            return
        job.heartbeat_at = utcnow()
        if stage is not None:
            prog = dict(job.progress or {})
            prog["stage"] = stage
            if info:
                prog.update(info)
            job.progress = prog


def complete(job_id: str, result: dict) -> None:
    with session_scope() as db:
        job = db.get(Job, job_id)
        job.status = "succeeded"
        job.result = result
        job.error = None
        job.finished_at = utcnow()
        job.progress = {**(job.progress or {}), "stage": "done"}


def fail(job_id: str, error: str, *, retryable: bool) -> None:
    with session_scope() as db:
        job = db.get(Job, job_id)
        job.error = error[:8000]
        if retryable and job.attempts < job.max_attempts:
            job.status = "queued"
            job.locked_by = None
            job.run_after = utcnow() + timedelta(seconds=15 * 2 ** job.attempts)
            job.progress = {**(job.progress or {}), "stage": f"retrying (attempt {job.attempts} failed)"}
        else:
            job.status = "failed"
            job.finished_at = utcnow()
            job.progress = {**(job.progress or {}), "stage": "failed"}


def requeue_stale() -> int:
    """Resume jobs abandoned by a crashed/stopped worker."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=get_settings().job_stale_after_seconds)
    with session_scope() as db:
        stale = db.scalars(select(Job).where(Job.status == "running", Job.heartbeat_at < cutoff)).all()
        for j in stale:
            if j.attempts < j.max_attempts:
                j.status = "queued"
                j.locked_by = None
                j.progress = {**(j.progress or {}), "stage": "resumed after interruption"}
            else:
                j.status = "failed"
                j.error = (j.error or "") + "\nworker stopped responding and attempts are exhausted"
                j.finished_at = utcnow()
        return len(stale)


def requeue_interrupted_on_startup(worker_id_prefix: str) -> int:
    """When a single embedded worker restarts, its previous 'running' jobs are definitely dead."""
    with session_scope() as db:
        rows = db.scalars(select(Job).where(Job.status == "running",
                                            Job.locked_by.like(f"{worker_id_prefix}%"))).all()
        for j in rows:
            j.status = "queued"
            j.locked_by = None
            j.progress = {**(j.progress or {}), "stage": "resumed after restart"}
        return len(rows)
