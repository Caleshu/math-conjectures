import platform
import sys
from pathlib import Path

import pytest

from app.sandbox.runner import run_python

LIB = Path(__file__).resolve().parent.parent / "experiments" / "library" / "hypercube_inscribed_squares.py"


def test_result_contract_and_env_scrubbing(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    code = "import json, os\njson.dump({'x': 41 + 1, 'key': os.environ.get('ANTHROPIC_API_KEY')}, open('result.json','w'))"
    r = run_python(code, {}, tmp_path / "a", timeout_s=30, memory_mb=512)
    assert r.status == "succeeded" and r.result == {"x": 42, "key": None}
    assert r.environment["networkx"] and r.environment["ortools"]


def test_timeout_kills_process(tmp_path):
    r = run_python("while True: pass", {}, tmp_path / "b", timeout_s=2, memory_mb=512)
    assert r.status == "timeout" and r.runtime_seconds < 15


def test_failure_is_reported(tmp_path):
    r = run_python("raise SystemExit(3)", {}, tmp_path / "c", timeout_s=10, memory_mb=512)
    assert r.status == "failed" and r.exit_code == 3


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS sandbox-exec profile")
def test_macos_sandbox_blocks_network_and_outside_writes(tmp_path):
    code = (
        "import socket, json\nout={}\n"
        "try:\n open('/Users/Shared/mrl_test_escape','w').write('x'); out['write']='allowed'\n"
        "except Exception as e: out['write']=type(e).__name__\n"
        "try:\n socket.create_connection(('1.1.1.1',80),timeout=3); out['net']='allowed'\n"
        "except Exception as e: out['net']=type(e).__name__\n"
        "json.dump(out, open('result.json','w'))")
    r = run_python(code, {}, tmp_path / "d", timeout_s=20, memory_mb=512)
    assert r.result["write"] != "allowed" and r.result["net"] != "allowed"
    assert "sandbox-exec" in r.environment["isolation"]


def test_hypercube_checker_functions():
    sys.path.insert(0, str(LIB.parent))
    import hypercube_inscribed_squares as h

    assert len(h.squares(3)) == 6 and len(h.squares(4)) == 24
    assert sum(1 for _ in h.enumerate_cycles(3)) == 6
    # Q_2 is itself a 4-cycle: its unique Hamiltonian cycle has an inscribed square.
    assert h.inscribed_squares([0, 1, 3, 2], 2)
    assert h.is_hamiltonian_cycle([0, 1, 3, 2], 2) and not h.is_hamiltonian_cycle([0, 1, 2, 3], 2)


def test_hypercube_experiment_small_n(tmp_path):
    params = {"enumerate_n": [2, 3, 4], "cpsat_n": [2, 3, 4], "min_squares_n": [3, 4], "time_limit_s": 60, "workers": 4}
    r = run_python(LIB.read_text(), params, tmp_path / "e", timeout_s=240, memory_mb=2048)
    assert r.status == "succeeded", r.stderr
    res = r.result
    assert [e["hamiltonian_cycles"] for e in res["enumeration"]] == [1, 6, 1344]  # OEIS A066037
    assert res["summary"]["model_sanity_passed"] and res["summary"]["cross_checks_passed"]
    assert res["summary"]["counterexample_found"] is False
