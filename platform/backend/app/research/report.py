"""Structured research report, built only from what is stored in the database.

The report separates:
  * Established facts: known results recorded with a citation, plus trusted finite computations.
  * Claims by verification state: refuted / disputed / needs work / no issues found by AI review / unreviewed.
  * Speculative ideas: claims whose own author rated them heuristic or speculative.
Nothing the agents said is listed as established.
"""
from __future__ import annotations

from sqlalchemy import select

from app.models import AgentTask, Claim, Conjecture, Experiment, Paper, ProofAttempt, ResearchRun
from app.research.agents import AGENTS

LEVEL_NAMES = {1: "idea", 2: "experimental evidence", 3: "finite computational result", 4: "written proof attempt",
               5: "independently reviewed proof (AI reviewer)", 6: "formally verified (Lean)"}


def _claim(c: Claim) -> dict:
    return {"id": c.id, "ref": f"C-{c.id[:6]}", "statement": c.statement, "type": c.claim_type, "author": c.created_by,
            "author_support": (c.details or {}).get("author_support"), "confidence": (c.details or {}).get("confidence"),
            "iteration": (c.details or {}).get("iteration"), "status": c.verification_status,
            "level": c.validation_level, "level_name": LEVEL_NAMES.get(c.validation_level),
            "justification": next((e.get("text") for e in c.evidence if e.get("type") == "author_justification"), ""),
            "evidence": [e for e in c.evidence if e.get("type") != "author_justification"],
            "reviews": c.reviews, "experiment_id": c.experiment_id, "related": c.related_claim_ids}


def build_report(db, run: ResearchRun) -> dict:
    c: Conjecture = db.get(Conjecture, run.conjecture_id)
    src = db.get(Paper, c.source_paper_id) if c.source_paper_id else None
    tasks = db.scalars(select(AgentTask).where(AgentTask.research_run_id == run.id).order_by(AgentTask.created_at)).all()
    claims = [_claim(x) for x in db.scalars(select(Claim).where(Claim.research_run_id == run.id)
                                            .order_by(Claim.created_at))]
    proofs = db.scalars(select(ProofAttempt).where(ProofAttempt.research_run_id == run.id)
                        .order_by(ProofAttempt.created_at)).all()
    exps = db.scalars(select(Experiment).where(Experiment.research_run_id == run.id).order_by(Experiment.created_at)).all()

    roles = []
    for t in tasks:
        if t.agent_role not in roles:
            roles.append(t.agent_role)
    approaches, failed, next_steps, requests, lit = [], [], [], [], []
    syntheses = []
    for t in tasks:
        o = t.output or {}
        for f in o.get("failed_approaches", []):
            failed.append({**f, "agent": t.agent_role})
        for s in o.get("next_steps", []):
            next_steps.append({"text": s, "agent": t.agent_role})
        for r in o.get("experiment_requests", []):
            requests.append({**r, "agent": t.agent_role})
        if t.agent_role == "literature" and o.get("relevant_works"):
            lit.append({"works": o["relevant_works"], "novelty": o.get("novelty_assessment")})
        if t.agent_role == "orchestrator":
            syntheses.append({"iteration": t.iteration, **o})
        if o.get("summary") and t.agent_role != "orchestrator":
            approaches.append({"agent": t.agent_role, "iteration": t.iteration,
                               "phase": (t.input or {}).get("phase"), "summary": o["summary"]})
    lit_queries = next(((t.output or {}).get("queries") for t in tasks
                        if t.agent_role == "literature" and (t.input or {}).get("phase") == "queries"), [])
    lit_errors = {}
    for t in tasks:
        if t.agent_role == "literature":
            lit_errors.update((t.output or {}).get("source_errors", {}))

    trusted_finite = [e for e in exps if e.status == "succeeded" and e.result_kind == "finite_computation"
                      and e.interpretation and "UNTRUSTWORTHY" not in e.interpretation]
    established = [{"statement": k.get("statement"), "citation": k.get("citation"),
                    "reproduced": k.get("reproduced"), "computational": k.get("is_computational")}
                   for k in c.known_results]
    speculative = [x for x in claims if x["author_support"] in ("heuristic", "speculative") and x["status"] != "refuted"]
    groups = {
        "refuted": [x for x in claims if x["status"] == "refuted"],
        "disputed": [x for x in claims if x["status"] == "disputed"],
        "needs_work": [x for x in claims if x["status"] == "needs_work"],
        "no_issues_found": [x for x in claims if x["status"] == "no_issues_found"],
        "unreviewed": [x for x in claims if x["status"] == "unverified"],
    }
    cp = run.checkpoint or {}
    return {
        "run": {"id": run.id, "status": run.status, "limits": run.limits, "iterations": run.iteration,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "stop_reason": cp.get("stop_reason"), "usage": cp.get("usage"), "error": run.error},
        "conjecture": {"id": c.id, "slug": c.slug, "title": c.title, "status": c.status,
                       "original_statement": c.original_statement, "normalized_statement": c.normalized_statement,
                       "definitions": c.definitions},
        "source": {"title": src.title if src else None, "authors": src.authors if src else [],
                   "arxiv_id": src.arxiv_id if src else None, "doi": src.doi if src else None,
                   "year": src.published_date.year if src and src.published_date else None},
        "established": established,
        "trusted_computations": [{"id": e.id, "title": e.title, "interpretation": e.interpretation}
                                 for e in trusted_finite],
        "agents": [{"role": r, "name": AGENTS.get(r, {}).get("name", "Orchestrator")} for r in roles],
        "approaches": approaches,
        "claims": claims,
        "claim_groups": groups,
        "candidate_lemmas": [x for x in claims if x["type"] in ("lemma", "reduction", "bound") and x["status"] != "refuted"],
        "counterexamples": [x for x in claims if x["type"] in ("counterexample_candidate", "construction")],
        "speculative": speculative,
        "experiments": [{"id": e.id, "title": e.title, "status": e.status, "kind": e.result_kind,
                         "runtime_s": e.runtime_seconds, "summary": (e.result or {}).get("summary")
                         if isinstance(e.result, dict) else None, "interpretation": e.interpretation,
                         "isolation": (e.environment or {}).get("isolation")} for e in exps],
        "proof_attempts": [{"id": p.id, "ref": f"P-{p.id[:6]}", "strategy": p.strategy, "argument": p.argument,
                            "author": p.created_by, "status": p.status, "level": p.validation_level,
                            "level_name": LEVEL_NAMES.get(p.validation_level), "known_gaps": p.known_gaps,
                            "lemmas": [x.get("statement") for x in p.lemma_claim_ids],
                            "reviews": p.reviewer_feedback} for p in proofs],
        "literature": {"queries": lit_queries, "assessments": lit, "source_errors": lit_errors},
        "failed_approaches": failed,
        "conflicts": [dict(x, iteration=s["iteration"]) for s in syntheses for x in s.get("conflicts", [])],
        "syntheses": syntheses,
        "open_experiment_requests": requests,
        "next_steps": ([{"text": t, "agent": "orchestrator"} for s in syntheses[-1:]
                        for t in s.get("recommended_next_steps", [])] + next_steps),
    }


