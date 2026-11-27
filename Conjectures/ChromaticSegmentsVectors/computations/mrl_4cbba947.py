# MathResearchLab experiment 4cbba947-eff5-4172-a93d-cf3f39b225ae
# Exact DFS certification of n=5 obstructions: validation, full-dihedral classes, explicit witnesses, c=14 table, c=12 sweep
# sha256(code) = e839059f5603afb4c935d4b4b1bfbe60ea42b1b51a4c824bc5c99d04037bae01
# parameters: {"time_limit": 106, "phase_ends": {"pass1": 68, "pass2": 84, "sym1": 97, "sym0": 105}, "sweep_c": [14, 16, 12], "neg_controls_c": [14], "budget1": 150000, "explicit": [[3, 2, 3, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]], "sym0_recheck_c": [14], "sym0_lists": [], "compute_old": true, "table_c": [14], "examples": [[2, 2, 2, 2, 2, 2, 3, 2, 3, 2, 2, 2, 2, 4], [2, 2, 3, 2, 3, 2, 2, 3, 2, 2, 4, 5]]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from itertools import combinations

params = json.load(open(os.environ["MRL_PARAMS"]))
T0 = time.time()
TL = float(params.get("time_limit", 105))
PH = params.get("phase_ends", {"pass1": 70, "pass2": 85, "sym1": 97, "sym0": 105})
SWEEP_C = params.get("sweep_c", [14, 16, 12])
NEG_C = params.get("neg_controls_c", [14])
BUDGET1 = int(params.get("budget1", 150000))
EXPLICIT = [tuple(x) for x in params.get("explicit", [])]
SYM0_C = params.get("sym0_recheck_c", [14])
SYM0_LISTS = [tuple(x) for x in params.get("sym0_lists", [])]
COMPUTE_OLD = params.get("compute_old", True)
TABLE_C = params.get("table_c", [14])
EXAMPLES = [tuple(x) for x in params.get("examples", [])]

def now():
    return time.time() - T0

class Budget(Exception):
    pass

def compositions(total, parts, minv=2):
    ex = total - minv * parts
    if ex < 0:
        return
    slots = ex + parts - 1
    for cuts in combinations(range(slots), parts - 1):
        res = []; prev = -1
        for cp in cuts:
            res.append(cp - prev - 1 + minv); prev = cp
        res.append(slots - prev - 1 + minv)
        yield tuple(res)

