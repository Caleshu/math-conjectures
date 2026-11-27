# MathResearchLab experiment 260dd780-7b0b-4650-9394-973f54951ab6
# Straight-free Hamiltonian cycles in Q3..Q6 and the T(7) path-pair problem
# sha256(code) = 7b73f6919bea7b9178e3ad4374149fee1a2bbaff974abd3bb0ab3b2ae484b6ca
# parameters: {"budget_s": 108, "time_limits": {"sanity": 4, "b5": 8, "b6": 10, "psan4": 2, "psan7": 5, "psan5": 3, "c0": 12, "c1": 25, "c2": 15, "c3": 15}}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, sys
from ortools.sat.python import cp_model

T0 = time.time()
try:
    params = json.load(open(os.environ["MRL_PARAMS"]))
except Exception:
    params = {}
BUDGET = float(params.get("budget_s", 108))
W = int(params.get("workers", min(8, os.cpu_count() or 1)))
TLd = {"sanity": 4, "b5": 8, "b6": 10, "psan4": 2, "psan7": 5, "psan5": 3,
       "c0": 12, "c1": 25, "c2": 15, "c3": 15}
TLd.update(params.get("time_limits", {}))

res = {"workers": W, "stages": {}}

def save():
    res["elapsed_s"] = round(time.time() - T0, 2)
    with open("result.json", "w") as f:
        json.dump(res, f, indent=1)

def popc(x):
    return bin(x).count("1")

def norm(a, b):
    return (a, b) if a < b else (b, a)

# ---------------- independent checkers (no shared code with models) -------------
def is_ham_cycle(seq, n):
    N = 1 << n
    if len(seq) != N or len(set(seq)) != N:
        return False
    if any((not isinstance(v, int)) or v < 0 or v >= N for v in seq):
        return False
    return all(popc(seq[k] ^ seq[(k + 1) % N]) == 1 for k in range(N))

def is_ham_path(seq, n, u, v):
    N = 1 << n
    return (len(seq) == N and len(set(seq)) == N and all(0 <= x < N for x in seq)
            and seq[0] == u and seq[-1] == v
            and all(popc(seq[k] ^ seq[k + 1]) == 1 for k in range(N - 1)))

def straight_twisted(seq):
    # brute force over pairs of cycle edges (oriented by the sequence)
    N = len(seq); st = tw = 0
    for i in range(N):
        a, b = seq[i], seq[(i + 1) % N]
        for j in range(i + 1, N):
            c, d = seq[j], seq[(j + 1) % N]
            if len({a, b, c, d}) < 4:
                continue
            if popc(b ^ c) == 1 and popc(d ^ a) == 1:
                st += 1   # h_i h_{i+1} h_j h_{j+1} is a 4-cycle
            if popc(b ^ d) == 1 and popc(a ^ c) == 1:
                tw += 1   # h_i h_{i+1} h_{j+1} h_j is a 4-cycle
    return st, tw

def opp_pairs(E1, E2, n):
    # ordered pairs (e in E1, f in E2) that are opposite rims of a 4-cycle of Q_n
    cnt = 0
    for (a, b) in E1:
        t = a ^ b
        for k in range(n):
            s = 1 << k
            if s == t:
                continue
            if norm(a ^ s, b ^ s) in E2:
                cnt += 1
    return cnt

def cyc_edges(seq):
    N = len(seq)
    return set(norm(seq[k], seq[(k + 1) % N]) for k in range(N))

def path_edges(seq):
    return set(norm(seq[k], seq[k + 1]) for k in range(len(seq) - 1))

def dir_counts_cycle(seq, n):
    N = len(seq); c = [0] * n
    for k in range(N):
        t = seq[k] ^ seq[(k + 1) % N]
        c[t.bit_length() - 1] += 1
    return c

def proj(a, i):
    low = a & ((1 << i) - 1); high = a >> (i + 1)
    return low | (high << i)

def fe5d7f_check(seq, n):
    N = len(seq); ok_counts = True; ok_pattern = True
    full = (1 << (n - 1)) - 1
    for i in range(n):
        bit = 1 << i; senses = {}
        for k in range(N):
            a, b = seq[k], seq[(k + 1) % N]
            if a ^ b == bit:
                senses[proj(a, i)] = 1 if (b & bit) else -1
        if len(senses) != 4:
            ok_counts = False; ok_pattern = False; continue
        plus = [p for p, s in senses.items() if s > 0]
        minus = [p for p, s in senses.items() if s < 0]
        pat = (len(plus) == 2 and len(minus) == 2 and popc(plus[0] ^ plus[1]) == 1
               and sorted(p ^ full for p in plus) == sorted(minus))
        if not pat:
            ok_pattern = False
    return ok_counts, ok_pattern

