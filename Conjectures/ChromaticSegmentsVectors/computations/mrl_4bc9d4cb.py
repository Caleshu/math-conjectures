# MathResearchLab experiment 4bc9d4cb-e558-4eba-b529-71d303d0d0c9
# Exhaustive chromatic-segment vectors of Q_n, n<=4, vs. necessary conditions C1-C4
# sha256(code) = 1ae63127f91e3441e2d4d0bdca0bffd898a31230d015c4ce78eab74365b45a53
# parameters: {"n_max": 4}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, sys
sys.setrecursionlimit(10000)
params = json.load(open(os.environ["MRL_PARAMS"]))
nmax = params.get("n_max", 4)
t0 = time.time()

def ham_cycles(n):
    N = 1 << n
    res = []
    path = [0]; used = [False]*N; used[0] = True
    def dfs():
        v = path[-1]
        if len(path) == N:
            if bin(v).count('1') == 1 and path[1] < path[-1]:
                res.append(tuple(path))
            return
        for b in range(n):
            u = v ^ (1 << b)
            if not used[u]:
                used[u] = True; path.append(u); dfs(); path.pop(); used[u] = False
    dfs()
    return res

def normalized_deltas(h, i):
    N = len(h); out = set()
    for seq in (h, h[::-1]):
        for s in range(N):
            g = seq[s:] + seq[:s]
            if (g[0] >> i) & 1 == 0 and g[1] == g[0] ^ (1 << i):
                js = [j for j in range(N) if g[j] ^ g[(j+1) % N] == (1 << i)]
                assert js[0] == 0
                d = tuple(js[k+1]-js[k] for k in range(len(js)-1)) + (N - js[-1],)
                out.add(d)
    return out

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

def canon(d):
    return min(orbit(d))

def weak_candidates(n):
    H = 1 << (n-1)
    A = list(comps(H))
    W = set()
    for a in A:
        for b in A:
            if len(a) == len(b):
                d = []
                for x, y in zip(a, b):
                    d += [x, y]
                W.add(tuple(d))
    return W

expected_counts = {2: 1, 3: 6, 4: 1344}
results = {}
all_ok = True
for n in range(2, nmax+1):
    cyc = ham_cycles(n)
    N = 1 << n
    R_by_i = []
    for i in range(n):
        R = set()
        for h in cyc:
            R |= normalized_deltas(h, i)
        R_by_i.append(R)
    R = R_by_i[0]
    same_all_i = all(Ri == R for Ri in R_by_i)
    closed = all(set(orbit(d)) <= R for d in R)
    W = weak_candidates(n)
    S = {d for d in W if color_balanced(d)}
    # direct checks of necessary conditions on realized lists
    c1 = all(len(d) % 2 == 0 and len(d) >= 2 for d in R)
    c2 = all(min(d) >= 2 for d in R)
    c3 = all(sum(d[0::2]) == N//2 and sum(d[1::2]) == N//2 for d in R)
    c4 = all(color_balanced(d) for d in R)
    R_minus_S = sorted(R - S)
    S_minus_R = sorted(S - R)
    canonR = sorted({canon(d) for d in R})
    canonS_minus_R = sorted({canon(d) for d in S_minus_R})
    canonW_minus_S = sorted({canon(d) for d in W - S})
    by_c = {}
    for d in canonR:
        by_c[len(d)] = by_c.get(len(d), 0) + 1
    count_ok = (len(cyc) == expected_counts.get(n, len(cyc)))
    all_ok &= count_ok
    results[str(n)] = {
        "num_undirected_ham_cycles": len(cyc),
        "count_matches_known": count_ok,
        "same_image_for_all_i": same_all_i,
        "image_closed_under_normalization_group": closed,
        "num_realized_raw": len(R), "num_weak_raw": len(W), "num_C1to4_raw": len(S),
        "realized_satisfy": {"C1": c1, "C2": c2, "C3": c3, "C4": c4},
        "R_minus_S": R_minus_S,
        "S_minus_R_canonical": canonS_minus_R,
        "R_equals_S": (R == S),
        "canonical_realized": canonR,
        "canonical_realized_count_by_c": by_c,
        "canonical_weak_but_not_C4": canonW_minus_S,
        "elapsed": time.time() - t0,
    }

summ = []
for n, r in results.items():
    summ.append(f"n={n}: cycles={r['num_undirected_ham_cycles']} (known ok={r['count_matches_known']}), |R|={r['num_realized_raw']}, |S(C1-4)|={r['num_C1to4_raw']}, |W(C1-3)|={r['num_weak_raw']}, R==S: {r['R_equals_S']}, R-S empty: {len(r['R_minus_S'])==0}, closed: {r['image_closed_under_normalization_group']}, same all i: {r['same_image_for_all_i']}, #canon S\\R={len(r['S_minus_R_canonical'])}")
out = {"summary": " | ".join(summ), "sanity_counts_ok": all_ok, "results": results}
json.dump(out, open("result.json", "w"), indent=1)
print(out["summary"])
