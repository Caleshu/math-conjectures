# MathResearchLab experiment ae339f44-ebf6-452f-acc8-d86e675a030f
# Q6 chromatic vectors: theory (lift/glue, explicit cycles) + square-flip local search + CP-SAT fallback (seed 1)
# sha256(code) = fbc164a0b765248a9103cb70ea63f24e5c958efb5c2f502265c0245185ef8a8f
# parameters: {"seed": 1, "ls_time": 65, "total_time": 108, "maxsteps": 400, "cp_max_per_vector": 10}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, random, itertools
from collections import defaultdict
params = json.load(open(os.environ["MRL_PARAMS"]))
T0 = time.time()
def el(): return time.time() - T0
SEED = params.get("seed", 1)
LS_TIME = params.get("ls_time", 65)
TOTAL = params.get("total_time", 108)
MAXSTEPS = params.get("maxsteps", 400)
CP_MAX = params.get("cp_max_per_vector", 10)
random.seed(SEED)
res = {"params": params}

def pvectors(n):
    N = 2 ** n; out = []
    def rec(prefix, remaining, minv, s):
        k = len(prefix)
        if k == n:
            if remaining == 0: out.append(tuple(prefix))
            return
        left = n - k; v = minv
        while v * left <= remaining:
            if s + v >= 2 ** (k + 1):
                rec(prefix + [v], remaining - v, v, s + v)
            v += 2
    rec([], N, 2, 0); return out

def basic_vectors(n):
    N = 2 ** n; out = []
    def rec(prefix, remaining, minv):
        k = len(prefix)
        if k == n:
            if remaining == 0: out.append(tuple(prefix))
            return
        v = minv
        while v * (n - k) <= remaining and v <= N // 2:
            rec(prefix + [v], remaining - v, v); v += 2
    rec([], N, 2); return out

def verify(order, n):
    N = 1 << n
    if len(order) != N or set(order) != set(range(N)): return None
    c = [0] * n
    for i in range(N):
        d = order[i] ^ order[(i + 1) % N]
        if d == 0 or (d & (d - 1)): return None
        c[d.bit_length() - 1] += 1
    return tuple(c)

def cyc_vec(order, n):
    N = len(order); c = [0] * n
    for i in range(N): c[(order[i] ^ order[(i + 1) % N]).bit_length() - 1] += 1
    return c

BAD = [0]

def search(start, t, n, maxsteps, rec):
    N = 1 << n
    order = list(start)
    pos = [0] * N
    for i, v in enumerate(order): pos[v] = i
    c = cyc_vec(order, n)
    tl = list(t)
    def dist(cc):
        s = sorted(cc); return sum(abs(s[k] - tl[k]) for k in range(n))
    d = dist(c)
    for step in range(maxsteps):
        if d == 0: return True
        groups = {}
        for i in range(N):
            u = order[i]; v = order[i + 1] if i + 1 < N else order[0]
            a = (u ^ v).bit_length() - 1
            for b in range(n):
                if b == a: continue
                m = 1 << b
                pz = pos[u ^ m]; pw = pos[v ^ m]
                if pw == pz + 1 or (pz == N - 1 and pw == 0):
                    groups.setdefault((a, b), []).append(i)
        if not groups: break
        scored = []
        for (a, b) in groups:
            cc = c[:]; cc[a] -= 2; cc[b] += 2
            scored.append((dist(cc), (a, b)))
        dmin = min(s for s, _ in scored)
        r = random.random()
        if dmin < d and r < 0.85:
            cand = [p for s, p in scored if s == dmin]
        elif r < 0.93:
            cand = [p for s, p in scored if s <= d] or [p for _, p in scored]
        else:
            cand = [p for _, p in scored]
        a, b = random.choice(cand)
        i = random.choice(groups[(a, b)])
        u = order[i]
        o = order[i:] + order[:i]
        z = u ^ (1 << b)
        k = o.index(z)
        o[1:k + 1] = o[k:0:-1]
        order = o
        for idx, v in enumerate(order): pos[v] = idx
        c[a] -= 2; c[b] += 2
        if c[a] < 2: BAD[0] += 1
        d = dist(c)
        key = tuple(sorted(c))
        if key not in rec: rec[key] = list(order)
    return d == 0

