"""Orchestrator tests with a scripted stand-in for the model (test-only; the app never uses it).

Exercises the real orchestration: task checkpointing, storage of claims/proofs with authorship,
real sandbox execution of the agent's program, review mapping, limits, resume and cancellation.
"""
import json
import uuid

import pytest

from app.db import session_scope
from app.llm.base import LLMResult
from app.models import AgentTask, Claim, Conjecture, Experiment, LLMUsage, ProofAttempt, ResearchRun

PROGRAM = """
import json, os, itertools
p = json.load(open(os.environ["MRL_PARAMS"]))
res = {}
for n in range(2, p["n_max"] + 1):
    res[str(n)] = 2 ** n
json.dump({"summary": "vertex counts", "counts": res, "sanity_ok": res["2"] == 4}, open("result.json", "w"))
"""


def _claim(stmt, kind="lemma", support="sketch"):
    return {"statement": stmt, "claim_type": kind, "justification": "because", "author_support": support,
            "confidence": 0.6, "related_refs": []}


class Script:
    """Returns schema-shaped data per agent role; records every call."""

    def __init__(self, cont=False):
        self.calls = []
        self.cont = cont

    def __call__(self, *, purpose, system, prompt, schema, provider=None, job_id=None, subject_id=None,
                 max_tokens=0, effort="high"):
        role = purpose.split(":", 1)[1]
        self.calls.append((role, prompt))
        props = schema["properties"]
        if "queries" in props:
            data = {"queries": [{"text": "hypercube squares", "rationale": "r"}]}
        elif "relevant_works" in props:
            data = {"summary": "lit", "relevant_works": [{"ref": "L1", "relevance": "direct", "how_it_relates": "x",
                                                          "may_resolve_conjecture": False},
                                                         {"ref": "L99", "relevance": "direct", "how_it_relates": "made up",
                                                          "may_resolve_conjecture": True}],
                    "novelty_assessment": "n", "claims": [_claim("known technique L1", "literature", "recalled_literature")],
                    "next_steps": []}
        elif "experiments" in props:
            data = {"summary": "plan", "experiments": [{"title": "count", "question": "q", "hypothesis": "h",
                                                        "result_kind": "finite_computation", "code": PROGRAM,
                                                        "parameters_json": "{\"n_max\": 4}"}]}
        elif "interpretations" in props:
            eref = next(l.split(":")[0].replace("### ", "") for l in prompt.splitlines() if l.startswith("### E-"))
            data = {"summary": "interp", "interpretations": [{"experiment_ref": eref, "interpretation": "ok",
                                                              "trustworthy": True}],
                    "claims": [_claim("Q_n has 2^n vertices for n<=4", "observation", "proved_here")], "next_steps": []}
        elif "reviews" in props:
            refs = [l.split(":")[0].replace("### ", "") for l in prompt.splitlines() if l.startswith("### ")]
            data = {"summary": "rev", "reviews": [{"target_ref": r, "verdict": "false" if i == 0 else "no_issues_found",
                                                   "issues": [{"kind": "boundary_case", "detail": "n=2"}] if i == 0 else [],
                                                   "counterexample_attempt": "tried", "confidence": 0.7}
                                                  for i, r in enumerate(refs)]}
        elif "follow_ups" in props:
            data = {"overall_assessment": "a", "conflicts": [{"description": "c", "refs": [], "how_to_resolve": "h"}],
                    "follow_ups": [{"agent": "construction", "task": "attack the lemma", "refs": []}] if self.cont else [],
                    "continue_research": self.cont, "reason": "done", "recommended_next_steps": ["think"]}
        else:
            data = {"summary": f"{role} summary", "claims": [_claim(f"{role} lemma")],
                    "proof_attempts": [{"strategy": f"{role} strategy", "target": "full", "argument": "arg",
                                        "lemmas": ["l"], "known_gaps": ["gap"]}] if role == "strategist" else [],
                    "failed_approaches": [{"approach": "naive", "why_it_fails": "fails"}],
                    "experiment_requests": [], "next_steps": ["more"]}
        with session_scope() as db:
            db.add(LLMUsage(provider="test", model="scripted", purpose=purpose, input_tokens=10, output_tokens=10,
                            cost_usd=0, subject_id=subject_id, success=True))
        return LLMResult(data=data, provider="test", model="scripted")


@pytest.fixture
def setup(monkeypatch):
    from app.research import orchestrator
    from app.sources import registry
    from app.sources.base import PaperRecord

    monkeypatch.setattr(registry, "federated_search",
                        lambda q, s: ([PaperRecord(source="arxiv", title="A real-looking record", authors=["X"])], {}))
    with session_scope() as db:
        c = Conjecture(slug=f"t-{uuid.uuid4().hex[:10]}", title="Test conjecture", field="graph_theory",
                       original_statement="Every H has a square.", normalized_statement="Every H has a square.",
                       created_by="test")
        db.add(c)
        db.flush()
        cid = c.id

    def make(limits=None, cont=False):
        script = Script(cont)
        monkeypatch.setattr(orchestrator, "tracked_json_call", script)
        with session_scope() as db:
            r = ResearchRun(conjecture_id=cid, limits=orchestrator.normalize_limits(limits or {}))
            db.add(r)
            db.flush()
            return r.id, script
    return make


