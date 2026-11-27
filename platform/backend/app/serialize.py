"""Row -> JSON helpers for API responses."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.inspection import inspect


def row(obj, *, exclude: set[str] | None = None) -> dict:
    if obj is None:
        return None
    exclude = exclude or set()
    out = {}
    for col in inspect(obj).mapper.column_attrs:
        k = col.key
        if k in exclude:
            continue
        v = getattr(obj, k)
        if isinstance(v, (datetime, date)):
            v = v.isoformat()
        out[k] = v
    return out


PAPER_LIST_EXCLUDE = {"references", "latex_source", "source_metadata", "abstract"}
PAPER_DETAIL_EXCLUDE = {"latex_source"}
CANDIDATE_LIST_EXCLUDE = {"context_before", "context_after"}
EXPERIMENT_LIST_EXCLUDE = {"code", "stdout", "stderr"}
JOB_EXCLUDE: set[str] = set()


def paper_brief(p, *, macros: bool = False) -> dict:
    d = row(p, exclude=PAPER_LIST_EXCLUDE)
    d["has_latex"] = bool(p.latex_source)
    if macros:
        from app.extraction.latex_macros import extract_macros

        d["latex_macros"] = extract_macros(p.latex_source)
    return d
