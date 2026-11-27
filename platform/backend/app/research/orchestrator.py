"""Research orchestrator: runs the six agents against one conjecture under hard limits.

Iteration 1 (independent): the Strategist, Extremal Mathematician, Construction Agent, Computational
Mathematician and Literature Specialist work in parallel. Each sees only the conjecture, its sourced context and
*prior* research (earlier runs, experiments), never each other's output from this run. Computational experiments run
in the sandbox, and their real outputs are interpreted in a second call. The Adversarial Reviewer then reviews the
iteration's proof attempts and strongest claims. It is independent of their authors (separate call, with no
authoring context). The orchestrator model identifies conflicts and picks follow-ups.

Iteration k > 1 (focused): only agents given a follow-up task run. They see the team's earlier claims labelled
UNVERIFIED with author and review status, and are told not to treat them as facts.

Limits: iterations, model calls, tokens, wall-clock runtime, number and size of experiments. Every step is
checkpointed in `agent_tasks`, so a run interrupted by a restart resumes without repeating finished work.
"""
from __future__ import annotations

import json
import re
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import func, select

from app.config import get_settings
from app.db import session_scope
from app.llm.base import LLMBudgetExceeded, LLMError, LLMUnavailable
from app.llm.registry import available_providers, tracked_json_call
from app.models import (AgentTask, Claim, Conjecture, ConjectureEvent, Experiment, LLMUsage, ProofAttempt,
                        ResearchRun, ValidationLevel, utcnow)
from app.research import agents as A

log = logging.getLogger("mrl.research")

DEFAULT_LIMITS = {
    "max_iterations": 2,
    "max_model_calls": 24,
    "max_tokens": 2_000_000,
    "max_runtime_s": 5400,
    "max_experiments": 4,
    "experiment_timeout_s": 120,
    "experiment_memory_mb": 2048,
    "concurrency": 3,
    "provider": None,
    "effort": "high",
}
LIMIT_BOUNDS = {"max_iterations": (1, 5), "max_model_calls": (6, 80), "max_tokens": (100_000, 10_000_000),
                "max_runtime_s": (300, 6 * 3600), "max_experiments": (0, 12), "experiment_timeout_s": (10, 1800),
                "experiment_memory_mb": (256, 16384), "concurrency": (1, 5)}
REASONING = ("strategist", "extremal", "construction")
TEAM_ROLES = ("strategist", "extremal", "construction", "computational", "literature")
REVIEW_CLAIM_CAP = 14


class LimitReached(Exception):
    pass


class Cancelled(Exception):
    pass


def normalize_limits(raw: dict | None) -> dict:
    out = dict(DEFAULT_LIMITS)
    for k, v in (raw or {}).items():
        if k in LIMIT_BOUNDS and v is not None:
            lo, hi = LIMIT_BOUNDS[k]
            out[k] = max(lo, min(hi, int(v)))
        elif k in ("provider", "effort") and v:
            out[k] = str(v)
    return out


# ------------------------------------------------------------------------------------------
# Context
# ------------------------------------------------------------------------------------------
def _ref(prefix: str, uid: str) -> str:
    return f"{prefix}-{uid[:6]}"


def conjecture_context(db, c: Conjecture) -> str:
    """Everything sourced about the conjecture, with provenance, in a stable textual form."""
    L = [f"# Conjecture: {c.title}", f"Field: {c.field}  |  Current recorded status: {c.status}", "",
         "## Original statement (verbatim from source)", c.original_statement, ""]
    if c.normalized_statement:
        L += ["## Normalized statement", c.normalized_statement, ""]
    if c.definitions:
        L.append("## Definitions")
        L += [f"- {d.get('term')}: {d.get('definition')}" for d in c.definitions]
        L.append("")
    if c.notation:
        L += ["## Notation", str(c.notation), ""]
    if c.known_results:
        L.append("## Known results (as recorded, with citations; 'reproduced' says whether a computation was "
                 "independently re-run here)")
        for k in c.known_results:
            L.append(f"- {k.get('statement')}  [source: {k.get('citation') or 'unspecified'}; "
                     f"computational={k.get('is_computational')}; reproduced={k.get('reproduced')}]")
            if k.get("note"):
                L.append(f"  note: {k['note']}")
        L.append("")
    exps = db.scalars(select(Experiment).where(Experiment.conjecture_id == c.id, Experiment.research_run_id.is_(None))
                      .order_by(Experiment.created_at)).all()
    if exps:
        L.append("## Earlier experiments on this conjecture (real sandbox runs)")
        for e in exps:
            summ = (e.result or {}).get("summary") if isinstance(e.result, dict) else None
            L.append(f"- {e.title} [{e.status}, {e.result_kind}]: {summ or ''}")
            if e.interpretation:
                L.append(f"  interpretation: {e.interpretation[:800]}")
        L.append("")
    return "\n".join(L)


