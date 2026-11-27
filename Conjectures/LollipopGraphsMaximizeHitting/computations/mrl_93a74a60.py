# MathResearchLab experiment 93a74a60-4d9e-4276-b1db-7c01310c153d
# Exhaustive exact reproduction of the lollipop-maximality check for n<=9
# sha256(code) = 2b43dcc1df40ef1e9d589937faf1a2fd346a0af30288a27c95b14bf068f6f5a5
# parameters: {"n_max": 9, "time_budget": 100, "pool_per_chunk": 60, "chunk_graphs": 25000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, shutil, warnings
import numpy as np
from fractions import Fraction
import networkx as nx
warnings.filterwarnings("ignore")

params = json.load(open(os.environ["MRL_PARAMS"]))
NMAX = int(params.get("n_max", 9))
BUDGET = float(params.get("time_budget", 100))
POOL_T = int(params.get("pool_per_chunk", 60))
CHUNK = int(params.get("chunk_graphs", 25000))
T0 = time.time()
def el(): return time.time() - T0

OEIS = {1: 1, 2: 1, 3: 2, 4: 6, 5: 21, 6: 112, 7: 853, 8: 11117, 9: 261080, 10: 11716571}

# ---------------- exact arithmetic ----------------
def montante(M):
    """Fraction-free Gauss-Jordan (Bareiss-Montante). Returns (det, adj) with M*adj = det*I.
    Assumes nonzero leading principal minors (true for reduced Laplacians of connected graphs)."""
    n = len(M)
    A = [[int(x) for x in M[i]] + [1 if i == j else 0 for j in range(n)] for i in range(n)]
    prev = 1
    for k in range(n):
        p = A[k][k]
        if p == 0:
            raise ValueError("zero pivot")
        rk = A[k]
        for i in range(n):
            if i == k:
                continue
            ri = A[i]; a = ri[k]
            A[i] = [(p * x - a * y) // prev for x, y in zip(ri, rk)]
        prev = p
    return prev, [row[n:] for row in A]

def ht_exact(n, edges):
    if n == 1:
        return Fraction(0)
    deg = [0] * n; adj = [[0] * n for _ in range(n)]
    for u, v in edges:
        adj[u][v] = adj[v][u] = 1; deg[u] += 1; deg[v] += 1
    m = len(edges); r = n - 1
    L0 = [[deg[i] if i == j else -adj[i][j] for j in range(r)] for i in range(r)]
    det, ad = montante(L0)
    Rn = [[0] * n for _ in range(n)]
    for i in range(r):
        for j in range(r):
            Rn[i][j] = ad[i][i] + ad[j][j] - 2 * ad[i][j]
        Rn[i][r] = ad[i][i]; Rn[r][i] = ad[i][i]
    rho = [sum(deg[k] * Rn[j][k] for k in range(n)) for j in range(n)]
    S = sum(Rn[i][j] for i in range(n) for j in range(i + 1, n))
    D = sum(abs(rho[i] - rho[j]) for i in range(n) for j in range(i + 1, n))
    return Fraction(2 * m * S + D, 2 * det)

def gauss(M):
    r = len(M)
    for c in range(r):
        p = next(i for i in range(c, r) if M[i][c] != 0)
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        M[c] = [x / pv for x in M[c]]
        for i in range(r):
            if i != c and M[i][c] != 0:
                f = M[i][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[c])]
    return [M[i][r] for i in range(r)]

def ht_direct(n, edges):
    """Independent check: solve h_i = 1 + avg_{w~i} h_w, h_j = 0, exactly, for each target j."""
    nb = [[] for _ in range(n)]
    for u, v in edges:
        nb[u].append(v); nb[v].append(u)
    H = [[Fraction(0)] * n for _ in range(n)]
    for j in range(n):
        idx = [i for i in range(n) if i != j]; pos = {v: t for t, v in enumerate(idx)}
        r = len(idx)
        M = [[Fraction(0)] * (r + 1) for _ in range(r)]
        for t, i in enumerate(idx):
            d = len(nb[i]); M[t][t] += d; M[t][r] = Fraction(d)
            for w in nb[i]:
                if w != j:
                    M[t][pos[w]] -= 1
        sol = gauss(M)
        for t, i in enumerate(idx):
            H[i][j] = sol[t]
    return sum(max(H[i][j], H[j][i]) for i in range(n) for j in range(i + 1, n))

