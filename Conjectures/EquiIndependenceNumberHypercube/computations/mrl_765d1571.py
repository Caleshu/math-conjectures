# MathResearchLab experiment 765d1571-0c20-4a2e-bb92-a7527c45e5a9
# CP-SAT without Harper: infeasibility of |A|=45 with |N[A]|<=83 in Q_7 (alpha_=(Q_8)<90), witness for 44, exact Phi_5 and critical Phi_6
# sha256(code) = 9db032285e5a534b60510dbe65cfc513f527e1801b19453eed8ab23b88abd27f
# parameters: {"total_budget": 108, "workers": 8, "tl_k44": 12, "tl_k45": 55, "m6_ks": [22, 23]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, math
from ortools.sat.python import cp_model

params = json.load(open(os.environ["MRL_PARAMS"]))
T0 = time.time()
BUDGET = params.get("total_budget", 108)
W = params.get("workers", 8)
def el():
    return time.time() - T0

def nbrs(m, v):
    return [v ^ (1 << i) for i in range(m)]
def closed(m, v):
    return [v] + nbrs(m, v)
def nbhd_set(m, S):
    s = set()
    for v in S:
        s.update(closed(m, v))
    return s
def popc(x):
    return bin(x).count("1")

def simplicial_order(m):
    return sorted(range(1 << m), key=lambda v: (popc(v), tuple(i for i in range(m) if v >> i & 1)))

def harper_profile(m):
    cov = bytearray(1 << m); size = 0; prof = [0]
    for v in simplicial_order(m):
        for w in closed(m, v):
            if not cov[w]:
                cov[w] = 1; size += 1
        prof.append(size)
    return prof

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

def solve_phi(m, k, cap=None, minimize=True, symbreak=True, tl=10.0, hint=None):
    N = 1 << m
    md = cp_model.CpModel()
    a = [md.NewBoolVar(f"a{v}") for v in range(N)]
    y = [md.NewBoolVar(f"y{v}") for v in range(N)]
    for v in range(N):
        cl = closed(m, v)
        for u in cl:
            md.AddImplication(a[u], y[v])
        md.AddBoolOr([a[u] for u in cl] + [y[v].Not()])  # y_v = OR_{u in N[v]} a_u
    md.Add(sum(a) == k)
    if cap is not None:
        md.Add(sum(y) <= cap)
    if symbreak and k >= 1:
        # translate a max-A-degree vertex of A to 0, then permute coords: weight-1 members of A form a prefix
        md.Add(a[0] == 1)
        for i in range(m - 1):
            md.Add(a[1 << i] >= a[1 << (i + 1)])
        deg0 = sum(a[1 << i] for i in range(m))
        for v in range(1, N):
            md.Add(sum(a[u] for u in nbrs(m, v)) + m * a[v] <= deg0 + m)
    if minimize:
        md.Minimize(sum(y))
    if hint is not None:
        hs = set(hint)
        for v in range(N):
            md.AddHint(a[v], 1 if v in hs else 0)
    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = max(0.5, tl)
    sol.parameters.num_workers = W
    st = sol.Solve(md)
    res = {"m": m, "k": k, "cap": cap, "symbreak": symbreak, "status": sol.StatusName(st), "wall": round(sol.WallTime(), 2)}
    if minimize:
        res["bound"] = sol.BestObjectiveBound()
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        A = [v for v in range(N) if sol.Value(a[v])]
        NA = nbhd_set(m, A)
        res["A"] = A
        res["size_ok"] = (len(A) == k)
        res["nbhd_verified"] = len(NA)
        if minimize:
            res["obj"] = int(round(sol.ObjectiveValue()))
            res["obj_matches_verified"] = (res["obj"] == len(NA))
        if cap is not None:
            res["cap_ok"] = len(NA) <= cap
    return res

def verify_lift(m, A, k):
    """Given A in Q_m with |N[A]|<=2^m-k, build balanced independent set in Q_{m+1} of size 2k and check directly."""
    NA = nbhd_set(m, A)
    comp = [w for w in range(1 << m) if w not in NA]
    if len(A) != k or len(comp) < k:
        return {"ok": False, "reason": "sizes"}
    B = comp[:k]
    par = lambda x: popc(x) & 1
    E = [u | (par(u) << m) for u in A]
    O = [w | ((1 - par(w)) << m) for w in B]
    n = m + 1
    S = set(E) | set(O)
    ok = len(S) == 2 * k and all(popc(x) % 2 == 0 for x in E) and all(popc(x) % 2 == 1 for x in O)
    for x in S:
        for i in range(n):
            if (x ^ (1 << i)) in S:
                ok = False
    return {"ok": ok, "n": n, "size": len(S), "even": len(E), "odd": len(O), "even_vertices": sorted(E), "odd_vertices": sorted(O)}

out = {"sanity": {}, "main": {}}