def prior_runs_context(db, c: Conjecture, run_id: str) -> str:
    claims = db.scalars(select(Claim).where(Claim.conjecture_id == c.id, Claim.research_run_id != run_id)
                        .order_by(Claim.created_at.desc()).limit(30)).all()
    if not claims:
        return ""
    L = ["## Claims from EARLIER research runs (UNVERIFIED unless the status says otherwise; not facts)"]
    for cl in claims:
        L.append(f"- [{cl.claim_type}, {cl.verification_status}, by {cl.created_by}] {cl.statement}")
    return "\n".join(L) + "\n"


def team_context(db, run_id: str, *, upto_iteration: int) -> str:
    """This run's claims and proof attempts so far, labelled as unverified work of other agents."""
    claims = db.scalars(select(Claim).where(Claim.research_run_id == run_id).order_by(Claim.created_at)).all()
    proofs = db.scalars(select(ProofAttempt).where(ProofAttempt.research_run_id == run_id)
                        .order_by(ProofAttempt.created_at)).all()
    exps = db.scalars(select(Experiment).where(Experiment.research_run_id == run_id)
                      .order_by(Experiment.created_at)).all()
    L = ["## Team results so far in THIS run. These are UNVERIFIED work of other agents. Check them, do not assume them."]
    for cl in claims:
        if (cl.details or {}).get("iteration", 1) > upto_iteration:
            continue
        rv = "; ".join(f"{r.get('verdict')}: " + "; ".join(i.get("detail", "")[:200] for i in r.get("issues", [])[:2])
                       for r in cl.reviews) or "not reviewed"
        L.append(f"- {_ref('C', cl.id)} [{cl.claim_type}, author={cl.created_by}, "
                 f"support={cl.details.get('author_support')}, status={cl.verification_status}] {cl.statement}\n"
                 f"  review: {rv}")
    for p in proofs:
        L.append(f"- {_ref('P', p.id)} proof attempt by {p.created_by} [{p.status}] {p.strategy}: "
                 f"gaps={p.known_gaps}")
    for e in exps:
        summ = (e.result or {}).get("summary") if isinstance(e.result, dict) else None
        L.append(f"- {_ref('E', e.id)} experiment [{e.status}] {e.title}: {summ or ''} "
                 f"{('| ' + e.interpretation[:400]) if e.interpretation else ''}")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------------------------------
