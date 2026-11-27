# MathResearchLab experiment 56436f80-8eed-4355-93e1-69518a417b33
# Q6: CP-SAT realisation of vectors satisfying the projection condition (P+), tight-boundary cases first
# sha256(code) = 3206d91451e814361766180ec818b2e017b2ced2feb5fb94e03296ec18e4e9c1
# parameters: {"tl_n5": 5.0, "tl_n6": 3.0, "tl_control": 4.0, "budget": 105.0, "n_control": 3, "workers": 8}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, itertools, random
from ortools.sat.python import cp_model

params = json.load(open(os.environ["MRL_PARAMS"]))
TL5 = float(params.get("tl_n5", 5.0))
TL6 = float(params.get("tl_n6", 3.0))
TLC = float(params.get("tl_control", 4.0))
BUDGET = float(params.get("budget", 105.0))
N_CONTROL = int(params.get("n_control", 3))
WORKERS = int(params.get("workers", 8))
T0 = time.time()

def enum_images(n):
    N = 1 << n
    vis = [False]*N; vis[0] = True
    cnt = [0]*n; image = set(); ncyc = [0]
    def dfs(v, depth):
        if depth == N:
            x = v
            if x and (x & (x-1)) == 0:
                i = x.bit_length()-1
                cnt[i] += 1; image.add(tuple(sorted(cnt))); ncyc[0] += 1; cnt[i] -= 1
            return
        for i in range(n):
            u = v ^ (1 << i)
            if not vis[u]:
                vis[u] = True; cnt[i] += 1
                dfs(u, depth+1)
                vis[u] = False; cnt[i] -= 1
    dfs(0, 1)
    return ncyc[0], image

def candidates(n):
    half = 1 << (n-1); cap = max(1, 1 << (n-2)); res = []
    def rec(remaining, k, minpart, cur):
        if k == 0:
            if remaining == 0: res.append(tuple(2*x for x in cur))
            return
        for p in range(minpart, min(cap, remaining)+1):
            if p*k > remaining: break
            rec(remaining-p, k-1, p, cur+[p])
    rec(half, n, 1, [])
    return res

def subset_ok(c):
    s = sorted(c); acc = 0
    for k in range(1, len(s)+1):
        acc += s[k-1]
        if acc < (1 << k): return False
    return acc == (1 << len(s))

def tight_count(c):
    n = len(c); t = 0
    for k in range(2, n):
        for S in itertools.combinations(range(n), k):
            if sum(c[i] for i in S) == (1 << k): t += 1
    return t

def recursive_ok(c, images):
    n = len(c)
    for k in range(2, n):
        for S in itertools.combinations(range(n), k):
            sub = tuple(sorted(c[i] for i in S))
            if sum(sub) == (1 << k):
                if k not in images: return None
                if sub not in images[k]: return False
    return True

def check_cycle(n, succ):
    N = 1 << n
    if len(succ) != N: return False, None
    cnt = [0]*n; v = 0; seen = set()
    for _ in range(N):
        if v in seen: return False, None
        seen.add(v); u = succ[v]; x = u ^ v
        if x == 0 or (x & (x-1)): return False, None
        cnt[x.bit_length()-1] += 1; v = u
    return (v == 0 and len(seen) == N), cnt