def _md_claim(x: dict) -> str:
    rv = ""
    if x["reviews"]:
        r = x["reviews"][-1]
        issues = "; ".join(f"{i['kind']}: {i['detail']}" for i in r.get("issues", []))
        rv = f"\n  - *Reviewer:* **{r['verdict']}**{(' — ' + issues) if issues else ''}"
        if r.get("counterexample_attempt"):
            rv += f"\n  - *Counterexample attempt:* {r['counterexample_attempt']}"
    return (f"- **[{x['ref']}]** ({x['type']}; by {x['author'].replace('agent:', '')}; author's support: "
            f"{x['author_support']}; level: {x['level_name']})\n  {x['statement']}" +
            (f"\n  - *Justification:* {x['justification']}" if x["justification"] else "") + rv)


def to_markdown(r: dict) -> str:
    c, run, s = r["conjecture"], r["run"], r["source"]
    L = [f"# Research report: {c['title']}", "",
         f"Run `{run['id']}`. Status **{run['status']}**, {run['iterations']} iteration(s). "
         f"Stopped because: {run['stop_reason'] or 'n/a'}.",
         f"Usage: {run['usage']}. Limits: {run['limits']}.", "",
         "> Everything under *Claims*, *Candidate lemmas*, *Proof attempts* and *Speculative ideas* was produced by AI "
         "agents and is **not established**. \"No issues found\" means an AI reviewer did not find an error. It is "
         "not a certification. Only results under *Established facts* carry a citation or a reproduced computation.",
         "", "## Original conjecture", "", c["original_statement"], ""]
    if c.get("normalized_statement"):
        L += ["**Normalized statement.** " + c["normalized_statement"], ""]
    L += ["## Source", "", f"{', '.join(s['authors'] or [])}, *{s['title']}* ({s['year']})"
          + (f", arXiv:{s['arxiv_id']}" if s.get("arxiv_id") else "") + (f", doi:{s['doi']}" if s.get("doi") else ""), ""]
    if c.get("definitions"):
        L += ["## Definitions", ""] + [f"- **{d.get('term')}**: {d.get('definition')}" for d in c["definitions"]] + [""]
    L += ["## Established facts", "", "*Known results recorded with citations:*", ""]
    L += [f"- {k['statement']} ({k['citation']}; computational: {k['computational']}; reproduced: {k['reproduced']})"
          for k in r["established"]] or ["- none recorded"]
    L += ["", "*Finite computations run in this research and judged trustworthy (finite results, not proofs):*", ""]
    L += [f"- {e['title']}: {e['interpretation']}" for e in r["trusted_computations"]] or ["- none"]
    L += ["", "## Agents involved", ""] + [f"- {a['name']}" for a in r["agents"]]
    L += ["", "## Approaches attempted", ""]
    L += [f"- **{a['agent']}** (iteration {a['iteration']}, {a['phase']}): {a['summary']}" for a in r["approaches"]] or ["- none"]
    titles = {"refuted": "Refuted by review", "disputed": "Disputed (flawed or unsupported)", "needs_work": "Needs work",
              "no_issues_found": "No issues found by the AI reviewer", "unreviewed": "Not reviewed"}
    L += ["", "## Mathematical claims", ""]
    for k, t in titles.items():
        if r["claim_groups"][k]:
            L += [f"### {t}", ""] + [_md_claim(x) for x in r["claim_groups"][k]] + [""]
    if not r["claims"]:
        L += ["- none", ""]
    L += ["## Computational experiments", ""]
    L += [f"- **{e['title']}** [{e['status']}, {e['kind']}, {e['runtime_s']}s, isolation {e['isolation']}]: "
          f"{e['summary'] or ''}\n  - *Interpretation:* {e['interpretation'] or 'none'}" for e in r["experiments"]] or ["- none"]
    L += ["", "## Candidate lemmas", ""] + ([f"- [{x['ref']}] {x['statement']} *(status: {x['status']})*"
                                           for x in r["candidate_lemmas"]] or ["- none"])
    L += ["", "## Proof attempts", ""]
    for p in r["proof_attempts"]:
        L += [f"### [{p['ref']}] {p['strategy']}", "", f"By {p['author']}. Status **{p['status']}**, level {p['level_name']}.",
              "", p["argument"], ""]
        if p["known_gaps"]:
            L += ["*Gaps admitted by the author:*"] + [f"- {g}" for g in p["known_gaps"]] + [""]
        for rv in p["reviews"]:
            L += [f"*Reviewer verdict:* **{rv['verdict']}**"] + [f"- {i['kind']}: {i['detail']}" for i in rv.get("issues", [])] + [""]
    if not r["proof_attempts"]:
        L += ["- none", ""]
    L += ["## Counterexamples and constructions", ""] + ([f"- [{x['ref']}] {x['statement']} *(status: {x['status']})*"
                                                         for x in r["counterexamples"]] or ["- none"])
    L += ["", "## Literature", ""]
    if r["literature"]["queries"]:
        L += ["Queries: " + "; ".join(q["text"] for q in r["literature"]["queries"]), ""]
    for a in r["literature"]["assessments"]:
        for w in a["works"]:
            rec = w["record"]
            L.append(f"- *{rec['title']}* ({rec.get('year')}{', arXiv:' + rec['arxiv_id'] if rec.get('arxiv_id') else ''}"
                     f"{', doi:' + rec['doi'] if rec.get('doi') else ''}): {w['relevance']}. {w['how_it_relates']}"
                     + (" **May resolve the conjecture; check it.**" if w.get("may_resolve_conjecture") else ""))
        if a.get("novelty"):
            L += ["", f"*Novelty assessment:* {a['novelty']}"]
    if r["literature"]["source_errors"]:
        L += ["", "*Source errors (coverage incomplete):* " + "; ".join(f"{k}: {v}" for k, v in r["literature"]["source_errors"].items())]
    L += ["", "## Failed approaches", ""] + ([f"- **{f['approach']}** ({f['agent']}): {f['why_it_fails']}"
                                            for f in r["failed_approaches"]] or ["- none"])
    L += ["", "## Conflicts identified", ""] + ([f"- (iteration {x['iteration']}) {x['description']} "
                                                f"[{', '.join(x['refs'])}]. To resolve: {x['how_to_resolve']}"
                                                for x in r["conflicts"]] or ["- none"])
    L += ["", "## Speculative ideas", ""] + ([f"- [{x['ref']}] {x['statement']}" for x in r["speculative"]] or ["- none"])
    L += ["", "## Unresolved gaps", ""]
    gaps = [f"- [{p['ref']}] {g}" for p in r["proof_attempts"] for g in p["known_gaps"]]
    gaps += [f"- [{x['ref']}] reviewer: {i['detail']}" for x in r["claims"] for rv in x["reviews"][-1:]
             for i in rv.get("issues", []) if x["status"] in ("disputed", "needs_work")]
    L += gaps or ["- none recorded"]
    L += ["", "## Recommended next steps", ""] + ([f"- {n['text']} *({n['agent']})*" for n in r["next_steps"]] or ["- none"])
    if r["syntheses"]:
        L += ["", "## Orchestrator assessment", "", r["syntheses"][-1].get("overall_assessment", "")]
    return "\n".join(L) + "\n"