class Orchestrator:
    def __init__(self, run_id: str, job_id: str | None = None, progress=None):
        self.run_id = run_id
        self.job_id = job_id
        self.progress = progress or (lambda *a, **k: None)
        with session_scope() as db:
            run = db.get(ResearchRun, run_id)
            self.limits = normalize_limits(run.limits)
            self.conjecture_id = run.conjecture_id
            if run.started_at is None:
                run.started_at = utcnow()
            self.started_at = run.started_at
            run.status = "running"
            run.error = None

    # ---- limits & bookkeeping ------------------------------------------------------------
    def usage(self) -> dict:
        with session_scope() as db:
            calls, tin, tout = db.execute(
                select(func.count(LLMUsage.id), func.coalesce(func.sum(LLMUsage.input_tokens), 0),
                       func.coalesce(func.sum(LLMUsage.output_tokens), 0)).where(LLMUsage.subject_id == self.run_id)
            ).one()
            n_exp = db.scalar(select(func.count(Experiment.id)).where(Experiment.research_run_id == self.run_id))
        return {"model_calls": int(calls), "tokens": int(tin) + int(tout), "experiments": int(n_exp or 0)}

    def check(self, *, need_call: bool = True) -> None:
        with session_scope() as db:
            st = db.get(ResearchRun, self.run_id).status
        if st == "cancelling":
            raise Cancelled("cancelled by user")
        u = self.usage()
        el = (utcnow() - self.started_at.replace(tzinfo=self.started_at.tzinfo or utcnow().tzinfo)).total_seconds()
        if el > self.limits["max_runtime_s"]:
            raise LimitReached(f"runtime limit reached ({self.limits['max_runtime_s']}s)")
        if need_call and u["model_calls"] >= self.limits["max_model_calls"]:
            raise LimitReached(f"model-call limit reached ({self.limits['max_model_calls']})")
        if u["tokens"] >= self.limits["max_tokens"]:
            raise LimitReached(f"token limit reached ({self.limits['max_tokens']})")

    # ---- model team ----------------------------------------------------------------------------
    def _team(self) -> list[str] | None:
        """Two-model team (a Claude provider + a GPT provider) when provider is "team", or unset and both are available."""
        want = self.limits.get("provider")
        if want not in (None, "team"):
            return None
        avail = available_providers()
        claude = next((p for p in ("claude_code", "anthropic") if p in avail), None)
        gpt = next((p for p in ("codex", "openai") if p in avail), None)  # prefer the ChatGPT subscription
        return [claude, gpt] if claude and gpt else None

    def provider_for(self, role: str, iteration: int) -> str | None:
        """Split roles across the two models and swap the split each iteration, so both models attempt every role.
        The reviewer is the model that wrote less of the iteration's work, so most claims get a cross-model review."""
        team = self._team()
        if not team:
            return None if self.limits.get("provider") == "team" else self.limits.get("provider")
        shift = (iteration - 1) % 2
        if role == "reviewer":
            return team[1 - shift]
        if role == "orchestrator":
            return team[shift]
        i = TEAM_ROLES.index(role) if role in TEAM_ROLES else 0
        return team[(i + shift) % 2]

    def call(self, role: str, iteration: int, system: str, prompt: str, schema: dict) -> dict:
        self.check()
        provider = self.provider_for(role, iteration)
        kw = dict(purpose=f"research:{role}", system=system, prompt=prompt, schema=schema, job_id=self.job_id,
                  subject_id=self.run_id, max_tokens=32000, effort=self.limits.get("effort", "high"))
        try:
            return tracked_json_call(provider=provider, **kw).data
        except (LLMError, LLMUnavailable) as e:
            team = self._team()
            if not team or not re.search(r"429|usage limit|hit your .*limit|rate.?limit|unavailable|not found", str(e), re.I):
                raise
            other = team[1] if provider == team[0] else team[0]
            log.warning("%s on %s failed (%s); falling back to %s", role, provider, e, other)
            self.check()
            return tracked_json_call(provider=other, **kw).data

    def checkpoint(self, **kw) -> None:
        with session_scope() as db:
            run = db.get(ResearchRun, self.run_id)
            cp = dict(run.checkpoint or {})
            cp.update(kw)
            run.checkpoint = cp

    def task(self, role: str, iteration: int, phase: str, current: str, inp: dict | None = None) -> tuple[str, dict | None]:
        """Get-or-create the AgentTask for (role, iteration, phase). Returns (id, output if already completed)."""
        with session_scope() as db:
            t = db.scalars(select(AgentTask).where(AgentTask.research_run_id == self.run_id,
                                                   AgentTask.agent_role == role, AgentTask.iteration == iteration)
                           ).all()
            t = next((x for x in t if (x.input or {}).get("phase") == phase), None)
            if t and t.status == "completed":
                return t.id, t.output
            if not t:
                t = AgentTask(research_run_id=self.run_id, agent_role=role, iteration=iteration,
                              input={"phase": phase, "focus": current, "provider": self.provider_for(role, iteration),
                                     **(inp or {})})
                db.add(t)
                db.flush()
            t.status, t.current_task, t.error = "running", current, None
            return t.id, None

    def finish_task(self, tid: str, output: dict, report: str | None = None, status: str = "completed",
                    error: str | None = None) -> None:
        with session_scope() as db:
            t = db.get(AgentTask, tid)
            t.status, t.output, t.report_markdown, t.error = status, output, report, error
            t.current_task = None if status == "completed" else t.current_task

    # ---- storing agent output --------------------------------------------------------------
    def _resolve(self, db, refs: list[str]) -> list[str]:
        out = []
        for r in refs or []:
            r = r.strip()
            if r.startswith("C-") and len(r) > 2:
                cid = db.scalar(select(Claim.id).where(Claim.research_run_id == self.run_id,
                                                       Claim.id.like(r[2:] + "%")))
                if cid:
                    out.append(cid)
        return out

    def store_reasoning(self, tid: str, role: str, iteration: int, data: dict, experiment_id: str | None = None) -> dict:
        """Persist claims and proof attempts atomically with marking the task complete (no duplicates on resume)."""
        author = f"agent:{role}"
        with session_scope() as db:
            claim_ids, proof_ids = [], []
            for c in data.get("claims", []):
                lvl = ValidationLevel.IDEA
                if c.get("author_support") in ("proved_here", "sketch"):
                    lvl = ValidationLevel.WRITTEN_PROOF_ATTEMPT
                cl = Claim(conjecture_id=self.conjecture_id, research_run_id=self.run_id, statement=c["statement"],
                           claim_type=c["claim_type"], validation_level=lvl, verification_status="unverified",
                           evidence=[{"type": "author_justification", "text": c.get("justification", "")}],
                           experiment_id=experiment_id, created_by=author,
                           details={"author_support": c.get("author_support"), "confidence": c.get("confidence"),
                                    "iteration": iteration, "agent_task_id": tid},
                           related_claim_ids=self._resolve(db, c.get("related_refs", [])))
                db.add(cl)
                db.flush()
                claim_ids.append(cl.id)
            for p in data.get("proof_attempts", []):
                pa = ProofAttempt(conjecture_id=self.conjecture_id, research_run_id=self.run_id,
                                  strategy=p["strategy"], argument=f"**Target:** {p.get('target', '')}\n\n{p['argument']}",
                                  lemma_claim_ids=[], known_gaps=p.get("known_gaps", []),
                                  reviewer_feedback=[], status="awaiting_review", created_by=author,
                                  lean_artifact=None)
                pa.lemma_claim_ids = [{"statement": s} for s in p.get("lemmas", [])]
                db.add(pa)
                db.flush()
                proof_ids.append(pa.id)
            t = db.get(AgentTask, tid)
            t.status, t.current_task = "completed", None
            t.output = {**data, "claim_ids": claim_ids, "proof_attempt_ids": proof_ids}
            t.report_markdown = data.get("summary")
            return t.output

    # ---- agent steps -------------------------------------------------------------------------
    def base_prompt(self, iteration: int, focus: str | None) -> str:
        with session_scope() as db:
            c = db.get(Conjecture, self.conjecture_id)
            parts = [conjecture_context(db, c), prior_runs_context(db, c, self.run_id)]
            if iteration > 1:
                parts.append(team_context(db, self.run_id, upto_iteration=iteration - 1))
        if focus:
            parts.append(f"## Your task in this iteration\n{focus}\n")
        else:
            parts.append("## Your task\nThis is the independent first pass: you have NOT seen any teammate's work. "
                         "Investigate the conjecture from your role's perspective.\n")
        return "\n".join(p for p in parts if p)

    def run_reasoning(self, role: str, iteration: int, focus: str | None) -> dict:
        tid, done = self.task(role, iteration, "main", focus or "independent first pass")
        if done is not None:
            return done
        try:
            data = self.call(role, iteration, A.AGENTS[role]["system"], self.base_prompt(iteration, focus), A.REASONING_SCHEMA)
        except (LLMError, LimitReached) as e:
            self.finish_task(tid, {}, status="failed", error=str(e))
            raise
        return self.store_reasoning(tid, role, iteration, data)

    def run_computational(self, iteration: int, focus: str | None) -> dict:
        role = "computational"
        tid, done = self.task(role, iteration, "plan", focus or "design experiments")
        if done is None:
            remaining = self.limits["max_experiments"] - self.usage()["experiments"]
            if remaining <= 0:
                out = {"summary": "Experiment limit reached; no programs written.", "experiments": [],
                       "experiment_ids": []}
                self.finish_task(tid, out, out["summary"])
                done = out
            else:
                prompt = (self.base_prompt(iteration, focus) + "\n" +
                          A.SANDBOX_CONTRACT.format(timeout=self.limits["experiment_timeout_s"]) +
                          f"\nWrite at most {min(2, remaining)} programs. Each must be complete and runnable as is.\n")
                try:
                    plan = self.call(role, iteration, A.AGENTS[role]["system"], prompt, A.COMPUTE_PLAN_SCHEMA)
                except (LLMError, LimitReached) as e:
                    self.finish_task(tid, {}, status="failed", error=str(e))
                    raise
                ids = []
                with session_scope() as db:
                    import hashlib
                    for ex in plan.get("experiments", [])[:min(2, remaining)]:
                        try:
                            params = json.loads(ex.get("parameters_json") or "{}")
                            if not isinstance(params, dict):
                                params = {"value": params}
                        except json.JSONDecodeError:
                            params = {"_unparsed": ex.get("parameters_json")}
                        e = Experiment(conjecture_id=self.conjecture_id, research_run_id=self.run_id,
                                       title=ex["title"][:300], problem=f"{ex['question']}\nHypothesis: {ex['hypothesis']}",
                                       code=ex["code"], code_sha256=hashlib.sha256(ex["code"].encode()).hexdigest(),
                                       parameters=params, settings={"timeout_s": self.limits["experiment_timeout_s"],
                                                                    "memory_mb": self.limits["experiment_memory_mb"]},
                                       result_kind=ex["result_kind"], created_by="agent:computational")
                        db.add(e)
                        db.flush()
                        ids.append(e.id)
                    t = db.get(AgentTask, tid)
                    t.status, t.current_task = "completed", None
                    t.output = {**plan, "experiment_ids": ids}
                    t.report_markdown = plan.get("summary")
                    done = t.output
        exp_ids = done.get("experiment_ids", [])
        if not exp_ids:
            return {"plan": done, "interpretation": None}

        # Execute in the sandbox (idempotent: finished experiments are skipped by the handler).
        from app.jobs.handlers import run_experiment
        for i, eid in enumerate(exp_ids):
            self.check(need_call=False)
            with session_scope() as db:
                t = db.get(AgentTask, tid)
                t.current_task = f"running experiment {i + 1}/{len(exp_ids)} in sandbox"
            self.progress("experiment", {"experiment_id": eid})
            run_experiment(self.job_id or "", {"experiment_id": eid}, lambda *a, **k: None)
        with session_scope() as db:
            db.get(AgentTask, tid).current_task = None

        tid2, done2 = self.task(role, iteration, "interpret", "interpret sandbox outputs")
        if done2 is not None:
            return {"plan": done, "interpretation": done2}
        with session_scope() as db:
            blocks = []
            for eid in exp_ids:
                e = db.get(Experiment, eid)
                blocks.append(
                    f"### {_ref('E', e.id)}: {e.title}\nQuestion: {e.problem}\nKind: {e.result_kind}\n"
                    f"Status: {e.status} (exit {e.exit_code}, {e.runtime_seconds}s)\n"
                    f"result.json:\n{json.dumps(e.result, indent=1)[:12000] if e.result is not None else '(none)'}\n"
                    f"stdout (tail):\n{(e.stdout or '')[-3000:]}\nstderr (tail):\n{(e.stderr or '')[-2000:]}\n"
                    f"Code:\n```python\n{e.code[:8000]}\n```")
        prompt = (self.base_prompt(iteration, focus) +
                  "\n## Real outputs of your programs (executed in the sandbox)\n" + "\n\n".join(blocks) +
                  "\nInterpret each run. A claim of type observation/bound/counterexample_candidate based on a run "
                  "must state the exact finite range checked. If a run failed or its sanity check did not pass, "
                  "mark it untrustworthy and make no claim from it.\n")
        try:
            interp = self.call(role, iteration, A.AGENTS[role]["system"], prompt, A.COMPUTE_INTERPRET_SCHEMA)
        except (LLMError, LimitReached) as e:
            self.finish_task(tid2, {}, status="failed", error=str(e))
            raise
        with session_scope() as db:
            by_ref = {_ref("E", eid): eid for eid in exp_ids}
            trusted = set()
            for it in interp.get("interpretations", []):
                eid = by_ref.get(it.get("experiment_ref", "").strip())
                if eid:
                    e = db.get(Experiment, eid)
                    e.interpretation = ("[Computational Mathematician] " + it["interpretation"] +
                                        ("" if it.get("trustworthy") else "  (marked UNTRUSTWORTHY by the agent)"))
                    if it.get("trustworthy") and e.status == "succeeded":
                        trusted.add(eid)
        out = self.store_reasoning(tid2, role, iteration, {**interp, "proof_attempts": []},
                                   experiment_id=exp_ids[0] if len(exp_ids) == 1 else None)
        # Claims backed by a trusted, exact finite computation get level 3; others stay at idea/evidence.
        with session_scope() as db:
            for cid in out["claim_ids"]:
                cl = db.get(Claim, cid)
                kinds = {db.get(Experiment, e).result_kind for e in trusted}
                if trusted and "finite_computation" in kinds:
                    cl.validation_level = ValidationLevel.FINITE_COMPUTATIONAL_RESULT
                elif trusted:
                    cl.validation_level = ValidationLevel.EXPERIMENTAL_EVIDENCE
                cl.evidence = cl.evidence + [{"type": "experiments", "ids": sorted(trusted),
                                              "note": "sandbox runs the agent judged trustworthy"}]
        return {"plan": done, "interpretation": out}

    def run_literature(self, iteration: int, focus: str | None) -> dict:
        role = "literature"
        tid, done = self.task(role, iteration, "queries", focus or "plan literature searches")
        if done is None:
            prompt = self.base_prompt(iteration, focus) + "\nPropose 3 to 5 focused keyword queries.\n"
            try:
                q = self.call(role, iteration, A.AGENTS[role]["system"], prompt, A.LIT_QUERY_SCHEMA)
            except (LLMError, LimitReached) as e:
                self.finish_task(tid, {}, status="failed", error=str(e))
                raise
            from app.sources.base import SearchQuery
            from app.sources.registry import federated_search
            records, errors, seen = [], {}, set()
            with session_scope() as db:
                db.get(AgentTask, tid).current_task = "searching arXiv / OpenAlex / Crossref / Semantic Scholar"
            for qq in q.get("queries", [])[:5]:
                recs, errs = federated_search(SearchQuery(text=qq["text"], limit=8),
                                              ["arxiv", "openalex", "crossref", "semantic_scholar"])
                for k, v in errs.items():
                    errors[f"{k} ({qq['text'][:40]})"] = v
                for r in recs:
                    key = r.doi or r.arxiv_id or r.title.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    records.append({"query": qq["text"], "title": r.title, "authors": r.authors[:6],
                                    "year": r.published_date.year if r.published_date else None,
                                    "doi": r.doi, "arxiv_id": r.arxiv_id, "venue": r.venue,
                                    "url": r.landing_url, "source": r.source,
                                    "abstract": (r.abstract or "")[:1200]})
            records = records[:40]
            for i, r in enumerate(records, 1):
                r["ref"] = f"L{i}"
            done = {"queries": q.get("queries", []), "records": records, "source_errors": errors}
            self.finish_task(tid, done, f"{len(records)} records from {len(q.get('queries', []))} queries")
        tid2, done2 = self.task(role, iteration, "assess", "assess search results")
        if done2 is not None:
            return done2
        recs = done["records"]
        listing = "\n".join(
            f"[{r['ref']}] {r['title']} ({r.get('year')}; {', '.join(r['authors'][:3])}"
            f"{'; arXiv:' + r['arxiv_id'] if r.get('arxiv_id') else ''}{'; doi:' + r['doi'] if r.get('doi') else ''})\n"
            f"    {r['abstract'][:700]}" for r in recs) or "(no results returned)"
        errs = "\n".join(f"- {k}: {v}" for k, v in done.get("source_errors", {}).items())
        prompt = (self.base_prompt(iteration, focus) + "\n## Real search results\n" + listing +
                  (f"\n\nSource errors (these sources may be incomplete):\n{errs}" if errs else "") +
                  "\n\nAssess these records. Cite them only by L-ref.\n")
        try:
            data = self.call(role, iteration, A.AGENTS[role]["system"], prompt, A.LIT_ASSESS_SCHEMA)
        except (LLMError, LimitReached) as e:
            self.finish_task(tid2, {}, status="failed", error=str(e))
            raise
        by_ref = {r["ref"]: r for r in recs}
        works = []
        for w in data.get("relevant_works", []):
            r = by_ref.get(w.get("ref", "").strip())
            if r:  # drop anything that does not correspond to a real returned record
                works.append({**w, "record": {k: r.get(k) for k in ("title", "authors", "year", "doi", "arxiv_id", "url", "venue")}})
        data["relevant_works"] = works
        data["proof_attempts"] = []
        out = self.store_reasoning(tid2, role, iteration, data)
        with session_scope() as db:  # attach citations to literature claims when they cite L-refs
            for cid in out["claim_ids"]:
                cl = db.get(Claim, cid)
                txt = cl.statement + " " + " ".join(e.get("text", "") for e in cl.evidence)
                cited = [by_ref[r]["title"] for r in by_ref if r in txt.replace("[", " ").replace("]", " ").split()]
                if cited:
                    cl.evidence = cl.evidence + [{"type": "search_results", "titles": cited}]
        return out

    def run_review(self, iteration: int) -> dict:
        role = "reviewer"
        tid, done = self.task(role, iteration, "main", "adversarial review")
        if done is not None:
            return done
        with session_scope() as db:
            proofs = db.scalars(select(ProofAttempt).where(ProofAttempt.research_run_id == self.run_id,
                                                           ProofAttempt.status == "awaiting_review")).all()
            claims = db.scalars(select(Claim).where(Claim.research_run_id == self.run_id)).all()
            unreviewed = [c for c in claims if not c.reviews and c.created_by != "agent:reviewer"]
            prio = {"counterexample_candidate": 0, "lemma": 1, "bound": 1, "reduction": 2, "equivalent_formulation": 2,
                    "observation": 3, "construction": 3}
            unreviewed.sort(key=lambda c: (prio.get(c.claim_type, 4), -(c.details.get("confidence") or 0)))
            targets = unreviewed[:REVIEW_CLAIM_CAP]
            if not proofs and not targets:
                out = {"summary": "Nothing new to review.", "reviews": []}
                db.get(AgentTask, tid).status = "completed"
                db.get(AgentTask, tid).output = out
                return out
            c = db.get(Conjecture, self.conjecture_id)
            ctx = conjecture_context(db, c)
            exps = db.scalars(select(Experiment).where(Experiment.research_run_id == self.run_id)).all()
            body = ["## Items to review (authors withheld on purpose; you did not write any of them)"]
            for p in proofs:
                body.append(f"### {_ref('P', p.id)}: proof attempt: {p.strategy}\n{p.argument}\n"
                            f"Lemmas used: {[x.get('statement') for x in p.lemma_claim_ids]}\n"
                            f"Gaps admitted by author: {p.known_gaps}")
            for cl in targets:
                ev = next((e.get("text") for e in cl.evidence if e.get("type") == "author_justification"), "")
                body.append(f"### {_ref('C', cl.id)}: claim ({cl.claim_type}, author's support: "
                            f"{cl.details.get('author_support')})\n{cl.statement}\nJustification given: {ev}")
            if exps:
                body.append("## Computations run in this research (real sandbox outputs; check that they test what is claimed)")
                for e in exps:
                    body.append(f"- {_ref('E', e.id)} [{e.status}] {e.title}: "
                                f"{json.dumps(e.result)[:1500] if e.result is not None else '(no result)'}\n"
                                f"  code (head): {e.code[:1500]}")
        prompt = ctx + "\n" + "\n\n".join(body) + "\nReview EVERY item listed.\n"
        try:
            data = self.call(role, iteration, A.AGENTS[role]["system"], prompt, A.REVIEW_SCHEMA)
        except (LLMError, LimitReached) as e:
            self.finish_task(tid, {}, status="failed", error=str(e))
            raise
        status_map = {"no_issues_found": "no_issues_found", "needs_work": "needs_work", "unsupported": "disputed",
                      "flawed": "disputed", "false": "refuted"}
        with session_scope() as db:
            pmap = {_ref("P", p.id): p.id for p in db.scalars(select(ProofAttempt).where(ProofAttempt.research_run_id == self.run_id))}
            cmap = {_ref("C", c.id): c.id for c in db.scalars(select(Claim).where(Claim.research_run_id == self.run_id))}
            applied = 0
            for r in data.get("reviews", []):
                ref = r.get("target_ref", "").strip()
                rec = {"by": "agent:reviewer", "iteration": iteration, "verdict": r["verdict"], "issues": r["issues"],
                       "counterexample_attempt": r.get("counterexample_attempt"), "confidence": r.get("confidence"),
                       "at": utcnow().isoformat()}
                if ref in pmap:
                    p = db.get(ProofAttempt, pmap[ref])
                    p.reviewer_feedback = list(p.reviewer_feedback) + [rec]
                    p.status = {"no_issues_found": "review_passed"}.get(r["verdict"], "review_" + r["verdict"])
                    if r["verdict"] == "no_issues_found":
                        p.validation_level = ValidationLevel.INDEPENDENTLY_REVIEWED_PROOF
                    applied += 1
                elif ref in cmap:
                    cl = db.get(Claim, cmap[ref])
                    cl.reviews = list(cl.reviews) + [rec]
                    cl.verification_status = status_map[r["verdict"]]
                    applied += 1
            t = db.get(AgentTask, tid)
            t.status, t.current_task = "completed", None
            t.output = {**data, "applied": applied}
            t.report_markdown = data.get("summary")
            return t.output

    def run_synthesis(self, iteration: int) -> dict:
        tid, done = self.task("orchestrator", iteration, "synthesis", "identify conflicts, choose follow-ups")
        if done is not None:
            return done
        with session_scope() as db:
            c = db.get(Conjecture, self.conjecture_id)
            prompt = (conjecture_context(db, c) + "\n" + team_context(db, self.run_id, upto_iteration=iteration) +
                      f"\nThis was iteration {iteration} of at most {self.limits['max_iterations']}. "
                      f"Usage so far: {self.usage()} against limits {self.limits}.\n")
        try:
            data = self.call("orchestrator", iteration, A.ORCHESTRATOR_SYSTEM, prompt, A.SYNTHESIS_SCHEMA)
        except (LLMError, LimitReached) as e:
            self.finish_task(tid, {}, status="failed", error=str(e))
            raise
        self.finish_task(tid, data, data.get("overall_assessment"))
        return data

    # ---- main loop -----------------------------------------------------------------------------
    def run(self) -> dict:
        stop_reason = None
        try:
            it = 1
            while it <= self.limits["max_iterations"]:
                with session_scope() as db:
                    db.get(ResearchRun, self.run_id).iteration = it
                self.progress("iteration", {"iteration": it})
                if it == 1:
                    plan = {r: None for r in (*REASONING, "computational", "literature")}
                else:
                    prev = self.run_synthesis_cached(it - 1)
                    plan = {}
                    for f in prev.get("follow_ups", []):
                        if f["agent"] not in plan:
                            refs = ", ".join(f.get("refs", []))
                            plan[f["agent"]] = f["task"] + (f" (see {refs})" if refs else "")
                    if not plan:
                        stop_reason = "orchestrator assigned no follow-up tasks"
                        break
                self.checkpoint(phase=f"iteration {it}: agents", plan=plan)

                def work(role):
                    focus = plan[role]
                    if role == "computational":
                        return self.run_computational(it, focus)
                    if role == "literature":
                        return self.run_literature(it, focus)
                    return self.run_reasoning(role, it, focus)

                errors = []
                with ThreadPoolExecutor(max_workers=self.limits["concurrency"]) as ex:
                    futs = {r: ex.submit(work, r) for r in plan}
                    for r, f in futs.items():
                        try:
                            f.result()
                        except (LimitReached, Cancelled):
                            raise
                        except (LLMError, LLMUnavailable, LLMBudgetExceeded) as e:
                            errors.append(f"{r}: {e}")
                            log.warning("agent %s failed: %s", r, e)
                limit_errs = [e for e in errors if re.search(r"429|usage limit|hit your .*limit|rate.?limit", e, re.I)]
                if limit_errs:  # stop resumably; the autopilot resumes after the provider's limit resets
                    raise LLMError(f"usage limit: {limit_errs[0]}")
                if len(errors) == len(plan):
                    raise LLMError("all agents failed: " + "; ".join(errors))
                self.checkpoint(phase=f"iteration {it}: adversarial review", agent_errors=errors)
                self.run_review(it)
                self.checkpoint(phase=f"iteration {it}: synthesis")
                syn = self.run_synthesis(it)
                if not syn.get("continue_research"):
                    stop_reason = f"orchestrator: {syn.get('reason')}"
                    break
                it += 1
            else:
                stop_reason = f"iteration limit reached ({self.limits['max_iterations']})"
            final_status = "completed"
        except LimitReached as e:
            stop_reason, final_status = str(e), "completed"
            if "runtime" in str(e) and self._recent_limit_error():
                stop_reason, final_status = f"usage limit (runtime ran out while waiting): {e}", "failed"
        except Cancelled as e:
            stop_reason, final_status = str(e), "cancelled"
        except (LLMUnavailable, LLMBudgetExceeded) as e:
            stop_reason, final_status = str(e), "failed"
        except LLMError as e:
            stop_reason, final_status = str(e), "failed"

        from app.research.report import build_report, to_markdown
        with session_scope() as db:
            run = db.get(ResearchRun, self.run_id)
            run.status = final_status
            run.finished_at = utcnow()
            cp = dict(run.checkpoint or {})
            cp.update(phase="finished", stop_reason=stop_reason, usage=self.usage())
            run.checkpoint = cp
            if final_status == "failed":
                run.error = stop_reason
            db.flush()
            rep = build_report(db, run)
            run.report_markdown = to_markdown(rep)
            db.add(ConjectureEvent(conjecture_id=self.conjecture_id, event_type="research_run", actor="orchestrator",
                                   summary=f"Research run {final_status}: {stop_reason}",
                                   details={"research_run_id": self.run_id, "usage": cp["usage"]}))
        return {"status": final_status, "stop_reason": stop_reason, "usage": self.usage()}

    def _recent_limit_error(self) -> bool:
        with session_scope() as db:
            errs = db.scalars(select(LLMUsage.error).where(LLMUsage.subject_id == self.run_id,
                                                           LLMUsage.success.is_(False))).all()
            terrs = db.scalars(select(AgentTask.error).where(AgentTask.research_run_id == self.run_id)).all()
        return any(e and re.search(r"429|usage limit|hit your .*limit", e, re.I) for e in [*errs, *terrs])

    def run_synthesis_cached(self, iteration: int) -> dict:
        with session_scope() as db:
            t = db.scalars(select(AgentTask).where(AgentTask.research_run_id == self.run_id,
                                                   AgentTask.agent_role == "orchestrator",
                                                   AgentTask.iteration == iteration)).first()
            return (t.output or {}) if t else {}