def has_iji(seq):
    N = len(seq)
    t = [seq[k] ^ seq[(k + 1) % N] for k in range(N)]
    return any(t[k] == t[(k + 2) % N] for k in range(N))

# ---------------- (a) exhaustive enumeration ----------------
def enum_paths_from0(n):
    N = 1 << n; out = []; path = [0]; used = bytearray(N); used[0] = 1
    sys.setrecursionlimit(10000)
    def dfs(x):
        if len(path) == N:
            out.append(path.copy()); return
        for k in range(n):
            y = x ^ (1 << k)
            if not used[y]:
                used[y] = 1; path.append(y); dfs(y); path.pop(); used[y] = 0
    dfs(0)
    return out

straightfree_cycles = {}
for n in (3, 4):
    t = time.time()
    paths = enum_paths_from0(n)
    cycles = [p for p in paths if popc(p[-1]) == 1 and p[1] < p[-1]]
    stats = {"n": n, "num_ham_paths_from_0": len(paths),
             "expected_paths_from_0": {3: 18, 4: 5712}[n],
             "num_ham_cycles": len(cycles), "expected_cycles": {3: 6, 4: 1344}[n]}
    dist = {}; sf_list = []; min_total = None; cross_ok = True; iji_ok = True
    for c in cycles:
        assert is_ham_cycle(c, n)
        st, tw = straight_twisted(c)
        E = cyc_edges(c)
        if opp_pairs(E, E, n) // 2 != st + tw:
            cross_ok = False
        if has_iji(c) and st == 0:
            iji_ok = False
        dist[st] = dist.get(st, 0) + 1
        tot = st + tw
        min_total = tot if min_total is None else min(min_total, tot)
        if st == 0:
            sf_list.append(c)
    stats["straight_count_distribution"] = {str(k): v for k, v in sorted(dist.items())}
    stats["min_total_inscribed"] = min_total
    stats["fast_vs_slow_counter_agree"] = cross_ok
    stats["iji_implies_straight_holds"] = iji_ok
    stats["num_straight_free_cycles"] = len(sf_list)
    if n == 4:
        pats = [fe5d7f_check(c, 4) for c in sf_list]
        stats["fe5d7f_all_have_4_per_direction"] = all(p[0] for p in pats)
        stats["fe5d7f_all_match_antipodal_pattern"] = all(p[1] for p in pats)
        stats["fe5d7f_num_violations"] = sum(1 for p in pats if not (p[0] and p[1]))
        stats["straight_free_dir_counts"] = [dir_counts_cycle(c, 4) for c in sf_list[:10]]
        stats["straight_free_examples"] = sf_list[:6]
        stats["straight_free_twisted_counts"] = sorted(set(straight_twisted(c)[1] for c in sf_list))
    straightfree_cycles[n] = sf_list
    # square-free Hamiltonian paths from 0 (edge-set condition)
    sfp = [p for p in paths if opp_pairs(path_edges(p), path_edges(p), n) == 0]
    stats["num_square_free_ham_paths_from_0"] = len(sfp)
    ends = {}
    for p in sfp:
        ends[p[-1]] = ends.get(p[-1], 0) + 1
    stats["square_free_paths_by_end"] = {str(k): v for k, v in ends.items()}
    stats["sf_path_count_to_all_ones"] = ends.get((1 << n) - 1, 0)
    stats["time_s"] = round(time.time() - t, 2)
    res["stages"][f"a_enum_Q{n}"] = stats
    save()

# ---------------- CP-SAT models ----------------
def rim_quads(n):
    N = 1 << n
    for a in range(N):
        for d in range(n):
            for k in range(d + 1, n):
                if (a >> d) & 1 or (a >> k) & 1:
                    continue
                b = a | (1 << d); c = a | (1 << k); e = b | (1 << k)
                # (p,q,r,s): rims p-q and r-s, p~r, q~s ; square p q s r
                yield (a, b, c, e)
                yield (a, c, b, e)