def drive(n, targets, rec, time_limit, maxsteps):
    targets = set(targets) - set(rec)
    attempts = 0
    while targets and el() < time_limit:
        for t in random.sample(sorted(targets), len(targets)):
            if el() >= time_limit: break
            if t in rec: continue
            keys = list(rec.keys())
            ds = sorted(keys, key=lambda s: (sum(abs(x - y) for x, y in zip(s, t)), random.random()))
            start = rec[random.choice(ds[:3])]
            search(start, t, n, maxsteps, rec); attempts += 1
        targets = {t for t in targets if t not in rec}
    return targets, attempts

def permute_cycle(order, n, target):
    c = cyc_vec(order, n)
    src = defaultdict(list)
    for d in range(n): src[c[d]].append(d)
    pi = [None] * n
    for d2 in range(n):
        d = src[target[d2]].pop(); pi[d] = d2
    return [sum(((v >> d) & 1) << pi[d] for d in range(n)) for v in order]

def glue(hx, hy, j, n):
    N = len(hx); m = 1 << j
    p = next(i for i in range(N) if hx[i] ^ hx[(i + 1) % N] == m)
    a = hx[p]; b = hx[(p + 1) % N]
    P0 = hx[(p + 1) % N:] + hx[:(p + 1) % N]
    q = next(i for i in range(N) if hy[i] ^ hy[(i + 1) % N] == m)
    s = a ^ hy[q]
    hy2 = [v ^ s for v in hy]
    P1 = hy2[(q + 1) % N:] + hy2[:(q + 1) % N]
    top = 1 << n
    return P0 + [v | top for v in P1[::-1]]

def lift(h, n):
    top = 1 << n; out = []
    for t, v in enumerate(h):
        out += [v, v | top] if t % 2 == 0 else [v | top, v]
    return out

from ortools.sat.python import cp_model
def cpsat(t, n, tl):
    N = 1 << n; m = cp_model.CpModel(); arcs = []; dl = [[] for _ in range(n)]; lit = {}
    for u in range(N):
        for b in range(n):
            v = u ^ (1 << b); x = m.NewBoolVar(""); arcs.append((u, v, x)); dl[b].append(x); lit[(u, v)] = x
    m.AddCircuit(arcs)
    for b in range(n): m.Add(sum(dl[b]) == t[b])
    m.Add(lit[(0, 1)] == 1)  # symmetry: translation + orientation, valid since t[0]>=2
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl; s.parameters.num_workers = 8
    st = s.Solve(m); name = s.StatusName(st)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {}
        for (u, v), x in lit.items():
            if s.Value(x): succ[u] = v
        order = [0]; cur = succ[0]
        while cur != 0 and len(order) <= N:
            order.append(cur); cur = succ[cur]
        return name, order
    return name, None

# ---- CP-SAT encoding sanity ----
san = {}
st, o = cpsat((4, 4, 4, 4), 4, 10); san["n4_(4,4,4,4)"] = [st, verify(o, 4) if o else None]
st, o = cpsat((2, 2, 2, 10), 4, 10); san["n4_(2,2,2,10)_violatesP"] = [st]
res["cpsat_sanity"] = san

# ---- Q5 image by local search ----
br5 = [i ^ (i >> 1) for i in range(32)]
P5 = pvectors(5)
rec5 = {tuple(sorted(cyc_vec(br5, 5))): br5}
left5, att5 = drive(5, P5, rec5, el() + 20, 300)
Im5 = set()
for k, o in rec5.items():
    v = verify(o, 5)
    if v is not None and tuple(sorted(v)) == k: Im5.add(k)
res["Q5"] = {"P5_count": len(P5), "realised_verified": len(Im5), "realised_not_in_P5": sorted(set(Im5) - set(P5)), "P5_unrealised": sorted(set(P5) - Im5), "attempts": att5, "time": el()}

# ---- n=6 theory ----
P6 = pvectors(6); P6set = set(P6)
res["n6_counts"] = {"basic": len(basic_vectors(6)), "P": len(P6)}
br6 = [i ^ (i >> 1) for i in range(64)]
rec6 = {tuple(sorted(cyc_vec(br6, 6))): br6}
res["brgc6_vector"] = cyc_vec(br6, 6)
lifted = set(); theory_bug = []
for t in P6:
    if 32 in t:
        r = list(t); r.remove(32); r = tuple(r)
        if r in Im5:
            cyc = lift(rec5[r], 5); v = verify(cyc, 6)
            if v is not None and tuple(sorted(v)) == t:
                lifted.add(t); rec6.setdefault(t, cyc)
            else: theory_bug.append(["lift", t])