# ---------------- graph families ----------------
def lolli(n, k):
    E = [(i, j) for i in range(k) for j in range(i + 1, k)]
    prev = k - 1
    for v in range(k, n):
        E.append((prev, v)); prev = v
    return E

def pc(n, k, j):
    E = [(i, i2) for i in range(k) for i2 in range(i + 1, k)]
    E += [(i, k) for i in range(j)]
    E += [(v, v + 1) for v in range(k, n - 1)]
    return E

def cm(n, k, where):
    E = [(i, j) for i in range(k) for j in range(i + 1, k) if (i, j) != (0, 1)]
    prev = 0 if where == 'end' else 2
    for v in range(k, n):
        E.append((prev, v)); prev = v
    return E

def tri(n, k):
    return lolli(n, k) + [(k - 1, k + 1)]

def nxg(n, E):
    G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(E); return G

def adjm(n, E):
    A = np.zeros((n, n), np.uint8)
    for u, v in E:
        A[u, v] = A[v, u] = 1
    return A

def edges_of(A):
    n = A.shape[0]
    return [(i, j) for i in range(n) for j in range(i + 1, n) if A[i, j]]

def identify(n, G):
    m = G.number_of_edges(); ds = sorted(d for _, d in G.degree())
    cands = [(f"L({n},{k})", lolli(n, k)) for k in range(2, n + 1)]
    for k in range(3, n):
        for j in range(2, k):
            cands.append((f"PC({n},{k},{j})", pc(n, k, j)))
    for k in range(3, n + 1):
        cands.append((f"CMend({n},{k})", cm(n, k, 'end')))
        if k < n:
            cands.append((f"CMother({n},{k})", cm(n, k, 'other')))
    for k in range(2, n - 1):
        cands.append((f"TRI({n},{k})", tri(n, k)))
    for name, E in cands:
        if len(E) != m:
            continue
        H = nxg(n, E)
        if sorted(d for _, d in H.degree()) != ds:
            continue
        if nx.is_isomorphic(G, H):
            return name
    return None

def make_lidx(n):
    d = {}
    for k in range(2, n + 1):
        E = lolli(n, k); H = nxg(n, E)
        d[len(E)] = (k, sorted(d_ for _, d_ in H.degree()), H)
    return d

def is_lolli(A, lidx):
    m = int(A.sum()) // 2
    if m not in lidx:
        return False
    k, ds, H = lidx[m]
    if sorted(A.sum(1).astype(int).tolist()) != ds:
        return False
    return nx.is_isomorphic(nx.from_numpy_array(A.astype(np.uint8)), H)

# ---------------- batched float HT + isomorphism-invariant hash ----------------
U = np.uint64
rs = np.random.RandomState(2024)
PW = rs.randint(1, 2 ** 62, size=16).astype(np.uint64) * U(2) + U(1)
QW = rs.randint(1, 2 ** 62, size=16).astype(np.uint64) * U(2) + U(1)

def mix(x):
    x = x ^ (x >> U(33)); x = x * U(0xff51afd7ed558ccd)
    x = x ^ (x >> U(33)); x = x * U(0xc4ceb9fe1a85ec53)
    x = x ^ (x >> U(33))
    return x

def analyze(Au8):
    B, n, _ = Au8.shape
    A = Au8.astype(np.float64)
    deg = A.sum(2)
    idx = np.arange(n)
    M = 1.0 / n - A
    M[:, idx, idx] += deg
    X = np.linalg.inv(M)
    d = X[:, idx, idx]
    R = d[:, :, None] + d[:, None, :] - 2.0 * X
    m = deg.sum(1) / 2.0
    rho = np.einsum('bij,bj->bi', R, deg)
    HT = m * R.sum((1, 2)) / 2.0 + np.abs(rho[:, :, None] - rho[:, None, :]).sum((1, 2)) / 4.0
    det = np.linalg.det(M)  # = n * tau
    tau = np.rint(det / n).astype(np.int64)
    N = np.rint(R * tau[:, None, None]).astype(np.int64)  # exact integers tau*R_ij
    c = (N * 2 + Au8.astype(np.int64)) * 16 + deg.astype(np.int64)[:, None, :]
    c = np.sort(c, axis=2).astype(np.uint64)
    rh = mix((c * PW[None, None, :n]).sum(2, dtype=np.uint64))
    rh = np.sort(rh, axis=1)
    gh = mix((rh * QW[None, :n]).sum(1, dtype=np.uint64) ^ mix(tau.astype(np.uint64) + U(12345)))
    return HT, gh, tau

