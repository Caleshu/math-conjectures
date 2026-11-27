"""Autopilot: keeps the Research Lab busy on problems that are open and not already known.

Each tick (once a minute, while enabled):
  1. If a research run is active, wait. If the last run stopped on a provider usage limit (HTTP 429), wait for
     a cooldown and then resume it from its checkpoints.
  2. Otherwise pick the next eligible conjecture: status UNVERIFIED / LIKELY_OPEN / VERIFIED_OPEN, never
     researched, not skipped. Before spending a research run, do a *novelty pre-check* (one model call). It
     uses real searches (title queries and works citing the source paper) plus the index of the user's
     math-conjectures repository. Problems judged already resolved, already in the repo, or trivial are
     skipped, with the reason recorded. They are never re-solved.
  3. If nothing is eligible, promote AI-extracted open problems from indexed papers. This requires the
     verbatim wording to have been verified against the source and stated confidence >= 0.75. If none
     remain, run AI extraction on papers that only have heuristic candidates. If those are exhausted too,
     discover new arXiv papers (math.CO, recent, mentioning conjectures/open problems) and ingest them.
  4. Every finished run, status change and new problem is exported to GitHub by the repo exporter.

State lives in DATA_DIR/autopilot.json, so it survives restarts. Nothing is promoted to "established".
"""
from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.config import get_settings
from app.db import session_scope
from app.models import CandidatePassage, Conjecture, ConjectureEvent, Job, Paper, ResearchRun

log = logging.getLogger("mrl.autopilot")
ELIGIBLE = ("UNVERIFIED", "LIKELY_OPEN", "VERIFIED_OPEN")
_state_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def state_path() -> Path:
    return get_settings().data_dir / "autopilot.json"


def load_state() -> dict:
    try:
        return json.loads(state_path().read_text())
    except (OSError, json.JSONDecodeError):
        return {"enabled": False, "log": []}


def save_state(st: dict) -> None:
    with _state_lock:
        st["log"] = st.get("log", [])[-80:]
        state_path().write_text(json.dumps(st, indent=1, default=str))


def note(st: dict, msg: str, **kw) -> None:
    log.info("autopilot: %s", msg)
    st.setdefault("log", []).append({"at": _now().isoformat(), "msg": msg, **kw})
    st["last_action"] = msg


def is_rate_limit(err: str | None) -> bool:
    return bool(err) and bool(re.search(r"429|rate.?limit|usage limit|hit your .*limit", err, re.I))


# ------------------------------------------------------------------------------------------
# Novelty pre-check
# ------------------------------------------------------------------------------------------
PRECHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["likely_open", "likely_resolved", "already_in_repo",
                                               "trivial_or_ill_posed", "unclear"]},
        "repo_match": {"type": "string", "description": "folder name of a matching repo problem, or empty"},
        "evidence_refs": {"type": "array", "items": {"type": "string"},
                          "description": "R-refs of search results that support the verdict"},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "repo_match", "evidence_refs", "reason"],
    "additionalProperties": False,
}
PRECHECK_SYSTEM = """You decide whether a conjecture is worth a full AI research run. You are NOT solving it.
Inputs: the conjecture, real bibliographic search results (R-refs: titles, years, abstracts), works citing
its source paper, and the index of problems the user ALREADY works on in their repository.
Verdicts:
- already_in_repo: the same problem (or one that trivially contains it) is already in the user's repository.
- likely_resolved: a returned record's title or abstract indicates that it was proved, disproved or settled. Cite the R-ref.
- likely_resolved also applies when results ALREADY RECORDED IN THIS APP (listed separately) settle it,
  for example a computed value that contradicts the claim. Say which.
- trivial_or_ill_posed: it is false or true by a one-line argument from its own definitions, or it is too
  vague to investigate.
- likely_open: no evidence of resolution, and it is a genuine research question.
- unclear: the evidence is mixed.
Never cite anything that is not an R-ref. Absence of evidence is not proof of openness; say so in the reason."""