def solve(m, tl):
    rem = BUDGET - (time.time() - T0) - 2.0
    tl = min(tl, rem)
    if tl < 0.5:
        return None, "SKIPPED_TIME", 0.0
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_workers = W
    t = time.time(); st = s.Solve(m)
    return s, s.StatusName(st), round(time.time() - t, 2)

def cycle_model(n, mode, symb=True):
    N = 1 << n; m = cp_model.CpModel(); arc = {}; arcs = []
    for x in range(N):
        for k in range(n):
            y = x ^ (1 << k); l = m.NewBoolVar(f"a_{x}_{y}"); arc[(x, y)] = l; arcs.append((x, y, l))
    m.AddCircuit(arcs)
    ncl = 0
    for (p, q, r, s_) in rim_quads(n):
        pairs = []
        if mode in ("straight", "all"):
            pairs += [(arc[(p, q)], arc[(s_, r)]), (arc[(q, p)], arc[(r, s_)])]
        if mode == "all":
            pairs += [(arc[(p, q)], arc[(r, s_)]), (arc[(q, p)], arc[(s_, r)])]
        for l1, l2 in pairs:
            m.AddBoolOr([l1.Not(), l2.Not()]); ncl += 1
    if symb:
        # WLOG (coordinate permutation + reversal): 0 -> e1 and e2 -> 0
        m.Add(arc[(0, 1)] == 1); m.Add(arc[(2, 0)] == 1)
    return m, arc, ncl

def extract_cycle(s, arc, N):
    succ = {}
    for (x, y), l in arc.items():
        if s.Value(l):
            succ[x] = y
    seq = [0]
    for _ in range(N):
        nx = succ.get(seq[-1])
        if nx is None or nx == 0:
            break
        seq.append(nx)
    return seq

def run_cycle(n, mode, tl, key):
    m, arc, ncl = cycle_model(n, mode)
    s, status, tt = solve(m, tl)
    out = {"n": n, "mode": mode, "status": status, "time_s": tt, "num_forbidden_pairs": ncl}
    if status in ("FEASIBLE", "OPTIMAL"):
        seq = extract_cycle(s, arc, 1 << n)
        out["witness"] = seq
        out["witness_is_ham_cycle"] = is_ham_cycle(seq, n)
        if out["witness_is_ham_cycle"]:
            st, tw = straight_twisted(seq)
            out["witness_straight"] = st; out["witness_twisted"] = tw
            out["dir_counts"] = dir_counts_cycle(seq, n)
    res["stages"][key] = out; save()
    return out

# sanity checks for the cycle model
san = {}
o3 = run_cycle(3, "straight", TLd["sanity"], "sanity_Q3_straight")
san["Q3_straight_agrees_with_enum"] = ((o3["status"] in ("FEASIBLE", "OPTIMAL")) == (len(straightfree_cycles[3]) > 0)) and o3["status"] != "UNKNOWN"
o4 = run_cycle(4, "straight", TLd["sanity"], "sanity_Q4_straight")
san["Q4_straight_agrees_with_enum"] = ((o4["status"] in ("FEASIBLE", "OPTIMAL")) == (len(straightfree_cycles[4]) > 0)) and o4["status"] != "UNKNOWN"
if o4.get("witness_is_ham_cycle"):
    san["Q4_straight_witness_has_0_straight"] = o4["witness_straight"] == 0
on = run_cycle(4, "none", TLd["sanity"], "sanity_Q4_none")
san["Q4_unconstrained_feasible_valid"] = bool(on.get("witness_is_ham_cycle"))
o5 = run_cycle(5, "all", TLd["sanity"], "sanity_Q5_all")
san["Q5_squarefree_infeasible"] = o5["status"] == "INFEASIBLE"
res["cycle_model_sanity"] = san
res["cycle_model_sanity_passed"] = all(san.values())
save()

# ---------------- (b) straight-free cycles in Q5, Q6 ----------------
b5 = run_cycle(5, "straight", TLd["b5"], "b_Q5_straight_free")
b6 = run_cycle(6, "straight", TLd["b6"], "b_Q6_straight_free")

