# MathResearchLab experiment 28275ee0-1b98-4de4-8adc-ab330722f284
# CP-SAT: which balanced parity vectors are realizable in Q_5 (and cross-check on Q_4)
# sha256(code) = 6229eb1f33de27eddf4e21a5fdec3a37ee3db67dc44748b961cee46f32065389
# parameters: {"ns": [4, 5], "budget_s": 100, "per_solve_s": 4.0, "infeasible_checks_per_k": 2}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from itertools import combinations
from ortools.sat.python import cp_model
params = json.load(open(os.environ["MRL_PARAMS"]))
NS = params.get("ns", [4, 5])
BUDGET = params.get("budget_s", 100)
TL = params.get("per_solve_s", 4.0)
NINF = params.get("infeasible_checks_per_k", 2)
T0 = time.time()

def popc(x): return bin(x).count("1")
def par_in(u, i): return popc(u & ~(1 << i)) & 1
s = lambda v: "".join(map(str, v))

def conds(v, n):
    k = len(v)
    s0 = [0, 0]; s1 = [0, 0]; df = [0, 0]
    for m in range(k):
        sd = m % 2
        a, b = v[m-1], v[m]
        if a == b:
            (s0 if b == 0 else s1)[sd] += 1
        else:
            df[sd] += 1
    A = (sum(v) * 2 == k)
    B = all(s0[x] == s1[x] for x in (0, 1))
    C = all(3*(s0[x]+s1[x]) + 2*df[x] <= (1 << (n-1)) for x in (0, 1))
    return A, B, C

def canonical(v):
    k = len(v); c = []
    for w in (list(v), [1-x for x in v]):
        for r in range(0, k, 2):
            c.append(tuple(w[r:] + w[:r]))
    return min(c)

