# MathResearchLab experiment 3b0ebddf-94fa-4bd5-9d50-aa549a989bb2
# Recursive (coordinate-split) lower bound for Phi_m vs simplicial upper profile: Harper-free bounds on alpha_=(Q_n) for n<=13
# sha256(code) = ab76b37241b10bf4dec30d52a24963916d330134b25526fc282caa27dc7c6202
# parameters: {"M": 12, "seed_ms": [5, 6], "seed_budget": 60, "seed_tl": 3}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, math
import numpy as np

params = json.load(open(os.environ["MRL_PARAMS"]))
T0 = time.time()
M = params.get("M", 12)
SEED_MS = params.get("seed_ms", [5, 6])
SEED_BUDGET = params.get("seed_budget", 60)
def el():
    return time.time() - T0
def popc(x):
    return bin(x).count("1")
def closed(m, v):
    return [v] + [v ^ (1 << i) for i in range(m)]

def harper_profile(m):
    order = sorted(range(1 << m), key=lambda v: (popc(v), tuple(i for i in range(m) if v >> i & 1)))
    cov = bytearray(1 << m); size = 0; prof = [0]
    for v in order:
        for w in closed(m, v):
            if not cov[w]:
                cov[w] = 1; size += 1
        prof.append(size)
    return np.array(prof, dtype=np.int64)

def brute_phi(m):
    N = 1 << m
    masks = [sum(1 << w for w in closed(m, v)) for v in range(N)]
    nm = [0] * (1 << N); best = [N + 1] * (N + 1); best[0] = 0
    for S in range(1, 1 << N):
        low = S & -S; v = low.bit_length() - 1
        x = nm[S ^ low] | masks[v]; nm[S] = x
        c = popc(S); s = popc(x)
        if s < best[c]:
            best[c] = s
    return best

def cpsat_lower_bound(m, k, tl):
    from ortools.sat.python import cp_model
    N = 1 << m
    md = cp_model.CpModel()
    a = [md.NewBoolVar("") for _ in range(N)]
    y = [md.NewBoolVar("") for _ in range(N)]
    for v in range(N):
        cl = closed(m, v)
        for u in cl:
            md.AddImplication(a[u], y[v])
    md.Add(sum(a) == k)
    if k >= 1:
        md.Add(a[0] == 1)
        for i in range(m - 1):
            md.Add(a[1 << i] >= a[1 << (i + 1)])
        deg0 = sum(a[1 << i] for i in range(m))
        for v in range(1, N):
            md.Add(sum(a[v ^ (1 << i)] for i in range(m)) + m * a[v] <= deg0 + m)
    md.Minimize(sum(y))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl; s.parameters.num_workers = 8
    st = s.Solve(md)
    return s.StatusName(st), int(math.ceil(s.BestObjectiveBound() - 1e-9))

def recurse(prev, m):
    h = 1 << (m - 1)
    Lm = np.zeros(2 * h + 1, dtype=np.int64)
    for a in range(2 * h + 1):
        a0 = np.arange(max(0, a - h), min(a, h) + 1)
        a1 = a - a0
        vals = np.maximum(prev[a0], a1) + np.maximum(prev[a1], a0)
        Lm[a] = vals.min()
    return np.maximum.accumulate(Lm)

res = {"per_m": {}, "brute_checks": {}, "seeding": []}
L = {0: np.array([0, 1], dtype=np.int64)}
H = {0: np.array([0, 1], dtype=np.int64)}
brute = {m: brute_phi(m) for m in range(0, 5)}
seed_used = 0.0
for m in range(1, M + 1):
    L[m] = recurse(L[m - 1], m)
    H[m] = harper_profile(m)
    gaps = [int(k) for k in range(len(L[m])) if L[m][k] != H[m][k]]
    if gaps and m in SEED_MS:
        # strengthen with CP-SAT proven lower bounds (valid even if not optimal)
        crit = [k for k in gaps]
        # prioritise k near threshold
        Ht = (1 << m)
        kH = max(k for k in range(len(H[m])) if k + H[m][k] <= Ht)
        crit.sort(key=lambda k: abs(k - kH))
        for k in crit:
            if seed_used > SEED_BUDGET or el() > 100:
                break
            t0 = time.time()
            st, lb = cpsat_lower_bound(m, k, tl=params.get("seed_tl", 3))
            seed_used += time.time() - t0
            res["seeding"].append({"m": m, "k": k, "status": st, "lb": lb, "L_before": int(L[m][k]), "H": int(H[m][k])})
            if lb > L[m][k]:
                L[m][k] = lb
        L[m] = np.maximum.accumulate(L[m])
        gaps = [int(k) for k in range(len(L[m])) if L[m][k] != H[m][k]]
    if m <= 4:
        bf = brute[m]
        res["brute_checks"][m] = {"L_le_phi": bool(all(L[m][k] <= bf[k] for k in range(len(bf)))), "phi_le_H": bool(all(bf[k] <= H[m][k] for k in range(len(bf)))), "L_eq_phi": bool(all(L[m][k] == bf[k] for k in range(len(bf))))}
    Nm = 1 << m
    kU = max(k for k in range(Nm + 1) if k + L[m][k] <= Nm)
    kH = max(k for k in range(Nm + 1) if k + H[m][k] <= Nm)
    entry = {"n": m + 1, "kappa_H": int(kH), "kappa_U": int(kU), "alpha_lower": 2 * int(kH), "alpha_upper": 2 * int(kU),
             "exact": bool(kH == kU), "num_gap_k": len(gaps), "first_gaps": gaps[:20],
             "L_H_at_critical": {int(k): [int(L[m][k]), int(H[m][k])] for k in range(max(0, kH - 1), min(Nm, kH + 2) + 1)}}
    if gaps:
        entry["max_gap"] = int(max(H[m][k] - L[m][k] for k in gaps))
    if m <= 8:
        entry["L"] = [int(x) for x in L[m]]; entry["H"] = [int(x) for x in H[m]]
    res["per_m"][m] = entry

formula = {}
for m in range(1, M + 1):
    n = m + 1; s = (n - 1) // 2
    formula[n] = 2 ** (n - 1) - 2 ** (n - 1 - 2 * s) * math.comb(2 * s, s)
res["formula_values"] = formula
res["formula_matches_H"] = all(res["per_m"][m]["alpha_lower"] == formula[m + 1] for m in range(1, M + 1))
brute_ok = all(v["L_le_phi"] and v["phi_le_H"] for v in res["brute_checks"].values())
res["summary"] = (f"brute sanity (L<=Phi<=H, m<=4): {brute_ok}; " +
                   "; ".join(f"n={res['per_m'][m]['n']}: {res['per_m'][m]['alpha_lower']}..{res['per_m'][m]['alpha_upper']} gaps={res['per_m'][m]['num_gap_k']}" for m in range(1, M + 1)) +
                   f"; formula matches constructive lower bound: {res['formula_matches_H']}; seeding calls: {len(res['seeding'])}; elapsed {round(el(),1)}s")
json.dump(res, open("result.json", "w"))
print(res["summary"])
