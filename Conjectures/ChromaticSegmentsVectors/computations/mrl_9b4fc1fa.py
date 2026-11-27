# MathResearchLab experiment 9b4fc1fa-3f80-4996-b989-4c71e558bbf5
# CP-SAT realizability of chromatic-segment lists: validation on n<=4, partial test on n=5
# sha256(code) = 746dc46257cca8bdadb15d704520d8b82b92e87bbce29c88281c0fb951d0cf3c
# parameters: {"time_budget": 100, "per_solve": 4.0, "seed": 1, "n_neg_controls": 30}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, random
from ortools.sat.python import cp_model
params = json.load(open(os.environ["MRL_PARAMS"]))
T = params.get("time_budget", 100)
per = params.get("per_solve", 4.0)
random.seed(params.get("seed", 1))
n_neg = params.get("n_neg_controls", 30)
t0 = time.time()

def comps(total, minpart=2):
    if total == 0:
        yield (); return
    for a in range(minpart, total+1):
        for rest in comps(total-a, minpart):
            yield (a,) + rest

def color_balanced(d):
    s = 0; imb = [0, 0]
    for k, x in enumerate(d):
        hb = 1 if k % 2 == 0 else 0
        if x % 2 == 1:
            imb[hb] += 1 if s == 0 else -1
        s = (s + x - 1) % 2
    return imb == [0, 0]

def orbit(d):
    c = len(d); r = (d[0],) + tuple(reversed(d[1:]))
    out = []
    for base in (d, r):
        for k in range(0, c, 2):
            out.append(base[k:] + base[:k])
    return out

def canon(d): return min(orbit(d))

def weak_candidates(n):
    H = 1 << (n-1)
    A = list(comps(H))
    W = set()
    for a in A:
        for b in A:
            if len(a) == len(b):
                d = []
                for x, y in zip(a, b): d += [x, y]
                W.add(tuple(d))
    return W

def delta_of(h):
    N = len(h)
    if (h[0] & 1) != 0 or h[1] != h[0] ^ 1: return None
    js = [j for j in range(N) if h[j] ^ h[(j+1) % N] == 1]
    return tuple(js[k+1]-js[k] for k in range(len(js)-1)) + (N - js[-1],)

def is_ham(h, n):
    N = 1 << n
    if len(h) != N or len(set(h)) != N: return False
    return all(bin(h[p] ^ h[(p+1) % N]).count('1') == 1 for p in range(N))

def solve(delta, n, tlim):
    N = 1 << n; M = 1 << (n-1)
    js = [0]
    for d in delta[:-1]: js.append(js[-1] + d)
    iedge = set(js)
    half = [0]*N; b = 0
    for p in range(N):
        half[p] = b
        if p in iedge: b ^= 1
    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f"x{p}_{v}") for v in range(M)] for p in range(N)]
    for p in range(N): m.AddExactlyOne(x[p])
    for hb in (0, 1):
        P = [p for p in range(N) if half[p] == hb]
        assert len(P) == M, (delta, hb, len(P))
        for v in range(M): m.AddExactlyOne([x[p][v] for p in P])
    for p in range(N):
        q = (p+1) % N
        for v in range(M):
            if p in iedge:
                m.AddImplication(x[p][v], x[q][v])
            else:
                m.AddBoolOr([x[q][v ^ (1 << a)] for a in range(n-1)]).OnlyEnforceIf(x[p][v])
    # symmetry breaking: Q_{n-1} automorphisms preserve delta_0
    m.Add(x[0][0] == 1)
    m.Add(x[2][1] == 1)  # valid since delta[0]>=2 so step 1->2 is a non-0 edge; coordinate permutation
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tlim; s.parameters.num_workers = 8
    st = s.Solve(m); name = s.StatusName(st)
    verified = None; cyc = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        proj = [next(v for v in range(M) if s.Value(x[p][v])) for p in range(N)]
        h = [(proj[p] << 1) | half[p] for p in range(N)]
        verified = is_ham(h, n) and delta_of(h) == tuple(delta)
        cyc = h
    return name, verified, cyc