# ---------- Sanity: m=3,4 brute force vs CP-SAT (with and without symmetry breaking) vs Harper profile ----------
sanity_ok = True
for m in (3, 4):
    bf = brute_phi(m); hp = harper_profile(m)
    cs, cn = [], []
    for k in range(0, (1 << m) + 1):
        r1 = solve_phi(m, k, symbreak=True, tl=5)
        r2 = solve_phi(m, k, symbreak=False, tl=5)
        cs.append(r1.get("obj")); cn.append(r2.get("obj"))
        if r1["status"] != "OPTIMAL" or r2["status"] != "OPTIMAL" or not r1.get("obj_matches_verified") or not r2.get("obj_matches_verified"):
            sanity_ok = False
    ok_m = (cs == bf) and (cn == bf) and (hp == bf)
    sanity_ok = sanity_ok and ok_m
    out["sanity"][f"m{m}"] = {"brute": bf, "cpsat_symbreak": cs, "cpsat_plain": cn, "harper": hp, "all_equal": ok_m}
out["sanity"]["ok"] = sanity_ok

# ---------- Explicit Harper set I_44 in Q_7 (unconditional lower bound for n=8) ----------
m = 7
order7 = simplicial_order(7)
I44 = order7[:44]
out["main"]["harper_I44_Q7"] = {"nbhd": len(nbhd_set(7, I44)), "lift": {kk: vv for kk, vv in verify_lift(7, I44, 44).items() if kk in ("ok", "n", "size", "even", "odd")}}
hp7 = harper_profile(7)
out["main"]["harper_profile_Q7_k40_50"] = {k: hp7[k] for k in range(40, 51)}

# ---------- m=7, k=44 feasibility (no hint) ----------
r44 = solve_phi(7, 44, cap=84, minimize=False, symbreak=True, tl=params.get("tl_k44", 12))
if "A" in r44:
    lift = verify_lift(7, r44["A"], 44)
    r44["lift_Q8"] = lift
out["main"]["Q7_k44_cap84"] = r44

# ---------- m=7, k=45 infeasibility ----------
tl45 = min(params.get("tl_k45", 55), BUDGET - el() - 25)
r45 = solve_phi(7, 45, cap=83, minimize=False, symbreak=True, tl=tl45)
if "A" in r45:
    r45["lift_Q8"] = {kk: vv for kk, vv in verify_lift(7, r45["A"], 45).items() if kk in ("ok", "size")}
out["main"]["Q7_k45_cap83"] = r45

# ---------- m=6 critical k ----------
hp6 = harper_profile(6)
out["main"]["Q6_critical"] = []
for k in params.get("m6_ks", [22, 23]):
    if el() > BUDGET - 12:
        break
    r = solve_phi(6, k, symbreak=True, tl=min(8, BUDGET - el() - 10))
    r.pop("A", None)
    r["harper"] = hp6[k]; r["pair_feasible_if_exact"] = (k + r.get("obj", 10**9) <= 64)
    out["main"]["Q6_critical"].append(r)

# ---------- m=5 full profile ----------
hp5 = harper_profile(5)
prof5 = []
for k in range(0, 33):
    if el() > BUDGET - 3:
        prof5.append({"k": k, "status": "SKIPPED"}); continue
    r = solve_phi(5, k, symbreak=True, tl=min(2.0, BUDGET - el() - 2))
    prof5.append({"k": k, "status": r["status"], "obj": r.get("obj"), "bound": r.get("bound"), "harper": hp5[k], "verified": r.get("obj_matches_verified")})
all_opt5 = all(p["status"] == "OPTIMAL" for p in prof5)
match5 = all(p.get("obj") == p["harper"] for p in prof5 if p["status"] == "OPTIMAL")
kappa5 = max(k for k in range(33) if prof5[k].get("obj") is not None and k + prof5[k]["obj"] <= 32) if all_opt5 else None
out["main"]["Q5_profile"] = {"entries": prof5, "all_optimal": all_opt5, "matches_harper_where_optimal": match5, "kappa5": kappa5, "alpha_eq_Q6": (2 * kappa5 if kappa5 is not None else None)}

r44s = out["main"]["Q7_k44_cap84"]
summary = (f"sanity_ok={sanity_ok}; Q7 k=44 cap84: {r44s['status']} lift_ok={r44s.get('lift_Q8',{}).get('ok')}; "
           f"Q7 k=45 cap83: {r45['status']} (wall {r45['wall']}s); Harper I44 nbhd={out['main']['harper_I44_Q7']['nbhd']}; "
           f"Q6 critical: {[(r['k'], r['status'], r.get('obj'), r.get('bound'), r['harper']) for r in out['main']['Q6_critical']]}; "
           f"Q5 profile all_optimal={all_opt5} matches_harper={match5} kappa5={kappa5}; elapsed={round(el(),1)}s")
out["summary"] = summary
# trim large lists
if "A" in out["main"]["Q7_k44_cap84"]:
    pass
json.dump(out, open("result.json", "w"))
print(summary)