def balanced_classes(k):
    cl = set()
    for ones in combinations(range(k), k//2):
        v = [0]*k
        for o in ones: v[o] = 1
        cl.add(canonical(v))
    return sorted(cl)

def beta(hp, i):
    N = len(hp)
    assert hp[0] ^ hp[1] == (1 << i) and (hp[0] >> i) & 1 == 0
    js = [l for l in range(N) if hp[l] ^ hp[(l+1) % N] == (1 << i)]
    b = [par_in(hp[0], i)]
    for t in range(1, len(js)):
        b.append((b[-1] + js[t] - js[t-1] + 1) % 2)
    return tuple(b)

def solve(v, n, i, tl):
    N = 1 << n; k = len(v)
    M = cp_model.CpModel()
    X = {}
    for u in range(N):
        for d in range(n):
            X[(u, u ^ (1 << d))] = M.NewBoolVar(f"x{u}_{d}")
    M.AddCircuit([(u, w, x) for (u, w), x in X.items()])
    S = {}
    for u in range(N):
        side = (u >> i) & 1
        S[u] = M.NewIntVarFromDomain(cp_model.Domain.FromValues([t for t in range(k) if t % 2 == side]), f"s{u}")
    I = []
    for (u, w), x in X.items():
        if u ^ w == (1 << i):
            I.append(x)
            M.AddLinearExpressionInDomain(S[w] - S[u], cp_model.Domain.FromValues(sorted({1, 1-k}))).OnlyEnforceIf(x)
            side = (u >> i) & 1
            allowed = [t for t in range(k) if t % 2 == side and v[t] == par_in(u, i)]
            if allowed:
                M.AddLinearExpressionInDomain(S[u], cp_model.Domain.FromValues(allowed)).OnlyEnforceIf(x)
            else:
                M.Add(x == 0)
        else:
            M.Add(S[w] == S[u]).OnlyEnforceIf(x)
    M.Add(sum(I) == k)
    j = 0 if i != 0 else 1
    root = 0 if v[0] == 0 else (1 << j)
    M.Add(X[(root, root ^ (1 << i))] == 1)
    M.Add(S[root] == 0)
    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = tl
    sol.parameters.num_workers = 8
    st = sol.Solve(M)
    name = sol.StatusName(st)
    verified = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {u: w for (u, w), x in X.items() if sol.Value(x)}
        h = [root]
        for _ in range(N-1): h.append(succ[h[-1]])
        ok = len(set(h)) == N and all(popc(h[t] ^ h[(t+1) % N]) == 1 for t in range(N))
        ok = ok and succ[h[-1]] == root and h[1] == root ^ (1 << i)
        verified = bool(ok and beta(h, i) == tuple(v))
    return name, verified

def ham_cycles(n):
    N = 1 << n; res = []; path = [0]; vis = [False]*N; vis[0] = True
    def dfs(u):
        if len(path) == N:
            if popc(u) == 1 and path[1] < path[-1]: res.append(list(path))
            return
        for d in range(n):
            w = u ^ (1 << d)
            if not vis[w]:
                vis[w] = True; path.append(w); dfs(w); path.pop(); vis[w] = False
    dfs(0); return res

def exhaustive_classes(n):
    N = 1 << n; ach = set()
    for h in ham_cycles(n):
        for i in range(n):
            for l in range(N):
                a, b = h[l], h[(l+1) % N]
                if a ^ b == (1 << i):
                    hp = [h[(l+t) % N] for t in range(N)] if (a >> i) & 1 == 0 else [h[(l+1-t) % N] for t in range(N)]
                    ach.add(canonical(list(beta(hp, i))))
    return ach

out = {"sanity": {}, "per_n": {}}
partial = False
# sanity checks on n=5
alt = [t % 2 for t in range(16)]
out["sanity"]["n5_k16_alternating"] = solve(alt, 5, 4, 10.0)
block = [0]*8 + [1]*8
out["sanity"]["n5_k16_0^8_1^8_conds"] = conds(block, 5)
out["sanity"]["n5_k16_0^8_1^8_cpsat"] = solve(block, 5, 4, 10.0)
out["sanity"]["n3_k4_0011"] = solve([0, 0, 1, 1], 3, 2, 5.0)
out["sanity"]["n3_k2_01"] = solve([0, 1], 3, 2, 5.0)

for n in NS:
    i = n - 1
    exh = exhaustive_classes(n) if n <= 4 else None
    per_k = {}
    for k in range(2, (1 << (n-1)) + 1, 2):
        recs = []; ninf = 0
        for v in balanced_classes(k):
            A, B, C = conds(v, n)
            rec = {"v": s(v), "A": A, "B": B, "C": C}
            if exh is not None: rec["exhaustive_achieved"] = v in exh
            run = (B and C) or (n <= 4) or (ninf < NINF)
            if run:
                if time.time() - T0 > BUDGET - TL - 2:
                    partial = True; rec["cpsat"] = "SKIPPED_BUDGET"
                else:
                    if not (B and C) and n > 4: ninf += 1
                    st, ver = solve(list(v), n, i, TL)
                    rec["cpsat"] = st; rec["verified"] = ver
            recs.append(rec)
        summ = {
            "num_classes": len(recs),
            "num_ABC": sum(r["B"] and r["C"] for r in recs),
            "ABC_feasible": sum(1 for r in recs if r["B"] and r["C"] and r.get("cpsat") in ("OPTIMAL", "FEASIBLE")),
            "ABC_infeasible": [r["v"] for r in recs if r["B"] and r["C"] and r.get("cpsat") == "INFEASIBLE"],
            "ABC_unknown_or_skipped": [r["v"] for r in recs if r["B"] and r["C"] and r.get("cpsat") in ("UNKNOWN", "SKIPPED_BUDGET")],
            "nonABC_feasible": [r["v"] for r in recs if not (r["B"] and r["C"]) and r.get("cpsat") in ("OPTIMAL", "FEASIBLE")],
            "nonABC_statuses": [(r["v"], r.get("cpsat")) for r in recs if not (r["B"] and r["C"]) and "cpsat" in r][:10],
            "all_feasible_verified": all(r.get("verified") for r in recs if r.get("cpsat") in ("OPTIMAL", "FEASIBLE")),
            "num_balanced_classes_not_realizable_proved": sum(1 for r in recs if not (r["B"] and r["C"])) ,
        }
        if exh is not None:
            summ["cpsat_matches_exhaustive"] = all(((r.get("cpsat") in ("OPTIMAL", "FEASIBLE")) == r["exhaustive_achieved"]) and r.get("cpsat") != "UNKNOWN" for r in recs)
            summ["ABC_matches_exhaustive"] = all((r["B"] and r["C"]) == r["exhaustive_achieved"] for r in recs)
        per_k[k] = {"summary": summ, "records": recs if len(recs) <= 150 else recs[:150]}
    out["per_n"][n] = per_k

parts = []
for n, pk in out["per_n"].items():
    for k, d in pk.items():
        sm = d["summary"]
        parts.append(f"n={n},k={k}: classes={sm['num_classes']} ABC={sm['num_ABC']} ABCfeas={sm['ABC_feasible']} ABCinf={len(sm['ABC_infeasible'])} ABCunk={len(sm['ABC_unknown_or_skipped'])} nonABCfeas={len(sm['nonABC_feasible'])}" + (f" exhMatch={sm.get('cpsat_matches_exhaustive')}/{sm.get('ABC_matches_exhaustive')}" if 'cpsat_matches_exhaustive' in sm else ""))
summary = f"sanity={out['sanity']} | " + " | ".join(parts) + f" | partial={partial} time={time.time()-T0:.1f}s"
out["summary"] = summary; out["partial"] = partial
json.dump(out, open("result.json", "w"), indent=1)
print(summary)