out = {"small_n": {}, "n5": {}}
bugs = []
# Part A: n=2,3,4 all raw weak candidates
for n in (2, 3, 4):
    W = sorted(weak_candidates(n))
    rec = {"tested": 0, "feasible": [], "infeasible": [], "unknown": []}
    for d in W:
        name, ver, _ = solve(d, n, per)
        rec["tested"] += 1
        if name in ("OPTIMAL", "FEASIBLE"):
            rec["feasible"].append(d)
            if not ver: bugs.append(("verify_fail", n, d))
        elif name == "INFEASIBLE": rec["infeasible"].append(d)
        else: rec["unknown"].append((d, name))
    F = set(rec["feasible"]); S = {d for d in W if color_balanced(d)}
    rec["feasible_equals_C1to4"] = (F == S) and not rec["unknown"]
    rec["C4_violators_feasible"] = sorted(F - S)
    rec["C1to4_not_feasible"] = sorted(S - F)
    rec["feasible_canonical"] = sorted({canon(d) for d in F})
    rec["infeasible_canonical"] = sorted({canon(d) for d in rec["infeasible"]})
    out["small_n"][str(n)] = rec
out["time_after_small"] = time.time() - t0

# Part B: n=5
n = 5
W = weak_candidates(n)
canW = sorted({canon(d) for d in W})
canS = [d for d in canW if color_balanced(d)]
canU = [d for d in canW if not color_balanced(d)]
out["n5"]["num_raw_C1to3"] = len(W)
out["n5"]["num_canonical_C1to3"] = len(canW)
out["n5"]["num_canonical_C1to4"] = len(canS)
out["n5"]["num_canonical_C4_violators"] = len(canU)
cnt = {}
for d in canS: cnt[len(d)] = cnt.get(len(d), 0) + 1
out["n5"]["canonical_C1to4_by_c"] = cnt
priority = [d for d in canS if len(d) in (2, 4, 14, 16)]
rest = [d for d in canS if len(d) not in (2, 4, 14, 16)]
random.shuffle(rest)
neg = random.sample(canU, min(n_neg, len(canU)))
queue = [("pos", d) for d in priority] + [("neg", d) for d in neg] + [("pos", d) for d in rest]
res5 = {"pos_feasible": 0, "pos_infeasible": [], "pos_unknown": [], "neg_infeasible": 0, "neg_feasible": [], "neg_unknown": [], "tested_by_c_pos": {}, "priority_count": len(priority), "stopped_early": False}
examples = {}
for kind, d in queue:
    if time.time() - t0 > T:
        res5["stopped_early"] = True; break
    name, ver, cyc = solve(d, n, per)
    if kind == "pos":
        res5["tested_by_c_pos"][len(d)] = res5["tested_by_c_pos"].get(len(d), 0) + 1
        if name in ("OPTIMAL", "FEASIBLE"):
            res5["pos_feasible"] += 1
            if not ver: bugs.append(("verify_fail", 5, d))
            if len(d) not in examples: examples[len(d)] = {"delta": d, "cycle": cyc}
        elif name == "INFEASIBLE": res5["pos_infeasible"].append(d)
        else: res5["pos_unknown"].append((d, name))
    else:
        if name in ("OPTIMAL", "FEASIBLE"):
            res5["neg_feasible"].append(d)
            bugs.append(("C4_violator_feasible", 5, d, ver))
        elif name == "INFEASIBLE": res5["neg_infeasible"] += 1
        else: res5["neg_unknown"].append((d, name))
res5["priority_all_tested"] = sum(res5["tested_by_c_pos"].get(c, 0) for c in (2, 4, 14, 16)) >= len(priority)
out["n5"].update(res5)
out["n5"]["example_cycles"] = {str(k): v for k, v in examples.items()}
out["bugs"] = bugs
out["elapsed"] = time.time() - t0
sm = []
for k, r in out["small_n"].items():
    sm.append(f"n={k}: tested {r['tested']} raw C1-3 lists, feasible==C1-4: {r['feasible_equals_C1to4']}, C1-4 infeasible canon: {sorted({canon(d) for d in r['C1to4_not_feasible']})}")
sm.append(f"n=5: canonical C1-4 lists={len(canS)}; tested pos feasible={res5['pos_feasible']}, pos INFEASIBLE={len(res5['pos_infeasible'])}, pos UNKNOWN={len(res5['pos_unknown'])}; neg controls INFEASIBLE={res5['neg_infeasible']}, neg FEASIBLE={len(res5['neg_feasible'])}, neg UNKNOWN={len(res5['neg_unknown'])}; priority(c in 2,4,14,16) all tested={res5['priority_all_tested']}; stopped_early={res5['stopped_early']}; bugs={len(bugs)}")
out["summary"] = " | ".join(sm)
json.dump(out, open("result.json", "w"), indent=1, default=list)
print(out["summary"])
