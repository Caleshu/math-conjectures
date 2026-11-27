"""GitHub export: debounced job requests and change detection."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models import ConjectureEvent, Experiment, Job, ResearchRun


def request_export(db) -> bool:
    """Queue one export job unless one is already waiting."""
    from app.config import get_settings
    from app.jobs.queue import enqueue
    if not get_settings().repo_export_enabled:
        return False
    if db.scalar(select(Job.id).where(Job.job_type == "export_repo", Job.status == "queued")):
        return False
    enqueue(db, "export_repo", {}, subject_type="repo", max_attempts=3)
    return True


def latest_change(db) -> datetime | None:
    vals = [db.scalar(select(func.max(ConjectureEvent.created_at))),
            db.scalar(select(func.max(ResearchRun.updated_at)).where(ResearchRun.status.in_(["completed", "failed", "cancelled"]))),
            db.scalar(select(func.max(Experiment.updated_at)).where(Experiment.status.in_(["succeeded", "failed", "timeout"])))]
    vals = [v.replace(tzinfo=v.tzinfo or timezone.utc) for v in vals if v]
    return max(vals) if vals else None