def repo_index() -> str:
    """Problems already in the user's repository (README index lines, folder names)."""
    from app.export.repo import ensure_clone
    try:
        repo = ensure_clone()
    except Exception as e:  # noqa: BLE001 - surface but don't block research
        return f"(repository index unavailable: {e})"
    text = (repo / "README.md").read_text() if (repo / "README.md").exists() else ""
    items = [l for l in text.split("\n") if l.startswith("- [")]
    folders = sorted(p.name for p in (repo / "Conjectures").iterdir() if p.is_dir()) if (repo / "Conjectures").exists() else []
    return "\n".join(items) + "\nFolders: " + ", ".join(folders)


def precheck(conjecture_id: str) -> dict:
    from app.llm.registry import tracked_json_call
    from app.sources.base import SearchQuery, SourceError
    from app.sources.registry import SOURCES, federated_search

    with session_scope() as db:
        c = db.get(Conjecture, conjecture_id)
        title, stmt, orig = c.title, c.normalized_statement, c.original_statement
        src = db.get(Paper, c.source_paper_id) if c.source_paper_id else None
        src_info = (src.title, src.openalex_id, src.arxiv_id) if src else None
        # what this app has already established about problems from the same paper
        from app.models import Experiment
        sib = []
        if src:
            for o in db.scalars(select(Conjecture).where(Conjecture.source_paper_id == src.id, Conjecture.id != c.id)):
                sib.append(f"- [{o.status}] {o.title}")
                sib += [f"    known: {k.get('statement')} ({k.get('citation')})" for k in o.known_results]
                for e in db.scalars(select(Experiment).where(Experiment.conjecture_id == o.id, Experiment.status == "succeeded")):
                    summ = (e.result or {}).get("summary") if isinstance(e.result, dict) else None
                    if isinstance(summ, str):
                        sib.append(f"    computed: {e.title}: {summ[:600]}")
        sib_text = "\n".join(sib)
    recs, errors = [], {}
    queries = [title]
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", title) if w.lower() not in
             {"conjecture", "problem", "exactly", "every", "with", "that", "from", "their"}]
    if len(words) > 3:
        queries.append(" ".join(words[:6]))
    for q in queries:
        rs, errs = federated_search(SearchQuery(text=q, limit=8), ["arxiv", "openalex", "crossref", "semantic_scholar"])
        recs += rs
        errors.update(errs)
    citing = []
    if src_info and src_info[1]:
        try:
            citing = SOURCES["openalex"].citing_works(src_info[1], 40)
        except SourceError as e:
            errors["openalex_citing"] = str(e)
    seen, rows = set(), []
    for r in recs + citing:
        key = r.doi or r.arxiv_id or r.title.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(r)
    rows = rows[:40]
    listing = "\n".join(f"[R{i}] {r.title} ({r.published_date.year if r.published_date else 'n.d.'}"
                        f"{'; arXiv:' + r.arxiv_id if r.arxiv_id else ''}){' [cites the source paper]' if r in citing else ''}\n"
                        f"     {(r.abstract or '')[:500]}" for i, r in enumerate(rows, 1))
    prompt = (f"# Conjecture: {title}\nOriginal statement:\n{orig}\n\nNormalized:\n{stmt}\n"
              f"Source paper: {src_info[0] if src_info else 'unknown'}\n\n"
              f"# The user's repository already contains:\n{repo_index()}\n\n"
              + (f"# Already recorded in this app for problems from the same source paper (sandbox results are "
                 f"finite computations):\n{sib_text}\n\n" if sib_text else "")
              + f"# Search results\n{listing or '(none returned)'}\n"
              + (f"\nSource errors: {errors}\n" if errors else ""))
    res = tracked_json_call(purpose="autopilot:precheck", system=PRECHECK_SYSTEM, prompt=prompt,
                            schema=PRECHECK_SCHEMA, subject_id=conjecture_id, max_tokens=8000, effort="medium")
    out = dict(res.data)
    refs = {f"R{i}": r for i, r in enumerate(rows, 1)}
    out["evidence"] = [{"ref": x, "title": refs[x].title, "arxiv_id": refs[x].arxiv_id, "doi": refs[x].doi}
                       for x in out.get("evidence_refs", []) if x in refs]  # only real records survive
    out["searched"] = {"queries": queries, "records": len(rows), "citing_works": len(citing), "errors": errors}
    out["at"] = _now().isoformat()
    return out