def subsets(r):
    s = np.arange(1, 2 ** r)
    return ((s[:, None] >> np.arange(r)[None, :]) & 1).astype(np.uint8)

def gen_chunks(bases, r, S, chunk):
    s = len(S); n = r + 1
    cb = max(1, chunk // s)
    for b0 in range(0, len(bases), cb):
        b1 = min(len(bases), b0 + cb); nb = b1 - b0
        A = np.zeros((nb * s, n, n), np.uint8)
        A[:, :r, :r] = np.repeat(bases[b0:b1], s, axis=0)
        St = np.tile(S, (nb, 1))
        A[:, r, :r] = St; A[:, :r, r] = St
        yield A

def gdesc(n, A, val=None):
    G = nx.from_numpy_array(A.astype(np.uint8))
    ex = ht_exact(n, edges_of(A)) if val is None else val
    return {"HT": str(ex), "HT_float": float(ex), "identity": identify(n, G),
            "num_edges": int(G.number_of_edges()), "degseq": sorted((d for _, d in G.degree()), reverse=True),
            "edges": edges_of(A), "graph6": nx.to_graph6_bytes(G, header=False).decode().strip()}

# ---------------- sanity checks ----------------
res = {"geng_available": bool(shutil.which("geng") or shutil.which("nauty-geng")), "sanity": [], "levels": []}
for name, n, E, exp in [("P6", 6, lolli(6, 2), Fraction(223)), ("L(6,4)", 6, lolli(6, 4), Fraction(224))]:
    a = ht_direct(n, E); b = ht_exact(n, E); f = float(analyze(adjm(n, E)[None])[0][0])
    res["sanity"].append({"name": name, "direct": str(a), "montante": str(b), "float": f, "paper_value": str(exp),
                          "ok": bool(a == b == exp and abs(f - float(exp)) < 1e-8)})
import random
rr = random.Random(5); ok = True; cnt = 0
while cnt < 15:
    n = rr.randint(3, 8); G = nx.gnp_random_graph(n, rr.uniform(0.3, 0.8), seed=rr.randint(0, 10 ** 6))
    if not nx.is_connected(G):
        continue
    cnt += 1; E = list(G.edges())
    a = ht_direct(n, E); b = ht_exact(n, E); f = float(analyze(adjm(n, E)[None])[0][0])
    ok = ok and (a == b) and abs(f - float(a)) < 1e-8 * max(1.0, float(a))
    # invariance of hash under relabelling
    perm = list(range(n)); rr.shuffle(perm)
    E2 = [(perm[u], perm[v]) for u, v in E]
    h1 = analyze(adjm(n, E)[None])[1][0]; h2 = analyze(adjm(n, E2)[None])[1][0]
    ok = ok and (h1 == h2)
res["sanity"].append({"name": "15 random graphs: direct==montante==float and hash relabel-invariant", "ok": bool(ok)})

# ---------------- level-by-level generation ----------------
levels = {1: np.zeros((1, 1, 1), np.uint8)}
for n in range(2, NMAX + 1):
    if el() > BUDGET or (n - 1) not in levels:
        res["levels"].append({"n": n, "status": "not_attempted_time_or_missing_previous_level"})
        break
    t_start = el()
    r = n - 1; bases = levels[r]; S = subsets(r); s = len(S)
    total = len(bases) * s
    keep_all = n < NMAX
    hashes = np.empty(total, np.uint64); pos = 0
    Aall = np.empty((total, n, n), np.uint8) if keep_all else None
    lidx = make_lidx(n)
    poolA = []; poolV = []; aborted = False; saturated = False
    nl_val = -1.0; nl_A = None
    for A in gen_chunks(bases, r, S, CHUNK):
        if el() > BUDGET:
            aborted = True; break
        HT, gh, tau = analyze(A)
        B = len(A)
        hashes[pos:pos + B] = gh
        if keep_all:
            Aall[pos:pos + B] = A
        pos += B
        top = np.argsort(-HT)[:POOL_T]
        poolA.append(A[top].copy()); poolV.append(HT[top].copy())
        if len(top) < B and HT[top[-1]] >= HT[top[0]] - 1e-9:
            saturated = True
        for q in top:
            if HT[q] <= nl_val + 1e-9:
                break
            if not is_lolli(A[q], lidx):
                nl_val = float(HT[q]); nl_A = A[q].copy(); break
    hashes = hashes[:pos]
    uniq, first = np.unique(hashes, return_index=True)
    ndist = int(len(uniq))
    entry = {"n": n, "num_candidates_generated": int(pos), "expected_candidates": int(total), "aborted": aborted,
             "distinct_invariant_classes": ndist, "oeis_connected_count": OEIS.get(n),
             "count_matches_oeis": bool(ndist == OEIS.get(n)) if not aborted else None, "pool_saturated_warning": saturated}
    if keep_all and not aborted:
        levels[n] = Aall[np.sort(first)]
    # top classes from pool
    PA = np.concatenate(poolA); PV = np.concatenate(poolV)
    order = np.argsort(-PV)
    classes = []
    for q in order:
        if len(classes) >= 4 and PV[q] < classes[3]["float"] - 1e-6:
            break
        G = nx.from_numpy_array(PA[q])
        found = False
        for c in classes:
            if abs(c["float"] - PV[q]) < 1e-7 * max(1.0, PV[q]) and nx.is_isomorphic(c["G"], G):
                found = True; break
        if not found:
            classes.append({"G": G, "A": PA[q], "float": float(PV[q]), "exact": ht_exact(n, edges_of(PA[q]))})
    classes.sort(key=lambda c: -c["exact"])
    entry["top_classes"] = [gdesc(n, c["A"], c["exact"]) for c in classes[:3]]
    if len(classes) >= 2:
        entry["gap_top1_minus_top2"] = str(classes[0]["exact"] - classes[1]["exact"])
        entry["gap_top1_minus_top2_float"] = float(classes[0]["exact"] - classes[1]["exact"])
    # lollipops
    lv = {k: ht_exact(n, lolli(n, k)) for k in range(2, n + 1)}
    kb = max(lv, key=lv.get)
    entry["lollipop_values"] = {str(k): str(v) for k, v in lv.items()}
    entry["best_lollipop_k"] = kb; entry["best_lollipop_HT"] = str(lv[kb])
    entry["max_is_lollipop"] = bool(classes[0]["exact"] == lv[kb] and identify(n, classes[0]["G"]) is not None and str(identify(n, classes[0]["G"])).startswith("L("))
    if nl_A is not None:
        d = gdesc(n, nl_A)
        d["gap_best_lollipop_minus_this"] = str(lv[kb] - Fraction(d["HT"]))
        d["gap_float"] = float(lv[kb] - Fraction(d["HT"]))
        entry["best_non_lollipop"] = d
    else:
        entry["best_non_lollipop"] = None
    # cross-check with explicit representative list (n<NMAX)
    if keep_all and not aborted:
        HTr = analyze(levels[n])[0]
        o = np.argsort(-HTr)
        top_rep = [float(HTr[i]) for i in o[:3]]
        nl_rep = None
        for i in o:
            if not is_lolli(levels[n][i], lidx):
                nl_rep = float(HTr[i]); break
        entry["crosscheck_reps"] = {"top3_float_from_reps": top_rep,
                                    "top3_float_from_pool": [c["float"] for c in classes[:3]],
                                    "best_nonlolli_float_reps": nl_rep, "best_nonlolli_float_pool": nl_val,
                                    "agree": bool(np.allclose(top_rep[:len(classes[:3])], [c["float"] for c in classes[:3]]) and (nl_rep is None or abs(nl_rep - nl_val) < 1e-6))}
    entry["seconds"] = round(el() - t_start, 2)
    res["levels"].append(entry)

res["n10"] = "not attempted (261080*511 ~ 1.3e8 candidates exceed the time limit)"
lines = []
for e in res["levels"]:
    if "top_classes" in e:
        t = e["top_classes"]
        lines.append(f"n={e['n']}: classes={e['distinct_invariant_classes']} (OEIS {e['oeis_connected_count']}, match={e['count_matches_oeis']}, aborted={e['aborted']}); max={t[0]['HT']} [{t[0]['identity']}]; 2nd={t[1]['HT'] + ' [' + str(t[1]['identity']) + ']' if len(t) > 1 else None}; best non-lollipop={e['best_non_lollipop']['HT'] + ' [' + str(e['best_non_lollipop']['identity']) + ']' if e['best_non_lollipop'] else None}; max_is_lollipop={e['max_is_lollipop']}")
res["summary"] = ("Exhaustive search over connected graphs by adding one vertex at a time, with exact relabelling-invariant dedup. " + " | ".join(lines) +
                  f" | sanity ok: {[s['ok'] for s in res['sanity']]} | elapsed {el():.1f}s")
json.dump(res, open("result.json", "w"), indent=1, default=str)