def solve(n, c, tl):
    N = 1 << n
    m = cp_model.CpModel(); arcs = []; lits = {}; dimlits = [[] for _ in range(n)]
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i); b = m.NewBoolVar("")
            arcs.append((v, u, b)); lits[(v, u)] = b; dimlits[i].append(b)
    m.AddCircuit(arcs)
    if c is not None:
        for i in range(n): m.Add(sum(dimlits[i]) == c[i])
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl; s.parameters.num_search_workers = WORKERS
    st = s.Solve(m)
    out = {"status": s.StatusName(st), "wall": round(s.WallTime(), 3)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {}; nt = 0
        for (v, u), b in lits.items():
            if s.Value(b): succ[v] = u; nt += 1
        ok, vec = check_cycle(n, succ)
        ok = ok and nt == N and (c is None or vec == list(c))
        out["verified"] = ok
    return out

res = {}
images = {}
for n in (2, 3, 4):
    nc, im = enum_images(n); images[n] = im
    res["Q%d_undirected_cycles" % n] = nc // 2
res["Q4_image"] = sorted(list(x) for x in images[4])
res["sanity_unconstrained_Q6"] = solve(6, None, 10.0)

# Q5 image: solve all candidates satisfying P (those violating P are excluded by the projection lemma)
q5 = []
for c in candidates(5):
    if not subset_ok(c):
        q5.append({"c": list(c), "status": "EXCLUDED_BY_P"}); continue
    out = solve(5, c, TL5); out["c"] = list(c); out["Pplus"] = recursive_ok(c, images); q5.append(out)
res["Q5_rows"] = q5
q5_unknown = [r["c"] for r in q5 if r["status"] not in ("OPTIMAL", "FEASIBLE", "INFEASIBLE", "EXCLUDED_BY_P")]
images[5] = set(tuple(r["c"]) for r in q5 if r["status"] in ("OPTIMAL", "FEASIBLE") and r.get("verified"))
res["Q5_image"] = sorted(list(x) for x in images[5])
res["Q5_unknown"] = q5_unknown
res["Q5_infeasible_with_P"] = [r["c"] for r in q5 if r["status"] == "INFEASIBLE"]

# n=6
cands = candidates(6)
classified = []
for c in cands:
    p = subset_ok(c)
    pp = recursive_ok(c, images) if p else False
    classified.append((c, p, pp))
res["n6_num_basic_candidates"] = len(cands)
res["n6_num_P"] = sum(1 for x in classified if x[1])
res["n6_num_Pplus"] = sum(1 for x in classified if x[2])
res["n6_excluded_by_P_only_recursion"] = [list(c) for c, p, pp in classified if p and not pp]
test = [c for c, p, pp in classified if pp]
test.sort(key=lambda c: (-tight_count(c), c))
rows = []
for c in test:
    if time.time()-T0 > BUDGET - (N_CONTROL*TLC + 5):
        rows.append({"c": list(c), "status": "NOT_RUN_BUDGET", "tight": tight_count(c)}); continue
    out = solve(6, c, TL6); out["c"] = list(c); out["tight"] = tight_count(c); rows.append(out)
res["n6_rows"] = rows
viol = [c for c, p, pp in classified if not p]
random.seed(1)
ctrl = []
for c in random.sample(viol, min(N_CONTROL, len(viol))):
    if time.time()-T0 > BUDGET: break
    out = solve(6, c, TLC); out["c"] = list(c); ctrl.append(out)
res["n6_control_violating_P"] = ctrl
fe = [r["c"] for r in rows if r["status"] in ("OPTIMAL", "FEASIBLE") and r.get("verified")]
inf = [r["c"] for r in rows if r["status"] == "INFEASIBLE"]
unk = [r["c"] for r in rows if r["status"] == "UNKNOWN"]
nr = [r["c"] for r in rows if r["status"] == "NOT_RUN_BUDGET"]
bug = [r["c"] for r in rows if r["status"] in ("OPTIMAL", "FEASIBLE") and not r.get("verified")]
ctrl_bug = [r["c"] for r in ctrl if r["status"] in ("OPTIMAL", "FEASIBLE")]
res["n6_feasible_count"] = len(fe); res["n6_infeasible"] = inf; res["n6_unknown"] = unk; res["n6_not_run_count"] = len(nr)
res["elapsed"] = round(time.time()-T0, 2)
res["summary"] = ("Q4 image %s; Q5 image (%d vectors) %s; Q5 unknown %s; Q5 infeasible despite P %s; sanity Q6 unconstrained %s; "
    "n6: %d basic candidates, %d satisfy P, %d satisfy P+, P-but-not-P+ %s; tested feasible %d, INFEASIBLE %s, UNKNOWN %s, not run %d, unverified-bug %s; control (violating P) statuses %s, control-bug %s; elapsed %.1fs") % (
    res["Q4_image"], len(images[5]), res["Q5_image"], q5_unknown, res["Q5_infeasible_with_P"], res["sanity_unconstrained_Q6"]["status"],
    len(cands), res["n6_num_P"], res["n6_num_Pplus"], res["n6_excluded_by_P_only_recursion"], len(fe), inf, unk, len(nr), bug,
    [(r["c"], r["status"]) for r in ctrl], ctrl_bug, res["elapsed"])
json.dump(res, open("result.json", "w"), indent=1)
print(res["summary"])