# ---------------- path-pair model ----------------
def path_model(a, v, nP, sq=True, disjoint=True, cross=False, symb=None):
    N = 1 << a; u = 0
    assert popc(u ^ v) != 1 and u != v
    m = cp_model.CpModel()
    edges = [(x, x ^ (1 << k)) for x in range(N) for k in range(a) if x < (x ^ (1 << k))]
    P = []
    for t in range(nP):
        arc = {}; arcs = []
        for x in range(N):
            for k in range(a):
                y = x ^ (1 << k); l = m.NewBoolVar(f"a{t}_{x}_{y}"); arc[(x, y)] = l; arcs.append((x, y, l))
        d = m.NewBoolVar(f"dummy{t}"); arcs.append((v, u, d)); m.Add(d == 1)
        m.AddCircuit(arcs)
        xe = {}
        for (x, y) in edges:
            e = m.NewBoolVar(f"e{t}_{x}_{y}"); m.Add(e == arc[(x, y)] + arc[(y, x)]); xe[(x, y)] = e
        P.append((arc, xe))
    opp = []
    for (p, q, r, s_) in rim_quads(a):
        opp.append((norm(p, q), norm(r, s_)))
    if sq:
        for (_, xe) in P:
            for e, f in opp:
                m.AddBoolOr([xe[e].Not(), xe[f].Not()])
    if nP == 2 and disjoint:
        for e in edges:
            m.AddBoolOr([P[0][1][e].Not(), P[1][1][e].Not()])
    if nP == 2 and cross:
        for e, f in opp:
            m.AddBoolOr([P[0][1][e].Not(), P[1][1][f].Not()])
            m.AddBoolOr([P[1][1][e].Not(), P[0][1][f].Not()])
    if symb == "allones":
        # automorphisms fixing 0 and 1^a = coordinate permutations
        m.Add(P[0][0][(0, 1)] == 1)
        if nP == 2:
            m.Add(P[1][0][(0, 2)] == 1)
    elif symb == "w3":
        # v = e1+e2+e3: stabilizer S3 x S_{a-3}; P's first step WLOG in {e1, e4}
        m.Add(P[0][0][(0, 1)] + P[0][0][(0, 8)] == 1)
    return m, P

def extract_path(s, arc, u, v, N):
    succ = {}
    for (x, y), l in arc.items():
        if s.Value(l):
            succ[x] = y
    seq = [u]
    for _ in range(N):
        if seq[-1] == v:
            break
        nx = succ.get(seq[-1])
        if nx is None:
            break
        seq.append(nx)
    return seq

def run_paths(a, v, nP, tl, key, **kw):
    m, P = path_model(a, v, nP, **kw)
    s, status, tt = solve(m, tl)
    out = {"a": a, "u": 0, "v": v, "nP": nP, "opts": {k: str(x) for k, x in kw.items()},
           "status": status, "time_s": tt}
    if status in ("FEASIBLE", "OPTIMAL"):
        paths = [extract_path(s, P[t][0], 0, v, 1 << a) for t in range(nP)]
        out["witness_paths"] = paths
        ver = {}
        Es = []
        for t, p in enumerate(paths):
            ok = is_ham_path(p, a, 0, v); ver[f"P{t}_is_ham_path"] = ok
            E = path_edges(p); Es.append(E)
            ver[f"P{t}_inscribed_squares"] = opp_pairs(E, E, a) // 2
        if nP == 2:
            ver["shared_edges"] = len(Es[0] & Es[1])
            ver["cross_opposite_pairs"] = opp_pairs(Es[0], Es[1], a)
        out["verification"] = ver
    res["stages"][key] = out; save()
    return out

# path-model sanity
ps = {}
p4 = run_paths(4, 15, 1, TLd["psan4"], "sanity_path_Q4_sf_to_1111", sq=True, symb="allones")
enum4 = res["stages"]["a_enum_Q4"]["sf_path_count_to_all_ones"]
ps["Q4_sf_path_agrees_with_enum"] = (p4["status"] != "UNKNOWN") and ((p4["status"] in ("FEASIBLE", "OPTIMAL")) == (enum4 > 0))
p7n = run_paths(7, 127, 2, TLd["psan7"], "sanity_path_Q7_two_disjoint_no_sq", sq=False, disjoint=True, symb="allones")
v7 = p7n.get("verification", {})
ps["Q7_unconstrained_pair_feasible_valid"] = bool(v7.get("P0_is_ham_path") and v7.get("P1_is_ham_path") and v7.get("shared_edges") == 0)
res["path_model_sanity"] = ps
res["path_model_sanity_passed"] = all(ps.values())
save()
p5 = run_paths(5, 31, 1, TLd["psan5"], "test_Q5_single_sf_path_to_11111", sq=True, symb="allones")

