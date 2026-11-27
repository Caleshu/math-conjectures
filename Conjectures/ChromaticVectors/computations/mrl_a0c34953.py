# MathResearchLab experiment a0c34953-6e59-47af-863d-c59cae983d56
# Exact chromatic-vector images for n<=4 (enumeration) and n=4,5 (CP-SAT), tested against the projection condition (P)/(P+)
# sha256(code) = 9f0bde64e81c032be1b980992e96cb3417964a012650232274c690e1ebe35072
# parameters: {"n_enum_max": 4, "sat_ns": [4, 5], "per_instance_time": 10.0, "budget": 100.0, "workers": 8}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, itertools
from ortools.sat.python import cp_model

params = json.load(open(os.environ["MRL_PARAMS"]))
N_ENUM_MAX = int(params.get("n_enum_max", 4))
SAT_NS = list(params.get("sat_ns", [4, 5]))
TL = float(params.get("per_instance_time", 10.0))
BUDGET = float(params.get("budget", 100.0))
WORKERS = int(params.get("workers", 8))
T0 = time.time()

def enum_images(n):
    N = 1 << n
    vis = [False]*N; vis[0] = True
    cnt = [0]*n
    image = {}
    ncyc = [0]
    def dfs(v, depth):
        if depth == N:
            x = v  # closing edge v -> 0
            if x and (x & (x-1)) == 0:
                i = x.bit_length()-1
                cnt[i] += 1
                key = tuple(sorted(cnt))
                image[key] = image.get(key, 0) + 1
                ncyc[0] += 1
                cnt[i] -= 1
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
    half = 1 << (n-1)
    cap = max(1, 1 << (n-2))
    res = []
    def rec(remaining, k, minpart, cur):
        if k == 0:
            if remaining == 0:
                res.append(tuple(2*x for x in cur))
            return
        for p in range(minpart, min(cap, remaining)+1):
            if p*k > remaining:
                break
            rec(remaining-p, k-1, p, cur+[p])
    rec(half, n, 1, [])
    return res

def subset_ok(c):
    s = sorted(c); acc = 0
    for k in range(1, len(s)+1):
        acc += s[k-1]
        if acc < (1 << k):
            return False
    return acc == (1 << len(s))

def recursive_ok(c, images):
    n = len(c)
    for k in range(2, n):
        for S in itertools.combinations(range(n), k):
            sub = tuple(sorted(c[i] for i in S))
            if sum(sub) == (1 << k):
                if k not in images:
                    return None
                if sub not in images[k]:
                    return False
    return True

def check_cycle(n, succ):
    N = 1 << n
    if len(succ) != N:
        return False, None
    cnt = [0]*n; v = 0; seen = set()
    for _ in range(N):
        if v in seen:
            return False, None
        seen.add(v)
        u = succ[v]; x = u ^ v
        if x == 0 or (x & (x-1)):
            return False, None
        cnt[x.bit_length()-1] += 1
        v = u
    return (v == 0 and len(seen) == N), cnt