# ------------------------------------------------------------------------------------------
# Supply of problems
# ------------------------------------------------------------------------------------------
def promote_candidate(db) -> str | None:
    from app.services import conjectures as svc
    cands = db.scalars(select(CandidatePassage).where(CandidatePassage.review_status == "pending",
                                                      CandidatePassage.detector.like("llm:%"))
                       .order_by(CandidatePassage.created_at)).all()
    for cand in cands:
        a = cand.llm_assessment or {}
        if a.get("llm_verdict") == "rejected" or not a.get("original_wording"):
            continue
        if a.get("kind") not in ("conjecture", "open_problem", "open_question"):
            continue
        if not a.get("wording_verified_in_source") or (a.get("confidence") or 0) < 0.75:
            continue
        # duplicates: the same passage was already recorded (via a sibling heuristic candidate, or same label)
        dup = None
        for sid in a.get("candidate_ids", []):
            sib = db.get(CandidatePassage, sid)
            if sib and sib.conjecture_id:
                dup = sib.conjecture_id
        if not dup and a.get("label"):
            for o in db.scalars(select(Conjecture).where(Conjecture.source_paper_id == cand.paper_id)):
                oc = db.get(CandidatePassage, o.source_candidate_id) if o.source_candidate_id else None
                labels = {oc.label if oc else None, ((o.extraction_details or {}).get("assessment") or {}).get("label")}
                if a["label"] in labels:
                    dup = o.id
        if dup:
            cand.review_status = "rejected"
            cand.review_note = f"autopilot: duplicate of an already recorded conjecture ({dup})"
            continue
        paper = db.get(Paper, cand.paper_id)
        cite = f"{', '.join((paper.authors or [])[:3])}, {paper.title}" + (f", arXiv:{paper.arxiv_id}" if paper.arxiv_id else "")
        data = {
            "title": a.get("title") or "Untitled problem", "field": a.get("field") or "combinatorics",
            "subfields": a.get("subfields", []), "problem_type": "conjecture" if a.get("kind") == "conjecture" else "open_problem",
            "original_statement": a["original_wording"], "normalized_statement": a.get("normalized_statement") or a["original_wording"],
            "definitions": a.get("definitions", []),
            "notation": ("Ambiguities flagged at extraction: " + " | ".join(a["ambiguities"])) if a.get("ambiguities") else None,
            "source_paper_id": cand.paper_id, "source_page": a.get("page"), "source_section": a.get("section"),
            "known_results": [{"statement": k["statement"], "citation": f"{cite} ({k.get('location', '')})",
                               "source_paper_id": cand.paper_id, "location": k.get("location"),
                               "is_computational": k.get("is_computational", False), "reproduced": None}
                              for k in a.get("known_partial_results", [])],
            "difficulty_estimate": a.get("difficulty_guess"),
            "difficulty_rationale": "AI extraction estimate.",
            "extraction_details": {"extracted_by": cand.detector, "assessment": a, "promoted_by": "autopilot"},
        }
        try:
            c = svc.create_conjecture(db, data, actor="autopilot", candidate=cand)
        except svc.ConjectureError as e:
            cand.review_note = f"autopilot could not promote: {e}"
            continue
        # sibling candidates pointing at the same passage are left for human review
        return c.id
    return None


def papers_needing_ai_extraction(db) -> list[str]:
    from app.models import LLMUsage
    extracted = set(db.scalars(select(LLMUsage.subject_id).where(LLMUsage.purpose == "conjecture_extraction",
                                                                LLMUsage.success.is_(True))))
    pending_jobs = set(db.scalars(select(Job.subject_id).where(Job.job_type == "llm_extract",
                                                               Job.status.in_(["queued", "running"]))))
    out = []
    for p in db.scalars(select(Paper).where(Paper.status == "scanned").order_by(Paper.created_at.desc())):
        if p.id not in extracted and p.id not in pending_jobs and (p.latex_source or p.page_count):
            out.append(p.id)
    return out


DISCOVERY_QUERIES = ["conjecture graph", "open problem combinatorics", "we conjecture hypercube",
                     "open question extremal graph", "conjecture coloring", "conjecture permutations"]