perms = {s: sorted(set(itertools.permutations(s))) for s in Im5}
glued_w = {}
for x in Im5:
    for s in Im5:
        for y in perms[s]:
            for j in range(5):
                r = tuple(sorted([2] + [x[i] + y[i] - (2 if i == j else 0) for i in range(5)]))
                if r not in glued_w: glued_w[r] = (x, s, y, j)
glued = set()
for r, (x, s, y, j) in glued_w.items():
    if r not in P6set: theory_bug.append(["glue_outside_P", r]); continue
    hx = permute_cycle(rec5[x], 5, x); hy = permute_cycle(rec5[s], 5, y)
    cyc = glue(hx, hy, j, 5); v = verify(cyc, 6)
    if v is not None and tuple(sorted(v)) == r:
        glued.add(r); rec6.setdefault(r, cyc)
    else: theory_bug.append(["glue", r])
remaining_theory = sorted(P6set - lifted - glued)
has2 = [t for t in P6 if 2 in t]
res["theory"] = {"lifted": len(lifted), "glued": len(glued), "lifted_and_glued": len(lifted & glued), "union": len(lifted | glued), "remaining": len(remaining_theory), "P6_with_a_2": len(has2), "P6_with_a_2_not_glued": sorted(set(has2) - glued), "remaining_all_entries_ge4_max_lt32": all(min(t) >= 4 and max(t) < 32 for t in remaining_theory), "theory_bugs": theory_bug, "time": el()}
res["remaining_after_theory"] = remaining_theory

# ---- local search on remaining ----
left6, att6 = drive(6, remaining_theory, rec6, LS_TIME, MAXSTEPS)
res["local_search"] = {"attempts": att6, "left": sorted(left6), "time": el(), "visited_vectors": len(rec6)}

# ---- CP-SAT fallback ----
cp_results = {}
left = sorted(left6)
for idx, t in enumerate(left):
    rem = TOTAL - el()
    if rem < 2: cp_results[str(t)] = "NOT_RUN"; continue
    tl = min(CP_MAX, rem / (len(left) - idx))
    st, o = cpsat(t, 6, tl)
    cp_results[str(t)] = st
    if o is not None:
        v = verify(o, 6)
        if v is not None and tuple(v) == tuple(t): rec6[t] = o
        else: cp_results[str(t)] = st + "_BUT_VERIFY_FAILED"
res["cpsat"] = cp_results

# ---- final verification ----
verified = {}
not_in_P = []
for k, o in rec6.items():
    v = verify(o, 6)
    if v is None or tuple(sorted(v)) != k: continue
    if k not in P6set: not_in_P.append(k)
    verified[k] = o
final_unrealised = sorted(t for t in P6 if t not in verified)
infeasible = [t for t in final_unrealised if cp_results.get(str(t)) == "INFEASIBLE"]
res["verified_realised_count"] = len([t for t in P6 if t in verified])
res["visited_not_in_P6_BUG"] = not_in_P
res["flip_below2_BUG_count"] = BAD[0]
res["final_unrealised"] = final_unrealised
res["proved_infeasible_by_cpsat"] = infeasible
res["witnesses_for_remaining_after_theory"] = {str(t): verified[t] for t in remaining_theory if t in verified}
res["summary"] = (f"Q5: {len(Im5)}/{len(P5)} P-vectors realised (verified). n=6: {len(P6)} P-vectors (basic {res['n6_counts']['basic']}). "
                  f"Theory (explicit verified lift/glue cycles): lifted {len(lifted)}, glued {len(glued)}, union {len(lifted|glued)}; remaining {len(remaining_theory)} "
                  f"(all entries>=4 & max<32: {res['theory']['remaining_all_entries_ge4_max_lt32']}). Local search left {len(left6)}; after CP-SAT final unrealised {len(final_unrealised)}: {final_unrealised}. "
                  f"CP-SAT INFEASIBLE: {infeasible}. Bugs: theory {len(theory_bug)}, visited-not-in-P {len(not_in_P)}, below2 {BAD[0]}. CP sanity {san}. time {el():.1f}s")
json.dump(res, open("result.json", "w"))
print(res["summary"])
