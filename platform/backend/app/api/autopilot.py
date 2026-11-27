"""Autopilot control and GitHub export status."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.autopilot import ELIGIBLE, load_state, note, save_state
from app.config import get_settings
from app.db import get_db
from app.export import request_export
from app.models import Conjecture, Job, ResearchRun
from app.serialize import row

router = APIRouter(prefix="/api/autopilot", tags=["autopilot"])


@router.get("")
def status(db: Session = Depends(get_db), _: dict = Depends(current_user)):
    st = load_state()
    s = get_settings()
    researched = set(db.scalars(select(ResearchRun.conjecture_id)))
    queue, skipped = [], []
    for c in db.scalars(select(Conjecture).order_by(Conjecture.created_at)):
        ap = (c.extraction_details or {}).get("autopilot", {})
        brief = {"id": c.id, "slug": c.slug, "title": c.title, "status": c.status,
                 "precheck": ap.get("precheck", {}).get("verdict"), "reason": ap.get("precheck", {}).get("reason")}
        if ap.get("skipped"):
            skipped.append(brief)
        elif c.status in ELIGIBLE and c.id not in researched:
            queue.append(brief)
    jobs = db.scalars(select(Job).where(Job.job_type == "export_repo").order_by(Job.created_at.desc()).limit(5)).all()
    return {"enabled": bool(st.get("enabled")), "cooldown_until": st.get("cooldown_until"), "blocked": st.get("blocked"),
            "last_action": st.get("last_action"), "last_error": st.get("last_error"), "current": st.get("current"),
            "waiting": st.get("waiting"), "limits": st.get("limits") or {}, "log": list(reversed(st.get("log", [])))[:40],
            "queue": queue, "skipped": skipped,
            "export": {"enabled": s.repo_export_enabled, "remote": s.repo_export_remote, "branch": s.repo_export_branch,
                       "last": st.get("last_export"), "jobs": [row(j, exclude={"payload"}) for j in jobs]}}


class ToggleIn(BaseModel):
    enabled: bool | None = None
    limits: dict | None = None


@router.post("")
def toggle(body: ToggleIn, _: dict = Depends(current_user)):
    st = load_state()
    if body.enabled is not None:
        from datetime import datetime, timezone
        st["enabled"] = body.enabled
        st["control_at"] = datetime.now(timezone.utc).isoformat()
        st.pop("cooldown_until", None)
        note(st, "autopilot enabled" if body.enabled else "autopilot paused (the current run, if any, continues)")
    if body.limits is not None:
        st["limits"] = body.limits
    save_state(st)
    return {"enabled": st["enabled"], "limits": st.get("limits") or {}}


@router.post("/export")
def export_now(db: Session = Depends(get_db), _: dict = Depends(current_user)):
    queued = request_export(db)
    db.commit()
    return {"queued": queued}