# ---------------- (c) T(7) ----------------
c0 = run_paths(7, 127, 1, TLd["c0"], "c0_Q7_single_sf_path_to_1111111", sq=True, symb="allones")
if c0["status"] == "INFEASIBLE":
    res["stages"]["c1_T7_allones_disjoint"] = {"status": "INFEASIBLE (implied by c0)"}
    res["stages"]["c2_T7_allones_disjoint_cross"] = {"status": "INFEASIBLE (implied by c0)"}
    c1 = c2 = None
else:
    c1 = run_paths(7, 127, 2, TLd["c1"], "c1_T7_allones_disjoint", sq=True, disjoint=True, cross=False, symb="allones")
    c2 = run_paths(7, 127, 2, TLd["c2"], "c2_T7_allones_disjoint_cross", sq=True, disjoint=True, cross=True, symb="allones")
c3 = run_paths(7, 7, 2, TLd["c3"], "c3_T7_weight3_disjoint", sq=True, disjoint=True, cross=False, symb="w3")

# ---------------- optional: product construction verification ----------------
def good_T(o):
    if not o or "verification" not in o:
        return False
    v = o["verification"]
    return (v.get("P0_is_ham_path") and v.get("P1_is_ham_path") and v.get("P0_inscribed_squares") == 0
            and v.get("P1_inscribed_squares") == 0 and v.get("shared_edges") == 0)

Tw = None
for o in (c1, c2, c3):
    if good_T(o):
        Tw = o; break
Cb = None
if straightfree_cycles.get(4):
    Cb = (4, straightfree_cycles[4][0])
elif b5.get("witness_is_ham_cycle") and b5.get("witness_straight") == 0:
    Cb = (5, b5["witness"])
elif b6.get("witness_is_ham_cycle") and b6.get("witness_straight") == 0:
    Cb = (6, b6["witness"])
if Tw is not None and Cb is not None:
    P0, P1 = Tw["witness_paths"]; b, C = Cb; a = 7
    seq = []
    for k, y in enumerate(C):
        layer = P0 if k % 2 == 0 else P1[::-1]
        for x in layer:
            seq.append(x | (y << a))
    okc = is_ham_cycle(seq, a + b)
    E = cyc_edges(seq)
    nsq = opp_pairs(E, E, a + b) // 2 if okc else None
    res["stages"]["product_check"] = {"n": a + b, "b": b, "is_ham_cycle": okc, "inscribed_squares": nsq,
                                      "square_free_cycle_found": bool(okc and nsq == 0)}
else:
    res["stages"]["product_check"] = {"skipped": True, "have_T7": Tw is not None, "have_straight_free_Cb": Cb is not None}

# ---------------- summary ----------------
S = res["stages"]
parts = []
for n in (3, 4):
    e = S[f"a_enum_Q{n}"]
    parts.append(f"Q{n}: {e['num_ham_cycles']} cycles (exp {e['expected_cycles']}), paths from 0 {e['num_ham_paths_from_0']} (exp {e['expected_paths_from_0']}), straight-free {e['num_straight_free_cycles']}, min total squares {e['min_total_inscribed']}, sf paths from 0 {e['num_square_free_ham_paths_from_0']}")
e4 = S["a_enum_Q4"]
if e4["num_straight_free_cycles"] > 0:
    parts.append(f"C-fe5d7f: 4/dir {e4['fe5d7f_all_have_4_per_direction']}, pattern {e4['fe5d7f_all_match_antipodal_pattern']}")
parts.append(f"cycle-model sanity {res['cycle_model_sanity_passed']}, path-model sanity {res['path_model_sanity_passed']}")
parts.append(f"straight-free Q5: {b5['status']}, Q6: {b6['status']}")
parts.append(f"Q5 single sf path 0->11111: {p5['status']}")
parts.append(f"Q7 single sf path 0->1^7: {c0['status']}")
for k in ("c1_T7_allones_disjoint", "c2_T7_allones_disjoint_cross", "c3_T7_weight3_disjoint"):
    parts.append(f"{k}: {S[k]['status']}")
parts.append(f"product: {S['product_check']}")
res["summary"] = " | ".join(parts)
save()
print(res["summary"])
