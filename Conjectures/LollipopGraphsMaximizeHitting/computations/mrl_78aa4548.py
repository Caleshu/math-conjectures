# MathResearchLab experiment 78aa4548-6f99-4fd5-931f-f690c05958da
# Exact lollipop k_opt offset, exact family comparisons (n<=40), and local search for non-lollipop maximisers (n=11..18)
# sha256(code) = d1df624a3b640db969cc2024c9410d3803595951bbf847102dc5e3c66e12f3c6
# parameters: {"time_budget": 108, "scan_nmax": 1000, "scan_large": [2000, 5000, 10000, 20000, 50000], "family_nmax": 40, "family_exact_all_nmax": 24, "ls_n": [11, 12, 13, 14, 15, 16, 17, 18], "seed": 7, "partA_deadline": 16, "partB_deadline": 42}
# environment: {}

import json, os, time, random, math, warnings
import numpy as np
from fractions import Fraction
import networkx as nx
import sympy as sp
import mpmath
warnings.filterwarnings("ignore")

params = json.load(open(os.environ["MRL_PARAMS"]))
BUDGET = float(params.get("time_budget", 108))
N1 = int(params.get("scan_nmax", 1000))
LARGE = [int(x) for x in params.get("scan_large", [2000, 5000, 10000, 20000, 50000])]
FAM_NMAX = int(params.get("family_nmax", 40))
EXACT_ALL_NMAX = int(params.get("family_exact_all_nmax", 24))
LS_N = [int(x) for x in params.get("ls_n", list(range(11, 19)))]
SEED = int(params.get("seed", 7))
TA = float(params.get("partA_deadline", 16))
TB = float(params.get("partB_deadline", 42))
T0 = time.time()
def el(): return time.time() - T0
ALPHA = (1 + math.sqrt(21)) / 10
out = {}

# ---------------- exact tools ----------------
def montante(M):
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
        pv = M[c][c]; M[c] = [x / pv for x in M[c]]
        for i in range(r):
            if i != c and M[i][c] != 0:
                f = M[i][c]; M[i] = [a - f * b for a, b in zip(M[i], M[c])]
    return [M[i][r] for i in range(r)]

def ht_direct(n, edges):
    nb = [[] for _ in range(n)]
    for u, v in edges:
        nb[u].append(v); nb[v].append(u)
    H = [[Fraction(0)] * n for _ in range(n)]
    for j in range(n):
        idx = [i for i in range(n) if i != j]; pos = {v: t for t, v in enumerate(idx)}; r = len(idx)
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

# ---------------- builders ----------------
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
def adjm(n, E):
    A = np.zeros((n, n), np.uint8)
    for u, v in E:
        A[u, v] = A[v, u] = 1
    return A
def nxg(n, E):
    G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(E); return G
def edges_of(A):
    n = A.shape[0]
    return [(i, j) for i in range(n) for j in range(i + 1, n) if A[i, j]]

def ht_batch(A):
    A = np.asarray(A, dtype=np.float64); B, n, _ = A.shape
    deg = A.sum(2); M = 1.0 / n - A; idx = np.arange(n); M[:, idx, idx] += deg
    X = np.linalg.inv(M); d = X[:, idx, idx]
    R = d[:, :, None] + d[:, None, :] - 2.0 * X
    m = deg.sum(1) / 2.0
    rho = np.einsum('bij,bj->bi', R, deg)
    return m * R.sum((1, 2)) / 2.0 + np.abs(rho[:, :, None] - rho[:, None, :]).sum((1, 2)) / 4.0

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

# ---------------- exact lollipop formula (own derivation) ----------------
# clique {a's, c}, path v1..vm. A_t=E_c T_{v_t}=K t+t^2, B_t=E_{v_t} T_c=2mt-t^2, E_c T_a=k-1+4m/k, E_a T_a'=k-1+2m/k.
# Returns N = k*HT (integer).
def lvalid(n, k):
    m = n - k; K = k * (k - 1)
    return k * (K - 2 * m + 2) >= 4 * m