def solve(n, c, tl, constrain=True):
    N = 1 << n
    m = cp_model.CpModel()
    arcs = []; lits = {}
    dimlits = [[] for _ in range(n)]
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i)
            b = m.NewBoolVar(f"a_{v}_{u}")
            arcs.append((v, u, b)); lits[(v, u)] = b; dimlits[i].append(b)
    m.AddCircuit(arcs)
    if constrain:
        for i in range(n):
            m.Add(sum(dimlits[i]) == c[i])
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_search_workers = WORKERS
    st = s.Solve(m)
    out = {"status": s.StatusName(st), "wall": round(s.WallTime(), 3)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {}; ntrue = 0
        for (v, u), b in lits.items():
            if s.Value(b):
                succ[v] = u; ntrue += 1
        ok, vec = check_cycle(n, succ)
        ok = ok and ntrue == N
        if constrain:
            ok = ok and vec == list(c)
        out["verified"] = ok; out["vector"] = vec
        out["cycle_from_0"] = None
        if ok and n <= 5:
            seq = [0]; v = 0
            for _ in range(N-1):
                v = succ[v]; seq.append(v)
            out["cycle_from_0"] = seq
    return out

res = {"enumeration": {}, "cpsat": {}, "sanity": {}}
images = {}
for n in range(2, N_ENUM_MAX+1):
    t = time.time()
    ncyc, image = enum_images(n)
    res["enumeration"][str(n)] = {"directed_cycles_through_0": ncyc,
        "undirected_cycles": ncyc//2,
        "image_sorted_with_directed_counts": {str(list(k)): v for k, v in sorted(image.items())},
        "seconds": round(time.time()-t, 2)}
    images[n] = set(image.keys())
known = {2: 1, 3: 6, 4: 1344}
res["sanity"]["enum_counts_match_known_(1,6,1344)"] = all(
    res["enumeration"][str(n)]["undirected_cycles"] == known[n] for n in range(2, N_ENUM_MAX+1) if n in known)

# unconstrained sanity solve
san = solve(5, None, TL, constrain=False)
res["sanity"]["unconstrained_Q5_circuit"] = {"status": san["status"], "verified": san.get("verified"), "vector": san.get("vector")}

for n in SAT_NS:
    rows = []
    for c in candidates(n):
        row = {"c": list(c), "P_subset_ok": subset_ok(c), "Pplus_recursive_ok": recursive_ok(c, images) if subset_ok(c) else False}
        if time.time()-T0 > BUDGET:
            row["status"] = "NOT_RUN_BUDGET"
        else:
            out = solve(n, c, TL)
            row.update({k: out[k] for k in out if k != "cycle_from_0"})
            if out.get("cycle_from_0") is not None:
                row["witness_cycle_from_0"] = out["cycle_from_0"]
        rows.append(row)
    feas = [tuple(r["c"]) for r in rows if r.get("status") in ("OPTIMAL", "FEASIBLE") and r.get("verified")]
    infeas = [tuple(r["c"]) for r in rows if r.get("status") == "INFEASIBLE"]
    unknown = [r["c"] for r in rows if r.get("status") not in ("OPTIMAL", "FEASIBLE", "INFEASIBLE")]
    unverified = [r["c"] for r in rows if r.get("status") in ("OPTIMAL", "FEASIBLE") and not r.get("verified")]
    entry = {"num_candidates_basic_conditions": len(rows), "rows": rows,
             "feasible": [list(x) for x in feas], "infeasible": [list(x) for x in infeas],
             "unknown_or_not_run": unknown, "feasible_but_unverified_BUG": unverified,
             "feasible_but_violates_P_BUG": [r["c"] for r in rows if tuple(r["c"]) in feas and not r["P_subset_ok"]],
             "infeasible_though_Pplus_holds": [r["c"] for r in rows if tuple(r["c"]) in infeas and r["Pplus_recursive_ok"]],
             "infeasible_though_P_holds": [r["c"] for r in rows if tuple(r["c"]) in infeas and r["P_subset_ok"]]}
    if n in images:
        entry["cpsat_matches_enumeration"] = (set(feas) == images[n] and len(unknown) == 0)
    else:
        if len(unknown) == 0:
            images[n] = set(feas)
    res["cpsat"][str(n)] = entry

lines = []
lines.append("enum counts ok: %s" % res["sanity"]["enum_counts_match_known_(1,6,1344)"])
lines.append("unconstrained Q5: %s" % san["status"])
for n in range(2, N_ENUM_MAX+1):
    lines.append("Q%d image: %s" % (n, sorted(images[n])))
for n in SAT_NS:
    e = res["cpsat"][str(n)]
    lines.append("n=%d: %d candidates, feasible=%s, infeasible=%s, unknown=%s, infeasible_though_P=%s, infeasible_though_P+=%s, BUGS=%s/%s, match_enum=%s" % (
        n, e["num_candidates_basic_conditions"], e["feasible"], e["infeasible"], e["unknown_or_not_run"],
        e["infeasible_though_P_holds"], e["infeasible_though_Pplus_holds"], e["feasible_but_unverified_BUG"], e["feasible_but_violates_P_BUG"], e.get("cpsat_matches_enumeration")))
res["elapsed"] = round(time.time()-T0, 2)
res["summary"] = " | ".join(lines)
json.dump(res, open("result.json", "w"), indent=1)
print(res["summary"])