def test_full_run_stores_attributed_work_and_report(setup):
    from app.research.orchestrator import Orchestrator
    rid, script = setup({"max_iterations": 1, "concurrency": 2})
    out = Orchestrator(rid).run()
    assert out["status"] == "completed"
    roles = [c[0] for c in script.calls]
    for r in ("strategist", "extremal", "construction", "computational", "literature", "reviewer", "orchestrator"):
        assert r in roles
    # independence: first-pass prompts never contain other agents' output
    for role, prompt in script.calls:
        if role in ("strategist", "extremal", "construction"):
            assert "lemma" not in prompt.split("## Your task")[0].lower() or "Team results" not in prompt
            assert "Team results so far" not in prompt
    with session_scope() as db:
        claims = db.query(Claim).filter_by(research_run_id=rid).all()
        assert {c.created_by for c in claims} >= {"agent:strategist", "agent:extremal", "agent:construction",
                                                  "agent:computational", "agent:literature"}
        assert any(c.verification_status == "no_issues_found" and c.reviews for c in claims)
        assert all(c.verification_status != "verified" for c in claims)
        exp = db.query(Experiment).filter_by(research_run_id=rid).one()
        assert exp.status == "succeeded" and exp.result["counts"]["4"] == 16  # really ran in the sandbox
        obs = next(c for c in claims if c.created_by == "agent:computational")
        assert obs.validation_level == 3
        pa = db.query(ProofAttempt).filter_by(research_run_id=rid).one()
        assert pa.reviewer_feedback and pa.status == "review_false" and pa.validation_level == 4
        run = db.get(ResearchRun, rid)
        md = run.report_markdown
    assert "## Established facts" in md and "not established" in md and "## Proof attempts" in md
    assert "made up" not in md  # literature refs that did not come from real search results are dropped


def test_model_call_limit_stops_run_and_still_reports(setup):
    from app.research.orchestrator import Orchestrator
    rid, script = setup({"max_model_calls": 6, "concurrency": 1, "max_experiments": 0})
    out = Orchestrator(rid).run()
    assert out["status"] == "completed" and "model-call limit" in out["stop_reason"]
    assert len(script.calls) <= 6
    with session_scope() as db:
        assert db.get(ResearchRun, rid).report_markdown


def test_resume_does_not_repeat_finished_tasks(setup):
    from app.research.orchestrator import Orchestrator
    rid, script = setup({"max_iterations": 1, "max_experiments": 0})
    Orchestrator(rid).run()
    with session_scope() as db:
        n_claims = db.query(Claim).filter_by(research_run_id=rid).count()
        n_tasks = db.query(AgentTask).filter_by(research_run_id=rid).count()
        db.get(ResearchRun, rid).status = "failed"
    before = len(script.calls)
    Orchestrator(rid).run()
    assert len(script.calls) == before  # everything was checkpointed
    with session_scope() as db:
        assert db.query(Claim).filter_by(research_run_id=rid).count() == n_claims
        assert db.query(AgentTask).filter_by(research_run_id=rid).count() == n_tasks


def test_second_iteration_runs_only_follow_ups_and_sees_team_work_as_unverified(setup):
    from app.research.orchestrator import Orchestrator
    rid, script = setup({"max_iterations": 2, "max_experiments": 0}, cont=True)
    Orchestrator(rid).run()
    with session_scope() as db:
        it2 = db.query(AgentTask).filter_by(research_run_id=rid, iteration=2).all()
        assert {t.agent_role for t in it2} == {"construction", "reviewer", "orchestrator"}
    p2 = [p for r, p in script.calls if r == "construction"][-1]
    assert "UNVERIFIED" in p2 and "attack the lemma" in p2


def test_cancel(setup):
    from app.research.orchestrator import Orchestrator
    rid, _ = setup()
    o = Orchestrator(rid)
    with session_scope() as db:
        db.get(ResearchRun, rid).status = "cancelling"
    assert o.run()["status"] == "cancelled"


def test_launch_api_refuses_without_provider(client):
    from app.models import Conjecture
    with session_scope() as db:
        c = Conjecture(slug="api-launch-test", title="T", field="graph_theory", original_statement="S", normalized_statement="S", created_by="t")
        db.add(c)
        db.flush()
        cid = c.id
    r = client.post("/api/research/runs", json={"conjecture_id": cid})
    assert r.status_code == 409
    assert client.get("/api/research/meta").json()["agents"][0]["role"] == "strategist"


def test_usage_limit_stops_run_resumably(setup):
    """A provider usage limit (HTTP 429) must leave the run failed (resumable), not 'completed'."""
    from app.llm.base import LLMError
    from app.research import orchestrator
    from app.research.orchestrator import Orchestrator
    rid, script = setup({"max_iterations": 1, "max_experiments": 0})
    inner = orchestrator.tracked_json_call

    def limited(**kw):
        if kw["purpose"] == "research:extremal":
            raise LLMError("Claude Code call failed: API error 429: You've hit your 5-hour limit · resets 4:10am (America/New_York)")
        return inner(**kw)

    orchestrator.tracked_json_call = limited
    try:
        out = Orchestrator(rid).run()
    finally:
        orchestrator.tracked_json_call = inner
    assert out["status"] == "failed" and "usage limit" in out["stop_reason"]
    from app.autopilot import is_rate_limit
    with session_scope() as db:
        assert is_rate_limit(db.get(ResearchRun, rid).error)
