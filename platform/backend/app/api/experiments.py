from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import BACKEND_DIR, get_settings
from app.db import get_db
from app.jobs.queue import enqueue
from app.models import Conjecture, ConjectureEvent, Experiment, Job
from app.serialize import EXPERIMENT_LIST_EXCLUDE, row

router = APIRouter(prefix="/api/experiments", tags=["experiments"])
LIB_DIR = BACKEND_DIR / "experiments" / "library"

# Library scripts with their default parameters. Code is read from disk at submission time and
# stored (with its hash) on the experiment, so later edits to the file never change old records.
LIBRARY = {
    "hypercube_inscribed_squares": {
        "title": "Square-free Hamiltonian cycles in Q_n (enumeration + CP-SAT)",
        "problem": "Search for a Hamiltonian cycle of Q_n containing no two opposite edges of any 4-cycle "
                   "(a counterexample to the inscribed-squares conjecture).",
        "default_parameters": {"enumerate_n": [2, 3, 4], "cpsat_n": [2, 3, 4, 5, 6], "min_squares_n": [2, 3, 4],
                               "time_limit_s": 300, "workers": 8, "seed": 0},
        "default_timeout_s": 900,
        "result_kind": "finite_computation",
        "applies_to_tags": ["hypercube", "hamiltonian"],
    },
}


def _doc(path: Path) -> str:
    import ast

    try:
        return ast.get_docstring(ast.parse(path.read_text())) or ""
    except SyntaxError:
        return ""


@router.get("/library")
def library(_: dict = Depends(current_user)):
    out = []
    for key, meta in LIBRARY.items():
        p = LIB_DIR / f"{key}.py"
        out.append({"key": key, **meta, "description": _doc(p), "available": p.exists()})
    return {"items": out}


@router.get("/library/{key}/code")
def library_code(key: str, _: dict = Depends(current_user)):
    p = LIB_DIR / f"{key}.py"
    if key not in LIBRARY or not p.exists():
        raise HTTPException(404, "Unknown library script")
    return {"key": key, "code": p.read_text()}


class ExperimentIn(BaseModel):
    title: str = Field(..., min_length=3)
    problem: str = Field(..., min_length=3)
    conjecture_id: str | None = None
    library_script: str | None = None
    code: str | None = None
    parameters: dict = {}
    timeout_s: int | None = Field(None, ge=1)
    memory_mb: int | None = Field(None, ge=64, le=65536)
    result_kind: str = Field("finite_computation", pattern="^(finite_computation|heuristic_search|exploratory)$")


@router.post("")
def create(body: ExperimentIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    s = get_settings()
    if body.conjecture_id and not db.get(Conjecture, body.conjecture_id):
        raise HTTPException(422, "conjecture_id does not exist")
    if bool(body.library_script) == bool(body.code):
        raise HTTPException(422, "Provide exactly one of library_script or code")
    if body.library_script:
        p = LIB_DIR / f"{body.library_script}.py"
        if body.library_script not in LIBRARY or not p.exists():
            raise HTTPException(422, "Unknown library script")
        code = p.read_text()
    else:
        code = body.code
    if len(code) > 500_000:
        raise HTTPException(422, "Code exceeds 500 kB")
    timeout = min(body.timeout_s or LIBRARY.get(body.library_script or "", {}).get("default_timeout_s")
                  or s.sandbox_default_timeout_s, s.sandbox_max_timeout_s)
    exp = Experiment(
        conjecture_id=body.conjecture_id, title=body.title, problem=body.problem, code=code,
        code_sha256=hashlib.sha256(code.encode()).hexdigest(), library_script=body.library_script,
        parameters=body.parameters, settings={"timeout_s": timeout, "memory_mb": body.memory_mb or s.sandbox_default_memory_mb},
        status="queued", result_kind=body.result_kind, created_by=f"user:{user.get('email') or user.get('id')}",
    )
    db.add(exp)
    db.flush()
    job = enqueue(db, "run_experiment", {"experiment_id": exp.id}, subject_type="experiment", subject_id=exp.id,
                  max_attempts=1)
    db.commit()
    return {**row(exp, exclude={"code"}), "job_id": job.id}


@router.get("")
def list_experiments(conjecture_id: str | None = None, status: str | None = None, limit: int = Query(100, le=500),
                     db: Session = Depends(get_db), _: dict = Depends(current_user)):
    stmt = select(Experiment)
    if conjecture_id:
        stmt = stmt.where(Experiment.conjecture_id == conjecture_id)
    if status:
        stmt = stmt.where(Experiment.status == status)
    exps = db.scalars(stmt.order_by(Experiment.created_at.desc()).limit(limit)).all()
    titles = dict(db.execute(select(Conjecture.id, Conjecture.title)).all())
    return {"items": [{**row(e, exclude=EXPERIMENT_LIST_EXCLUDE), "conjecture_title": titles.get(e.conjecture_id),
                       "summary": (e.result or {}).get("summary") if isinstance(e.result, dict) else None} for e in exps]}


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str, db: Session = Depends(get_db), _: dict = Depends(current_user)):
    e = db.get(Experiment, experiment_id)
    if not e:
        raise HTTPException(404, "Experiment not found")
    d = row(e)
    c = db.get(Conjecture, e.conjecture_id) if e.conjecture_id else None
    d["conjecture_title"] = c.title if c else None
    d["job"] = row(db.scalars(select(Job).where(Job.subject_id == e.id).order_by(Job.created_at.desc())).first())
    return d


class InterpretIn(BaseModel):
    interpretation: str = Field(..., min_length=3)


@router.post("/{experiment_id}/interpretation")
def interpret(experiment_id: str, body: InterpretIn, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    e = db.get(Experiment, experiment_id)
    if not e:
        raise HTTPException(404, "Experiment not found")
    e.interpretation = body.interpretation
    if e.conjecture_id:
        db.add(ConjectureEvent(conjecture_id=e.conjecture_id, event_type="note",
                               actor=f"user:{user.get('email') or user.get('id')}",
                               summary=f"Interpretation of experiment '{e.title}': {body.interpretation[:300]}",
                               details={"experiment_id": e.id}))
    db.commit()
    return row(e, exclude={"code"})


@router.post("/{experiment_id}/rerun")
def rerun(experiment_id: str, db: Session = Depends(get_db), user: dict = Depends(current_user)):
    """Reproduce an experiment: identical stored code and parameters, fresh sandbox."""
    e = db.get(Experiment, experiment_id)
    if not e:
        raise HTTPException(404, "Experiment not found")
    clone = Experiment(conjecture_id=e.conjecture_id, title=f"{e.title} (reproduction)", problem=e.problem, code=e.code,
                       code_sha256=e.code_sha256, library_script=e.library_script, parameters=e.parameters,
                       settings=e.settings, status="queued", result_kind=e.result_kind,
                       created_by=f"user:{user.get('email') or user.get('id')}")
    db.add(clone)
    db.flush()
    job = enqueue(db, "run_experiment", {"experiment_id": clone.id}, subject_type="experiment", subject_id=clone.id,
                  max_attempts=1)
    db.commit()
    return {**row(clone, exclude={"code"}), "job_id": job.id, "reproduces": e.id}
