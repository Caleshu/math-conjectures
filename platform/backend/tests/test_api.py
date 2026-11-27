"""API workflow tests that need no network: manual conjecture lifecycle, provenance rules,
status overrides, job queue claiming and resumption, honest LLM unavailability."""
from datetime import datetime, timedelta, timezone

from app.db import session_scope
from app.models import CandidatePassage, Job, Paper


def _make_paper_with_candidate():
    with session_scope() as db:
        p = Paper(title="Test paper", normalized_title="test paper", authors=["A"], status="scanned")
        db.add(p)
        db.flush()
        c = CandidatePassage(paper_id=p.id, passage="\\begin{conjecture} Every X is Y. \\end{conjecture}",
                             origin="latex", char_start=10, detector="heuristic", kind="conjecture", score=0.95,
                             page_number=3, section="Main")
        db.add(c)
        db.flush()
        return p.id, c.id


BODY = {"title": "Every X is Y", "field": "graph_theory", "original_statement": "ignored-for-candidates?",
        "normalized_statement": "For all $X$, $X$ is $Y$."}


def test_health_and_settings_report_missing_integrations(client):
    assert client.get("/health").json() == {"ok": True}
    s = client.get("/api/settings").json()
    anth = next(i for i in s["integrations"] if i["key"] == "anthropic")
    assert anth["available"] is False and "ANTHROPIC_API_KEY" in anth["detail"]


def test_accept_candidate_creates_conjecture_with_provenance(client):
    pid, cid = _make_paper_with_candidate()
    r = client.post(f"/api/candidates/{cid}/accept", json={**BODY, "original_statement": "\\begin{conjecture} Every X is Y. \\end{conjecture}"})
    assert r.status_code == 200, r.text
    c = r.json()
    assert c["status"] == "UNVERIFIED" and c["source_paper_id"] == pid and c["source_page"] == 3
    assert client.post(f"/api/candidates/{cid}/accept", json=BODY).status_code == 409
    detail = client.get(f"/api/conjectures/{c['slug']}").json()
    assert detail["events"][0]["event_type"] == "created"


def test_original_statement_is_immutable_and_edits_logged(client):
    c = client.post("/api/conjectures", json={**BODY, "title": "Immutable test"}).json()
    r = client.patch(f"/api/conjectures/{c['id']}", json={"changes": {"original_statement": "changed"}})
    assert r.status_code == 422
    r = client.patch(f"/api/conjectures/{c['id']}", json={"changes": {"normalized_statement": "new"}, "note": "fix"})
    assert r.status_code == 200
    ev = client.get(f"/api/conjectures/{c['id']}").json()["events"]
    assert any(e["event_type"] == "edit" and e["summary"] == "fix" for e in ev)


def test_status_override_requires_rationale(client):
    c = client.post("/api/conjectures", json={**BODY, "title": "Override test"}).json()
    assert client.post(f"/api/conjectures/{c['id']}/status", json={"status": "SOLVED", "rationale": "short"}).status_code == 422
    r = client.post(f"/api/conjectures/{c['id']}/status", json={
        "status": "SOLVED", "rationale": "Proved in a later paper (manual check).", "evidence": [{"description": "Smith 2020, Thm 1"}]})
    assert r.status_code == 200 and r.json()["status_is_manual_override"] is True
    assert client.post(f"/api/conjectures/{c['id']}/status", json={"status": "BOGUS", "rationale": "x" * 20}).status_code == 422


def test_library_filters(client):
    client.post("/api/conjectures", json={**BODY, "title": "Number theory one", "field": "number_theory"})
    items = client.get("/api/conjectures", params={"field": "number_theory"}).json()["items"]
    assert items and all(i["field"] == "number_theory" for i in items)
    assert client.get("/api/conjectures", params={"q": "zzzz-nothing"}).json()["items"] == []


def test_llm_extraction_refuses_honestly_without_key(client):
    pid, _ = _make_paper_with_candidate()
    r = client.post(f"/api/papers/{pid}/extract", json={})
    assert r.status_code == 409 and "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_submit_rejects_garbage(client):
    assert client.post("/api/papers/submit", json={"identifier": "hello world"}).status_code == 422


def test_job_claim_and_stale_resume():
    from app.jobs import queue

    with session_scope() as db:
        j = queue.enqueue(db, "process_paper", {"paper_id": "x"})
        jid = j.id
    assert queue.claim_next("w1", ["process_paper"]) == jid
    assert queue.claim_next("w2", ["process_paper"]) is None  # cannot be claimed twice
    with session_scope() as db:
        db.get(Job, jid).heartbeat_at = datetime.now(timezone.utc) - timedelta(hours=1)
    assert queue.requeue_stale() >= 1
    with session_scope() as db:
        assert db.get(Job, jid).status == "queued"
    assert queue.claim_next("w3", ["process_paper"]) == jid


def test_experiment_requires_exactly_one_code_source(client):
    r = client.post("/api/experiments", json={"title": "bad", "problem": "bad"})
    assert r.status_code == 422
