# MathResearchLab experiment e456f51f-10ca-42b9-a045-ae254842af6f
# Independent CP-SAT computation of alpha_=(Q_n) directly on Q_n, n=3..8
# sha256(code) = 1473e8997277a17e1d4e42076ba6dad2097d1ed71068a6d4e6081cdd7f923a9e
# parameters: {"ns": [3, 4, 5, 6, 7, 8], "time_limits": {"3": 5, "4": 5, "5": 10, "6": 20, "7": 35, "8": 30}}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from ortools.sat.python import cp_model
params = json.load(open(os.environ["MRL_PARAMS"]))
ns = params.get("ns", [3, 4, 5, 6, 7, 8])
tl = params.get("time_limits", {})
t0 = time.time()

def popc(x):
    return bin(x).count("1")

def solve(n, balanced=True, limit=10.0, fix_zero=True):
    N = 1 << n
    m = cp_model.CpModel()
    x = [m.NewBoolVar("x%d" % v) for v in range(N)]
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i)
            if u > v:
                m.AddBoolOr([x[u].Not(), x[v].Not()])
    ev = [x[v] for v in range(N) if popc(v) % 2 == 0]
    od = [x[v] for v in range(N) if popc(v) % 2 == 1]
    if balanced:
        m.Add(sum(ev) == sum(od))
    if fix_zero:
        # WLOG 0 in the set: translation by an even vector preserves parity classes and edges
        m.Add(x[0] == 1)
    m.Maximize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = limit
    s.parameters.num_workers = 8
    st = s.Solve(m)
    out = {"status": s.StatusName(st), "wall": s.WallTime()}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sol = [v for v in range(N) if s.Value(x[v])]
        S = set(sol)
        out["value"] = len(sol)
        out["bound"] = s.BestObjectiveBound()
        out["check_independent"] = all((v ^ (1 << i)) not in S for v in sol for i in range(n))
        out["check_even_odd"] = [sum(1 for v in sol if popc(v) % 2 == 0), sum(1 for v in sol if popc(v) % 2 == 1)]
        out["weight_profile"] = {w: sum(1 for v in sol if popc(v) == w) for w in range(n + 1)}
    return out

sanity = {}
for n in [3, 4, 5]:
    r = solve(n, balanced=False, limit=10.0, fix_zero=False)
    sanity[n] = {"unbalanced": r, "expected": 2 ** (n - 1), "ok": r.get("value") == 2 ** (n - 1) and r["status"] == "OPTIMAL"}

res = {}
for n in ns:
    remaining = 110 - (time.time() - t0)
    if remaining < 3:
        res[n] = {"status": "NOT_RUN_time"}
        continue
    lim = min(float(tl.get(str(n), 10.0)), remaining - 2)
    res[n] = solve(n, balanced=True, limit=lim)

recorded = {3: 2, 4: 4, 5: 10, 6: 16, 7: 40}
summary = "CP-SAT balanced independent set in Q_n: " + "; ".join(
    "n=%d: %s value=%s bound=%s" % (n, res[n]["status"], res[n].get("value"), res[n].get("bound")) for n in ns) + \
    ". Sanity (unbalanced = 2^(n-1), n=3..5): %s. Recorded values: %s" % (all(v["ok"] for v in sanity.values()), recorded)
json.dump({"summary": summary, "sanity": sanity, "results": res, "recorded": recorded,
           "elapsed_s": time.time() - t0}, open("result.json", "w"), indent=1, default=str)