def Nclosed(n, k):
    m = n - k; K = k * (k - 1)
    N = (k - 1) * (k - 2) // 2 * (K + 2 * m) + (k - 1) * (K + 4 * m)
    N += (k - 1) * (m * K + k * (K * m * (m + 1) // 2 + m * (m + 1) * (2 * m + 1) // 6))
    N += k * (m * (m + 1) * (m + 2) * (K + m) // 6)
    return N
def Ngeneral(n, k):
    m = n - k; K = k * (k - 1)
    t = np.arange(m + 1, dtype=np.int64)
    A = K * t + t * t; B = 2 * m * t - t * t
    N = (k - 1) * (k - 2) // 2 * (K + 2 * m) + (k - 1) * (K + 4 * m)
    at = np.maximum(k * A[1:], k * B[1:] + 4 * m)
    N += (k - 1) * (m * K + int(at.sum()))
    dA = A[None, :] - A[:, None]; dB = B[None, :] - B[:, None]
    mask = np.triu(np.ones((m + 1, m + 1), bool), 1)
    N += k * int(np.maximum(dA, dB)[mask].sum())
    return N

def scan(n):
    vals = {}
    for k in range(2, n + 1):
        if lvalid(n, k):
            vals[k] = Fraction(Nclosed(n, k), k)
    best = max(vals.values()) if vals else Fraction(-1)
    unres = []
    for k in range(2, n + 1):
        if k in vals:
            continue
        m = n - k; K = k * (k - 1)
        ub = (n * (n - 1) // 2) * (2 * k + K * m + 3 * m * m + 4 * m + 1)  # C(n,2)*max hitting time bound
        if ub < best:
            continue
        if n <= 1500:
            vals[k] = Fraction(Ngeneral(n, k), k)
        else:
            unres.append(k)
    best = max(vals.values())
    ks = sorted(k for k, v in vals.items() if v == best)
    return vals, best, ks, unres

# ---------------- validation ----------------
val = {}
chk = []
for name, n, E, exp in [("P6", 6, lolli(6, 2), Fraction(223)), ("L(6,4)", 6, lolli(6, 4), Fraction(224)), ("L(5,3) team claim", 5, lolli(5, 3), Fraction(296, 3)), ("P5 team claim", 5, lolli(5, 2), Fraction(102))]:
    a = ht_direct(n, E); b = ht_exact(n, E); f = float(ht_batch(adjm(n, E)[None])[0])
    chk.append({"name": name, "direct": str(a), "montante": str(b), "float": f, "expected": str(exp), "ok": bool(a == b == exp and abs(f - float(exp)) < 1e-8)})
val["known_values"] = chk
rng = random.Random(SEED); ok = True; c = 0
while c < 12:
    n = rng.randint(4, 8); G = nx.gnp_random_graph(n, rng.uniform(0.3, 0.8), seed=rng.randint(0, 10 ** 6))
    if not nx.is_connected(G):
        continue
    c += 1; E = list(G.edges()); a = ht_direct(n, E); b = ht_exact(n, E); f = float(ht_batch(adjm(n, E)[None])[0])
    ok = ok and a == b and abs(f - float(a)) < 1e-8 * max(1.0, float(a))
val["random_direct_vs_montante_vs_float_ok"] = bool(ok)
lok = True; mism = []
for n in range(2, 14):
    for k in range(2, n + 1):
        ex = ht_exact(n, lolli(n, k)); g = Fraction(Ngeneral(n, k), k)
        if g != ex or (lvalid(n, k) and Fraction(Nclosed(n, k), k) != ex):
            lok = False; mism.append([n, k])
for n in range(14, 61):
    for k in range(2, n + 1):
        if lvalid(n, k) and Nclosed(n, k) != Ngeneral(n, k):
            lok = False; mism.append([n, k])
val["lollipop_formula_ok"] = bool(lok); val["lollipop_formula_mismatches"] = mism[:20]
out["validation"] = val

# ---------------- Part A: exact k_opt scan ----------------
scanres = {}
for n in list(range(4, N1 + 1)) + LARGE:
    if el() > TA:
        break
    vals, best, ks, unres = scan(n)
    k0 = ks[0]; xc = None
    if (k0 - 1) in vals and (k0 + 1) in vals:
        hm, h0, hp = vals[k0 - 1], vals[k0], vals[k0 + 1]
        den = hm - 2 * h0 + hp
        if den != 0:
            xc = k0 + float((hm - hp) / (2 * den))
    sec = max((v for v in vals.values() if v != best), default=None)
    scanres[n] = {"kopt": ks, "best": best, "gap_to_second": float(best - sec) if sec is not None else None, "xc": xc, "unresolved": unres}
out["partA_scanned_up_to"] = max(scanres) if scanres else None

# symbolic expansion
x_, n_ = sp.symbols('x n', positive=True)
def Nsym(nn, kk):
    mm = nn - kk; KK = kk * (kk - 1)
    return ((kk - 1) * (kk - 2) / 2 * (KK + 2 * mm) + (kk - 1) * (KK + 4 * mm)
            + (kk - 1) * (mm * KK + kk * (KK * mm * (mm + 1) / 2 + mm * (mm + 1) * (2 * mm + 1) / 6))
            + kk * (mm * (mm + 1) * (mm + 2) * (KK + mm) / 6))
Hx = sp.expand(Nsym(n_, x_ * n_) / (x_ * n_))
F = sp.simplify(Hx.coeff(n_, 5)); Gc = sp.simplify(Hx.coeff(n_, 4))
Ft = x_ ** 2 * (1 - x_) ** 2 * (1 + 2 * x_) / 6
Gclaim = (1 - x_) ** 4 / 6 + x_ * (1 - x_) ** 3 / 6 - x_ ** 2 * (1 - x_) ** 2 / 2 + x_ ** 3 * (1 - x_) / 2
al = (1 + sp.sqrt(21)) / 10
gamma = sp.nsimplify(sp.simplify(-sp.diff(Gc, x_).subs(x_, al) / sp.diff(F, x_, 2).subs(x_, al)))
gamma_f = float(sp.N(gamma, 30))
symb = {"F": str(sp.factor(F)), "F_matches_claim": bool(sp.simplify(F - Ft) == 0), "G": str(sp.factor(Gc)),
        "G_matches_C15d835": bool(sp.simplify(Gc - Gclaim) == 0), "Fprime_at_alpha": float(sp.N(sp.diff(F, x_).subs(x_, al))),
        "F_at_alpha": str(sp.nsimplify(sp.simplify(F.subs(x_, al)))), "F_at_alpha_float": float(sp.N(F.subs(x_, al))),
        "gamma_exact": str(gamma), "gamma_float": gamma_f}
# exact continuous optimum for large n
nn, kk = sp.symbols('nn kk', positive=True)
dH = sp.lambdify((nn, kk), sp.diff(Nsym(nn, kk) / kk, kk), 'mpmath')
mpmath.mp.dps = 60
cont = []
for nv in [100, 1000, 10 ** 4, 10 ** 5, 10 ** 6, 10 ** 8]:
    try:
        r = mpmath.findroot(lambda k: dH(mpmath.mpf(nv), k), mpmath.mpf(ALPHA * nv))
        cont.append({"n": nv, "xc_minus_alpha_n": float(r - mpmath.mpf(nv) * (1 + mpmath.sqrt(21)) / 10)})
    except Exception as e:
        cont.append({"n": nv, "error": str(e)})
symb["continuous_optimum_offsets"] = cont
out["symbolic"] = symb

sel = list(range(4, 21)) + [25, 30, 40, 50, 100, 200, 250, 500, 1000] + LARGE
table = []
for n in sel:
    if n in scanres:
        s = scanres[n]
        table.append({"n": n, "kopt": s["kopt"], "kopt_minus_alpha_n": s["kopt"][0] - ALPHA * n,
                      "xc_interp_minus_alpha_n": (s["xc"] - ALPHA * n) if s["xc"] is not None else None,
                      "pred_round_alpha_n_plus_gamma": int(round(ALPHA * n + gamma_f)), "gap_to_second": s["gap_to_second"], "unresolved": s["unresolved"]})
agree = 0; tot = 0; mis = []; ties = []
for n, s in scanres.items():
    if n < 6:
        continue
    tot += 1
    if len(s["kopt"]) > 1:
        ties.append(n)
    if s["kopt"][0] == int(round(ALPHA * n + gamma_f)):
        agree += 1
    else:
        mis.append([n, s["kopt"], ALPHA * n + gamma_f])
xs = [s["xc"] - ALPHA * n for n, s in scanres.items() if s["xc"] is not None and N1 // 2 <= n <= N1]
paper = {20: 11, 25: 14, 50: 28, 100: 56, 250: 140, 500: 279, 1000: 558, 6: 4, 7: 4, 8: 5, 9: 5, 10: 6}
out["partA"] = {"table": table, "n_range_agreement": [6, max(k for k in scanres if k <= N1) if scanres else None], "agree_count": agree, "total": tot,
                "mismatches_first40": mis[:40], "num_mismatches": len(mis), "ties_kopt_nonunique": ties[:40],
                "mean_xc_minus_alpha_n_over_upper_half": (sum(xs) / len(xs)) if xs else None,
                "min_max_xc_minus_alpha_n_upper_half": [min(xs), max(xs)] if xs else None,
                "compare_E_c2afdb": {str(n): [scanres[n]["kopt"], v] for n, v in paper.items() if n in scanres},
                "B_n_exact_small": {str(n): str(scanres[n]["best"]) for n in range(4, 41) if n in scanres}}

# ---------------- Part B: structured families, n<=40 ----------------
fam_out = []
for n in range(4, FAM_NMAX + 1):
    if el() > TB or n not in scanres:
        fam_out.append({"n": n, "status": "skipped_time"}); continue
    Bn = scanres[n]["best"]; Bf = float(Bn)
    graphs = []
    for k in range(3, n):
        for j in range(2, k):
            graphs.append(("PC", [k, j], pc(n, k, j)))
    for k in range(3, n + 1):
        graphs.append(("CM_end", [k], cm(n, k, 'end')))
        if k < n:
            graphs.append(("CM_other", [k], cm(n, k, 'other')))
    for k in range(2, n - 1):
        graphs.append(("TRI", [k], tri(n, k)))
    vals = np.concatenate([ht_batch(np.stack([adjm(n, g[2]) for g in graphs[c0:c0 + 1500]])) for c0 in range(0, len(graphs), 1500)])
    rec = {"n": n, "B_n": str(Bn), "kopt": scanres[n]["kopt"], "families": {}}
    overall = int(np.argmax(vals))
    for fam in ["PC", "CM_end", "CM_other", "TRI"]:
        ids = [i for i, g in enumerate(graphs) if g[0] == fam]
        if not ids:
            continue
        bi = max(ids, key=lambda i: vals[i])
        d = {"count": len(ids), "best_params": graphs[bi][1], "best_float": float(vals[bi]), "gap_float": Bf - float(vals[bi]),
             "rel_gap": (Bf - float(vals[bi])) / Bf, "num_within_1e-9_rel_or_above": int(sum(1 for i in ids if vals[i] >= Bf * (1 - 1e-9)))}
        if (n <= EXACT_ALL_NMAX or bi == overall or d["num_within_1e-9_rel_or_above"] > 0) and el() < TB:
            ex = ht_exact(n, graphs[bi][2]); d["best_exact"] = str(ex); d["gap_exact"] = str(Bn - ex); d["strictly_below"] = bool(ex < Bn)
        rec["families"][fam] = d
    rec["all_strictly_below_float"] = bool(float(vals.max()) < Bf * (1 - 1e-12))
    rec["overall_closest"] = [graphs[overall][0], graphs[overall][1], Bf - float(vals[overall])]
    fam_out.append(rec)
out["partB"] = fam_out

# ---------------- Part C: local search n=11..18 ----------------
def bridge_sides(A):
    G = nx.from_numpy_array(A)
    sides = {}
    for (u, v) in list(nx.bridges(G)):
        e = (min(u, v), max(u, v))
        G.remove_edge(u, v)
        sides[e] = nx.node_connected_component(G, e[0])
        G.add_edge(u, v)
    return sides
def basic_moves(A):
    n = A.shape[0]; E = []; NE = []
    for i in range(n):
        for j in range(i + 1, n):
            (E if A[i, j] else NE).append((i, j))
    sides = bridge_sides(A)
    mv = [((), (f,)) for f in NE] + [((e,), ()) for e in E if e not in sides]
    return mv, E, NE, sides
def swap_moves(E, NE, sides):
    mv = []
    for e in E:
        sd = sides.get(e)
        for f in NE:
            if sd is not None and ((f[0] in sd) == (f[1] in sd)):
                continue
            mv.append(((e,), (f,)))
    return mv
def eval_moves(A, mv):
    B = len(mv)
    Ab = np.repeat(A[None].astype(np.float64), B, axis=0)
    bi = []; ii = []; jj = []; vv = []
    for b, (dl, ad) in enumerate(mv):
        for (i, j) in dl:
            bi.extend((b, b)); ii.extend((i, j)); jj.extend((j, i)); vv.extend((0.0, 0.0))
        for (i, j) in ad:
            bi.extend((b, b)); ii.extend((i, j)); jj.extend((j, i)); vv.extend((1.0, 1.0))
    Ab[bi, ii, jj] = vv
    return ht_batch(Ab), Ab
def make_lidx(n):
    d = {}
    for k in range(2, n + 1):
        E = lolli(n, k); H = nxg(n, E)
        d[len(E)] = (k, sorted(x for _, x in H.degree()), H)
    return d
def is_lolli(A, lidx):
    m = int(A.sum()) // 2
    if m not in lidx:
        return False
    k, ds, H = lidx[m]
    if sorted(A.sum(1).astype(int).tolist()) != ds:
        return False
    return nx.is_isomorphic(nx.from_numpy_array(A.astype(np.uint8)), H)
def track(st, vals, Ab):
    q0 = int(np.argmax(vals))
    if vals[q0] > st['best_val']:
        st['best_val'] = float(vals[q0]); st['best_A'] = (Ab[q0] > 0.5).astype(np.uint8)
    if vals[q0] <= st['nl_val'] + 1e-9:
        return
    for q in np.argsort(-vals)[:6]:
        v = float(vals[q])
        if v <= st['nl_val'] + 1e-9:
            break
        Aq = (Ab[q] > 0.5).astype(np.uint8)
        if not is_lolli(Aq, st['lidx']):
            st['nl_val'] = v; st['nl_A'] = Aq
            if v >= st['Bf'] * (1 - 1e-9) and len(st['ties']) < 20:
                st['ties'].append(edges_of(Aq))
            break
def climb(A, st, deadline):
    cur = float(ht_batch(A[None])[0]); st['evals'] += 1
    track(st, np.array([cur]), A[None].astype(np.float64))
    while time.time() < deadline:
        mv, E, NE, sides = basic_moves(A)
        vals, Ab = eval_moves(A, mv); st['evals'] += len(mv); track(st, vals, Ab)
        q = int(np.argmax(vals))
        if vals[q] > cur * (1 + 1e-12) + 1e-9:
            A = (Ab[q] > 0.5).astype(np.uint8); cur = float(vals[q]); continue
        sm = swap_moves(E, NE, sides)
        bestv = cur; bestA = None
        for c0 in range(0, len(sm), 3000):
            vals, Ab = eval_moves(A, sm[c0:c0 + 3000]); st['evals'] += len(vals); track(st, vals, Ab)
            q = int(np.argmax(vals))
            if vals[q] > bestv * (1 + 1e-12) + 1e-9:
                bestv = float(vals[q]); bestA = (Ab[q] > 0.5).astype(np.uint8)
        if bestA is not None:
            A = bestA; cur = bestv; continue
        break
    return A, cur
def perturb(A, r, rr):
    A = A.copy()
    for _ in range(r):
        mv, E, NE, sides = basic_moves(A)
        if rr.random() < 0.3:
            sm = swap_moves(E, NE, sides)
            if sm:
                mv = sm
        dl, ad = mv[rr.randrange(len(mv))]
        for (i, j) in dl:
            A[i, j] = A[j, i] = 0
        for (i, j) in ad:
            A[i, j] = A[j, i] = 1
    return A
def rand_seed(n, rr):
    t = rr.random()
    if t < 0.4:
        while True:
            G = nx.gnp_random_graph(n, rr.uniform(0.25, 0.4), seed=rr.randint(0, 10 ** 9))
            if nx.is_connected(G):
                return nx.to_numpy_array(G, dtype=np.uint8)
    elif t < 0.75:
        c = rr.randint(max(3, n // 3), max(3, (2 * n) // 3))
        E = [(i, j) for i in range(c) for j in range(i + 1, c)]
        for v in range(c, n):
            E.append((rr.randrange(v), v))
        return adjm(n, E)
    else:
        k = rr.randint(3, n - 2); j = rr.randint(1, k)
        A = adjm(n, pc(n, k, j))
        return perturb(A, rr.randint(1, 4), rr)

ls_out = []
rr = random.Random(SEED)
for idx_n, n in enumerate(LS_N):
    remaining = BUDGET - el() - 4
    if remaining < 1.5:
        ls_out.append({"n": n, "status": "skipped_time"}); continue
    per = remaining / (len(LS_N) - idx_n)
    dl_n = time.time() + per
    vals_l, Bn, ks, _ = scan(n)
    kopt = ks[0]
    st = {'best_val': -1.0, 'best_A': None, 'nl_val': -1.0, 'nl_A': None, 'lidx': make_lidx(n), 'Bf': float(Bn), 'ties': [], 'evals': 0}
    seeds = []
    for k in [kopt, kopt - 1, kopt + 1]:
        if 2 <= k <= n:
            seeds.append(adjm(n, lolli(n, k)))
    for k in range(max(3, kopt - 2), min(n - 1, kopt + 3)):
        for j in sorted(set([2, max(2, k // 2), k - 1])):
            if 2 <= j <= k - 1:
                seeds.append(adjm(n, pc(n, k, j)))
    for k in [kopt, kopt + 1]:
        if 3 <= k <= n:
            seeds.append(adjm(n, cm(n, k, 'end')))
            if k < n:
                seeds.append(adjm(n, cm(n, k, 'other')))
    archive = []; locopt = {}; si = 0; climbs = 0
    while time.time() < dl_n:
        if si < len(seeds):
            A0 = seeds[si]; si += 1
        else:
            u = rr.random()
            if u < 0.35 and archive:
                archive.sort(key=lambda z: -z[0])
                A0 = perturb(archive[rr.randrange(min(5, len(archive)))][1], rr.randint(1, 3), rr)
            elif u < 0.6 and archive:
                A0 = perturb(archive[rr.randrange(len(archive))][1], rr.randint(2, 6), rr)
            else:
                A0 = rand_seed(n, rr)
        A1, v = climb(A0, st, dl_n)
        climbs += 1
        archive.append((v, A1))
        key = round(v, 6)
        if key not in locopt:
            locopt[key] = [0, bool(is_lolli(A1, st['lidx']))]
        locopt[key][0] += 1
        if len(archive) > 200:
            archive.sort(key=lambda z: -z[0]); archive = archive[:100]
    rec = {"n": n, "B_n_exact": str(Bn), "kopt": ks, "climbs": climbs, "evaluations": st['evals']}
    if st['best_A'] is not None:
        bex = ht_exact(n, edges_of(st['best_A']))
        rec["best_found_exact"] = str(bex); rec["best_found_identity"] = identify(n, nx.from_numpy_array(st['best_A']))
        rec["best_found_equals_B_n"] = bool(bex == Bn); rec["best_found_exceeds_B_n"] = bool(bex > Bn)
    if st['nl_A'] is not None:
        ex = ht_exact(n, edges_of(st['nl_A']))
        G = nx.from_numpy_array(st['nl_A'])
        rec["best_non_lollipop"] = {"HT_exact": str(ex), "HT_float": float(ex), "gap_exact": str(Bn - ex), "gap_float": float(Bn - ex),
                                    "rel_gap": float((Bn - ex) / Bn), "identity": identify(n, G), "num_edges": G.number_of_edges(),
                                    "degseq": sorted((d for _, d in G.degree()), reverse=True), "edges": edges_of(st['nl_A']),
                                    "graph6": nx.to_graph6_bytes(G, header=False).decode().strip()}
    rec["non_lollipop_ties_or_beats_float"] = st['ties']
    lo = sorted(locopt.items(), key=lambda z: -z[0])[:10]
    rec["top_local_optima"] = [{"HT_float": k_, "hits": v_[0], "is_lollipop": v_[1]} for k_, v_ in lo]
    rec["num_distinct_local_optima"] = len(locopt)
    ls_out.append(rec)
out["partC"] = ls_out

# ---------------- summary ----------------
bad_fam = [r["n"] for r in fam_out if "families" in r and not r["all_strictly_below_float"]]
exact_fail = [(r["n"], f) for r in fam_out if "families" in r for f, d in r["families"].items() if "strictly_below" in d and not d["strictly_below"]]
ls_s = []
for r in ls_out:
    if "best_non_lollipop" in r:
        ls_s.append(f"n={r['n']}: B_n={float(Fraction(r['B_n_exact'])):.4f} (k={r['kopt']}), best found={r.get('best_found_identity')} eqB={r.get('best_found_equals_B_n')} exceeds={r.get('best_found_exceeds_B_n')}, best non-lolli gap={r['best_non_lollipop']['gap_float']:.4f} [{r['best_non_lollipop']['identity']}], climbs={r['climbs']}, ties/beats={len(r['non_lollipop_ties_or_beats_float'])}")
out["summary"] = (f"Validation: known values {[c['ok'] for c in chk]}, random ok={val['random_direct_vs_montante_vs_float_ok']}, lollipop formula ok={lok}. "
                  f"Part A: gamma=-G'/F''={gamma_f:.6f} (exact {gamma}); G matches C-15d835: {symb['G_matches_C15d835']}; continuous offsets {[(c_['n'], round(c_.get('xc_minus_alpha_n', float('nan')), 5)) for c_ in cont]}; "
                  f"k_opt=round(alpha n+gamma) for {agree}/{tot} n in [6,{N1}], mismatches {mis[:8]}; mean interp offset upper half={out['partA']['mean_xc_minus_alpha_n_over_upper_half']}. "
                  f"Part B (n<=40): n with some family member >= B_n (float): {bad_fam}; exact failures: {exact_fail}. "
                  f"Part C: " + " | ".join(ls_s) + f" | elapsed {el():.1f}s")
json.dump(out, open("result.json", "w"), indent=1, default=str)