def raw_lists(n, c):
    N = 2 ** (n - 1)
    for E in compositions(N, c // 2):
        for O in compositions(N, c // 2):
            yield tuple(x for pr in zip(E, O) for x in pr)

def c4(d):
    j = 0; cnt = 0
    for k, x in enumerate(d):
        if (j + k) % 2 == 0:
            cnt += 1
        j += x
    return 2 * cnt == len(d)

def rev(d):
    return (d[0],) + tuple(reversed(d[1:]))

def orbit_full(d):
    c = len(d); o = set()
    for s in (d, rev(d)):
        for k in range(c):
            o.add(s[k:] + s[:k])
    return o

def orbit_old(d):
    c = len(d); o = set()
    for s in (d, rev(d)):
        for k in range(0, c, 2):
            o.add(s[k:] + s[:k])
    return o

class Solver:
    def __init__(self, m):
        self.m = m; V = 1 << m; self.V = V; self.FULL = (1 << V) - 1
        self.C = sum(1 << u for u in range(V) if bin(u).count("1") % 2 == 0)
        self.nbr = [tuple(u ^ (1 << j) for j in range(m)) for u in range(V)]
        self.dm = []
        for j in range(m):
            M = sum(1 << u for u in range(V) if not (u >> j) & 1)
            self.dm.append((M, 1 << j))

    def run(self, d, sym, count_mode=False, budget=None, deadline=None, memo_cap=1000000):
        V = self.V; FULL = self.FULL; C = self.C; nbr = self.nbr; dm = self.dm
        c = len(d)
        assert sum(d) == 2 * V and c % 2 == 0 and min(d) >= 2
        half = []; start = []; rem = []; seg = []
        for k, x in enumerate(d):
            for t in range(x):
                half.append(k & 1); start.append(t == 0); rem.append(x - 1 - t); seg.append(k)
        P = len(half)
        fut = [[0] * P, [0] * P]
        for p in range(P):
            for k in range(seg[p] + 1, c):
                if d[k] & 1:
                    fut[k & 1][p] += 1
        lastseg = c - 1
        path = [0] * P
        sol = [None]
        cnt = [0]
        memo = {}

        def nb(U):
            r = 0
            for M, s in dm:
                r |= ((U & M) << s) | ((U >> s) & M)
            return r

        def ok(p, tip, u0, u1, v0):
            hp = half[p]; r = rem[p]
            for b in (0, 1):
                U = FULL & ~(u1 if b else u0)
                act = (hp == b and r > 0)
                if U:
                    ext = (U | (1 << tip)) if act else U
                    if U & ~nb(ext):
                        return False
                diff = 2 * (U & C).bit_count() - U.bit_count()
                if act and (r & 1):
                    if (C >> tip) & 1:
                        diff += 1
                    else:
                        diff -= 1
                f = fut[b][p]
                if diff > f or diff < -f or ((diff - f) & 1):
                    return False
            if seg[p] == lastseg and r > 0:
                dist = (tip ^ v0).bit_count()
                if dist > r or ((r - dist) & 1):
                    return False
            return True

        def rec(p, tip, u0, u1, v0):
            if p == P - 1:
                if sol[0] is None:
                    sol[0] = path[:]
                return 1
            cnt[0] += 1
            if budget is not None and cnt[0] > budget:
                raise Budget()
            if deadline is not None and (cnt[0] & 2047) == 0 and time.time() > deadline:
                raise Budget()
            key = (((p * V + tip) << (2 * V)) | (u0 << V) | u1)
            g = memo.get(key)
            if g is not None:
                return g
            q = p + 1; b = half[q]; total = 0
            cands = (tip,) if start[q] else nbr[tip]
            for w in cands:
                if sym == 2 and q == 1 and w != 1:
                    continue
                bit = 1 << w
                if b == 0:
                    if u0 & bit:
                        continue
                    nu0 = u0 | bit; nu1 = u1
                else:
                    if u1 & bit:
                        continue
                    if q == P - 1:
                        if w != v0:
                            continue
                    elif w == v0:
                        continue
                    nu0 = u0; nu1 = u1 | bit
                if not ok(q, w, nu0, nu1, v0):
                    continue
                path[q] = w
                res = rec(q, w, nu0, nu1, v0)
                if res:
                    if not count_mode:
                        return res
                    total += res
            if len(memo) < memo_cap:
                memo[key] = total
            return total

        total = 0
        v0s = range(V) if sym == 0 else (0,)
        try:
            for v0 in v0s:
                memo.clear()
                u0 = 1 << v0
                path[0] = v0
                if not ok(0, v0, u0, 0, v0):
                    continue
                res = rec(0, v0, u0, 0, v0)
                if res:
                    total += res
                    if not count_mode:
                        break
        except Budget:
            return {"status": "UNKNOWN", "nodes": cnt[0]}
        if count_mode:
            return {"status": "COUNTED", "count": total, "nodes": cnt[0]}
        if total:
            return {"status": "FEASIBLE", "path": sol[0], "nodes": cnt[0]}
        return {"status": "INFEASIBLE", "nodes": cnt[0]}

def verify(d, path, m):
    n = m + 1; L = 2 ** n
    seq = []; p = 0
    for k, x in enumerate(d):
        for t in range(x):
            seq.append(path[p] | (((k + 1) & 1) << m)); p += 1
    h = [seq[-1]] + seq[:-1]
    if len(h) != L or len(set(h)) != L:
        return False, None
    for t in range(L):
        x = h[t] ^ h[(t + 1) % L]
        if x == 0 or (x & (x - 1)):
            return False, None
    if (h[0] >> m) & 1:
        return False, None
    lam = [t for t in range(L) if (h[t] ^ h[(t + 1) % L]) == (1 << m)]
    if not lam or lam[0] != 0:
        return False, None
    delta = [lam[k + 1] - lam[k] for k in range(len(lam) - 1)] + [L - lam[-1]]
    return tuple(delta) == tuple(d), h

out = {}
bugs = []

def save(summary):
    out["summary"] = summary
    out["elapsed"] = round(now(), 2)
    with open("result.json", "w") as f:
        json.dump(out, f, default=str)

# ---------------- validation n=2,3,4 ----------------
NCYC = {2: 1, 3: 6, 4: 1344}
validation = {}
for n in (2, 3, 4):
    m = n - 1; S = Solver(m); N = 2 ** m
    W = [d for c in range(2, N + 1, 2) for d in raw_lists(n, c)]
    tot = [0, 0, 0]; rel_ok = True; agree = True; wit_ok = True
    R = set()
    for d in W:
        cs = [S.run(d, s, count_mode=True)["count"] for s in (0, 1, 2)]
        for s in range(3):
            tot[s] += cs[s]
        if cs[0] != N * cs[1] or cs[1] != m * cs[2]:
            rel_ok = False
        for s in (0, 1, 2):
            r = S.run(d, s)
            f = r["status"] == "FEASIBLE"
            if f != (cs[0] > 0):
                agree = False
            if f:
                okv, _ = verify(d, r["path"], m)
                if not okv:
                    wit_ok = False
        if cs[0] > 0:
            R.add(d)
    exp = NCYC[n] * 2 ** n // n
    S4 = {d for d in W if c4(d)}
    v = {"raw_C1_3": len(W), "raw_C1_4": len(S4), "raw_realized": len(R),
         "total_count_sym0": tot[0], "expected_sym0": exp,
         "total_sym1": tot[1], "total_sym2": tot[2],
         "count_matches": tot[0] == exp, "per_list_sym_relations_ok": rel_ok,
         "feasibility_agrees_with_counts": agree, "witnesses_verified": wit_ok,
         "realized_subset_C1_4": R <= S4,
         "realized_classes": sorted({min(orbit_full(d)) for d in R}),
         "C1_4_unrealized_classes": sorted({min(orbit_full(d)) for d in S4 - R})}
    if n == 4:
        v["R_equals_S4_minus_orbit_223234"] = (R == S4 - orbit_full((2, 2, 3, 2, 3, 4)))
    else:
        v["R_equals_S"] = (R == S4)
    validation[n] = v
out["validation"] = validation
val_ok = all(validation[n]["count_matches"] and validation[n]["per_list_sym_relations_ok"] and validation[n]["feasibility_agrees_with_counts"] and validation[n]["witnesses_verified"] for n in (2, 3, 4)) and validation[4]["R_equals_S4_minus_orbit_223234"]
out["validation_all_ok"] = val_ok
out["t_after_validation"] = round(now(), 2)
save("partial: validation done")

# ---------------- n=5 class enumeration ----------------
n = 5; m = 4; S = Solver(m)
classes = {}
enum_stats = {}
c4_invariant_all = True
total_old = 0
for c in range(2, 17, 2):
    seen = set(); lst = []
    nraw = 0; nraw4 = 0
    for d in raw_lists(n, c):
        nraw += 1
        if c4(d):
            nraw4 += 1
        if d in seen:
            continue
        orb = orbit_full(d); seen |= orb
        vals = {c4(x) for x in orb}
        if len(vals) != 1:
            c4_invariant_all = False
        rep = min(orb)
        info = {"rep": rep, "c4": c4(rep), "orbit_size": len(orb)}
        if COMPUTE_OLD and info["c4"]:
            info["old_reps"] = sorted({min(orbit_old(x)) for x in orb})
            total_old += len(info["old_reps"])
        lst.append(info)
    lst.sort(key=lambda z: z["rep"])
    classes[c] = lst
    enum_stats[c] = {"raw_C1_3": nraw, "raw_C1_4": nraw4, "full_classes_C1_3": len(lst),
                     "full_classes_C1_4": sum(1 for z in lst if z["c4"]),
                     "old_classes_C1_4": (sum(len(z.get("old_reps", [])) for z in lst if z["c4"]) if COMPUTE_OLD else None)}
out["n5_enumeration"] = enum_stats
out["c4_invariant_under_full_dihedral"] = c4_invariant_all
out["total_full_classes_C1_4"] = sum(enum_stats[c]["full_classes_C1_4"] for c in enum_stats)
out["total_old_classes_C1_4"] = total_old if COMPUTE_OLD else None
out["t_after_enum"] = round(now(), 2)
save("partial: enumeration done")

# ---------------- explicit realizations ----------------
explicit = []
for d in EXPLICIT:
    r = S.run(d, 0, budget=2000000, deadline=time.time() + 15)
    e = {"list": d, "status": r["status"], "nodes": r["nodes"], "sym": 0}
    if r["status"] == "FEASIBLE":
        okv, h = verify(d, r["path"], m)
        e["verified_from_definition"] = okv
        e["hamiltonian_cycle_bits"] = [format(x, "05b") for x in h] if h else None
        e["dimension_i"] = "bit 4 (most significant)"
        if not okv:
            bugs.append(("explicit", d))
    explicit.append(e)
out["explicit"] = explicit
save("partial: explicit done")

# ---------------- sweep ----------------
status = {}

def solve(d, sym, budget, dl_abs):
    r = S.run(d, sym, budget=budget, deadline=dl_abs)
    res = {"status": r["status"], "nodes": r["nodes"], "sym": sym}
    if r["status"] == "FEASIBLE":
        okv, h = verify(d, r["path"], m)
        res["verified"] = okv
        if not okv:
            bugs.append(("sweep", d))
            res["status"] = "BUG_UNVERIFIED_WITNESS"
        res["h"] = h
    return res

order = []
for c in SWEEP_C:
    for z in classes[c]:
        if z["c4"]:
            order.append(z["rep"])
for d in order:
    if now() > PH["pass1"]:
        status[d] = {"status": "UNTESTED"}
        continue
    status[d] = solve(d, 2, BUDGET1, min(T0 + PH["pass1"], time.time() + 6))
unk = [d for d in order if status[d]["status"] == "UNKNOWN"]
for i, d in enumerate(unk):
    left = T0 + PH["pass2"] - time.time()
    if left <= 0.5:
        break
    share = left / (len(unk) - i)
    r = solve(d, 2, None, time.time() + share)
    r["nodes"] += status[d]["nodes"]
    status[d] = r
save("partial: sweep done")

# negative controls
neg = []
for c in NEG_C:
    for z in classes[c]:
        if not z["c4"]:
            if now() > PH["pass2"] + 3:
                neg.append({"rep": z["rep"], "status": "UNTESTED"}); continue
            r = solve(z["rep"], 2, 400000, time.time() + 3)
            neg.append({"rep": z["rep"], "status": r["status"], "nodes": r["nodes"]})
out["negative_controls_C4_false"] = neg
out["negative_controls_all_infeasible"] = all(x["status"] == "INFEASIBLE" for x in neg)

# recheck infeasible with sym1, then sym0
inf = [d for d in order if status[d]["status"] == "INFEASIBLE"]
inf.sort(key=lambda d: -len(d))
recheck1 = {}
for i, d in enumerate(inf):
    left = T0 + PH["sym1"] - time.time()
    if left <= 0.3:
        recheck1[d] = "UNTESTED"; continue
    r = S.run(d, 1, deadline=time.time() + left / (len(inf) - i))
    recheck1[d] = r["status"]
    if r["status"] == "FEASIBLE":
        bugs.append(("sym1_contradiction", d))
recheck0 = {}
cand0 = [d for d in inf if len(d) in SYM0_C] + [d for d in SYM0_LISTS]
for i, d in enumerate(cand0):
    left = T0 + PH["sym0"] - time.time()
    if left <= 0.3:
        recheck0[d] = "UNTESTED"; continue
    r = S.run(d, 0, deadline=time.time() + left / (len(cand0) - i))
    recheck0[d] = r["status"]
    if r["status"] == "FEASIBLE" and d in inf:
        bugs.append(("sym0_contradiction", d))

# ---------------- report ----------------
per_c = {}
for c in SWEEP_C:
    reps = [z for z in classes[c] if z["c4"]]
    st = [status[z["rep"]]["status"] for z in reps]
    per_c[c] = {k: st.count(k) for k in set(st)}
    per_c[c]["total_full_classes_C1_4"] = len(reps)
out["per_c_status_counts"] = per_c
rep2old = {z["rep"]: z.get("old_reps") for c in classes for z in classes[c] if z["c4"]}
infeasible_list = []
for d in inf:
    infeasible_list.append({"rep": d, "c": len(d), "nodes_sym2": status[d]["nodes"],
                            "sym1_recheck": recheck1.get(d), "sym0_recheck": recheck0.get(d),
                            "old_canonical_reps": rep2old.get(d)})
out["infeasible_full_classes"] = infeasible_list
out["num_infeasible_full_classes"] = len(inf)
out["num_old_classes_covered_by_infeasible"] = sum(len(rep2old.get(d) or []) for d in inf) if COMPUTE_OLD else None
out["unknown_lists"] = [d for d in order if status[d]["status"] in ("UNKNOWN", "UNTESTED")]
out["sym0_rechecks"] = {str(k): v for k, v in recheck0.items()}
ex_stat = {}
for d in EXAMPLES:
    rp = min(orbit_full(d))
    ex_stat[str(d)] = {"full_rep": rp, "status": status.get(rp, {}).get("status", "not in sweep")}
out["reported_examples"] = ex_stat
tables = {}
for c in TABLE_C:
    tab = []
    for z in classes[c]:
        e = {"rep": z["rep"], "C4": z["c4"], "orbit_size": z["orbit_size"]}
        if z["c4"]:
            s = status.get(z["rep"], {})
            e["status"] = s.get("status")
            e["nodes"] = s.get("nodes")
            if s.get("status") == "FEASIBLE":
                e["witness_h_bits"] = "".join(format(x, "05b") + " " for x in s["h"]).strip()
            e["old_reps"] = z.get("old_reps")
        else:
            nn = [x for x in neg if x["rep"] == z["rep"]]
            e["status"] = "excluded_by_C4" + (" / solver:" + nn[0]["status"] if nn else "")
        tab.append(e)
    tables[c] = tab
out["tables"] = tables
out["bugs"] = bugs
summ = (f"validation_ok={val_ok}; n4 counts={[validation[k]['total_count_sym0'] for k in (2,3,4)]} (expect 2,16,5376); "
        f"C4 invariant under full dihedral={c4_invariant_all}; full C1-4 classes n=5: {out['total_full_classes_C1_4']}, old classes: {out['total_old_classes_C1_4']}; "
        f"explicit: {[(e['list'], e['status'], e.get('verified_from_definition')) for e in explicit]}; "
        f"per-c: {per_c}; infeasible full classes: {[(x['rep'], x['sym1_recheck'], x['sym0_recheck']) for x in infeasible_list]}; "
        f"old classes covered: {out['num_old_classes_covered_by_infeasible']}; neg controls all infeasible: {out['negative_controls_all_infeasible']}; "
        f"unknown/untested: {len(out['unknown_lists'])}; bugs: {len(bugs)}")
save(summ)