def discover(st: dict) -> int:
    from app.jobs.queue import enqueue
    from app.services.papers import find_existing, upsert_paper
    from app.sources.base import SearchQuery
    from app.sources.registry import federated_search
    i = st.get("discovery_index", 0)
    q = DISCOVERY_QUERIES[i % len(DISCOVERY_QUERIES)]
    st["discovery_index"] = i + 1
    recs, errs = federated_search(SearchQuery(text=q, subject="math.CO", limit=15,
                                              from_date=(_now() - timedelta(days=540)).date()), ["arxiv"])
    added = 0
    with session_scope() as db:
        for r in recs:
            if added >= 3:
                break
            if not r.arxiv_id or find_existing(db, r):
                continue
            p, _ = upsert_paper(db, r, discovered_via=f"autopilot:{q}")
            db.flush()
            enqueue(db, "process_paper", {"paper_id": p.id}, subject_type="paper", subject_id=p.id)
            added += 1
    note(st, f"discovery: query '{q}' indexed {added} new arXiv paper(s)", errors=errs or None)
    return added


# ------------------------------------------------------------------------------------------
# Main tick
# ------------------------------------------------------------------------------------------
def tick() -> None:
    st = load_state()
    if not st.get("enabled"):
        return
    from app.llm.registry import available_providers
    if not available_providers():
        st["blocked"] = "no AI provider available"
        save_state(st)
        return
    st.pop("blocked", None)
    cd = st.get("cooldown_until")
    if cd and datetime.fromisoformat(cd) > _now():
        save_state(st)
        return
    try:
        _tick(st)
    except Exception as e:  # noqa: BLE001
        msg = f"{type(e).__name__}: {e}"
        if is_rate_limit(msg):
            st["cooldown_until"] = (_now() + timedelta(minutes=30)).isoformat()
            note(st, "usage limit reached; pausing 30 min")
        else:
            st["last_error"] = msg[:500]
            st["cooldown_until"] = (_now() + timedelta(minutes=5)).isoformat()
            note(st, f"error: {msg[:300]}")
            log.exception("autopilot tick failed")
    save_state(st)


def _launch(db, cid: str, st: dict) -> None:
    from app.jobs.queue import enqueue
    from app.research.orchestrator import normalize_limits
    lim = normalize_limits(st.get("limits") or {})
    run = ResearchRun(conjecture_id=cid, status="queued", limits=lim, checkpoint={"phase": "queued", "launched_by": "autopilot"})
    db.add(run)
    db.flush()
    job = enqueue(db, "research_run", {"research_run_id": run.id}, subject_type="research_run", subject_id=run.id, max_attempts=2)
    run.checkpoint = {**run.checkpoint, "job_id": job.id}
    db.add(ConjectureEvent(conjecture_id=cid, event_type="research_run", actor="autopilot",
                           summary="Research run launched by autopilot", details={"research_run_id": run.id}))


def _tick(st: dict) -> None:
    from app.jobs.queue import enqueue
    with session_scope() as db:
        active = db.scalar(select(ResearchRun).where(ResearchRun.status.in_(["queued", "running", "cancelling"])))
        if active:
            st["current"] = {"research_run_id": active.id, "conjecture_id": active.conjecture_id}
            return
        # resume a run that stopped on a usage limit
        last = db.scalars(select(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(1)).first()
        if last and last.status == "failed" and is_rate_limit(last.error) and \
                (last.checkpoint or {}).get("autopilot_resumes", 0) < 6:
            if not st.get("cooldown_for") == last.id:
                st["cooldown_for"] = last.id
                st["cooldown_until"] = (_now() + timedelta(minutes=30)).isoformat()
                note(st, f"run {last.id[:8]} hit the usage limit; resuming in 30 min")
                return
            last.status, last.error, last.finished_at = "queued", None, None
            job = enqueue(db, "research_run", {"research_run_id": last.id}, subject_type="research_run",
                          subject_id=last.id, max_attempts=2)
            cp = {k: v for k, v in (last.checkpoint or {}).items() if k not in ("stop_reason", "agent_errors", "usage")}
            last.checkpoint = {**cp, "phase": "resuming", "job_id": job.id,
                               "autopilot_resumes": cp.get("autopilot_resumes", 0) + 1}
            st.pop("cooldown_for", None)
            note(st, f"resumed run {last.id[:8]} after usage-limit cooldown")
            return
        st.pop("current", None)

        researched = set(db.scalars(select(ResearchRun.conjecture_id)))
        cands = [c for c in db.scalars(select(Conjecture).where(Conjecture.status.in_(ELIGIBLE))
                                       .order_by(Conjecture.created_at))
                 if c.id not in researched and not (c.extraction_details or {}).get("autopilot", {}).get("skipped")]
        target = cands[0].id if cands else None
        if target is None:
            new = promote_candidate(db)
            if new:
                note(st, "promoted an AI-extracted open problem to the library", conjecture_id=new)
                db.flush()
                _request_export(db)
                return
            papers = papers_needing_ai_extraction(db)
            busy = db.scalar(select(func.count(Job.id)).where(Job.job_type.in_(["llm_extract", "process_paper", "ingest_identifier"]),
                                                             Job.status.in_(["queued", "running"])))
            if busy:
                st["waiting"] = "paper processing / extraction in progress"
                return
            if papers:
                enqueue(db, "llm_extract", {"paper_id": papers[0]}, subject_type="paper", subject_id=papers[0], max_attempts=2)
                note(st, "queued AI extraction for an indexed paper", paper_id=papers[0])
                return
    if target is None:
        discover(st)
        return

    # novelty pre-check (outside the DB session: it makes network and model calls)
    with session_scope() as db:
        c = db.get(Conjecture, target)
        pc = (c.extraction_details or {}).get("autopilot", {}).get("precheck")
        title = c.title
    if not pc:
        note(st, f"pre-checking '{title[:80]}'")
        save_state(st)
        pc = precheck(target)
        with session_scope() as db:
            c = db.get(Conjecture, target)
            ap = {**(c.extraction_details or {}).get("autopilot", {}), "precheck": pc}
            if pc["verdict"] in ("likely_resolved", "already_in_repo", "trivial_or_ill_posed"):
                ap["skipped"] = pc["verdict"]
            c.extraction_details = {**(c.extraction_details or {}), "autopilot": ap}
            db.add(ConjectureEvent(conjecture_id=target, event_type="autopilot_precheck", actor="autopilot",
                                   summary=f"Novelty pre-check: {pc['verdict']}", details=pc))
            if ap.get("skipped"):
                note(st, f"skipped '{title[:80]}': {pc['verdict']}. {pc['reason'][:200]}")
                _request_export(db)
                return
    with session_scope() as db:
        _launch(db, target, st)
        note(st, f"launched research on '{title[:80]}' (pre-check: {pc['verdict']})", conjecture_id=target)


def _request_export(db) -> None:
    from app.export import request_export
    request_export(db)


def export_watch() -> None:
    """Always-on: queue a GitHub export whenever problem data changed since the last successful sync."""
    from app.export import latest_change, request_export
    if not get_settings().repo_export_enabled:
        return
    st = load_state()
    last = (st.get("last_export") or {})
    last_ok = datetime.fromisoformat(last["at"]) if last.get("ok") and last.get("at") else None
    if last_ok and last_ok.tzinfo is None:
        last_ok = last_ok.replace(tzinfo=timezone.utc)
    if not last.get("ok") and last.get("at") and \
            datetime.fromisoformat(last["at"]).replace(tzinfo=timezone.utc) > _now() - timedelta(minutes=10):
        return  # back off for 10 min after a failed export
    with session_scope() as db:
        ch = latest_change(db)
        if ch and (last_ok is None or ch > last_ok):
            request_export(db)


class AutopilotThread:
    def __init__(self, interval: float = 60.0):
        self.interval = interval
        self._stop = threading.Event()

    def start(self) -> None:
        threading.Thread(target=self._loop, name="mrl-autopilot", daemon=True).start()

    def _loop(self) -> None:
        self._stop.wait(15)
        while not self._stop.is_set():
            try:
                tick()
            except Exception:  # noqa: BLE001
                log.exception("autopilot loop error")
            try:
                export_watch()
            except Exception:  # noqa: BLE001
                log.exception("export watch error")
            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
