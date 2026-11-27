# MathResearchLab experiment 97939b80-1277-4eeb-bb4a-67c3b3594ee8
# Exact alpha_=(Q_n) via reduction to Q_{n-1} and Harper's simplicial order, with brute-force check of the isoperimetric step for small n
# sha256(code) = e1bfceb70a3c0623dc555604b7424afa5e26fae33e6770e09dcb475b8cecd07b
# parameters: {"n_max": 20, "verify_n_max": 16, "brute_m_max": 4}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, itertools, time, math
params = json.load(open(os.environ["MRL_PARAMS"]))
n_max = params.get("n_max", 20)
verify_n_max = params.get("verify_n_max", 16)
brute_m_max = params.get("brute_m_max", 4)
t0 = time.time()

def simplicial_order(m):
    order = []
    for w in range(m + 1):
        for c in itertools.combinations(range(m), w):  # lex order of sorted tuples = simplicial order within a level
            mask = 0
            for i in c:
                mask |= 1 << i
            order.append(mask)
    return order

def harper_profile(m):
    N = 1 << m
    order = simplicial_order(m)
    covered = bytearray(N)
    cnt = 0
    f = [0]
    bits = [1 << i for i in range(m)]
    for v in order:
        if not covered[v]:
            covered[v] = 1; cnt += 1
        for b in bits:
            u = v ^ b
            if not covered[u]:
                covered[u] = 1; cnt += 1
        f.append(cnt)
    return order, f

def popc(x):
    return bin(x).count("1")

results = {}
brute = {}
sanity_ok = True

# Exhaustive check of isoperimetric profile and balanced problem for small m
for m in range(1, brute_m_max + 1):
    N = 1 << m
    nb = []
    for v in range(N):
        s = 1 << v
        for i in range(m):
            s |= 1 << (v ^ (1 << i))
        nb.append(s)
    minN = [None] * (N + 1)
    best_bal = 0
    for S in range(1 << N):
        cl = 0; k = 0; x = S; v = 0
        while x:
            if x & 1:
                cl |= nb[v]; k += 1
            x >>= 1; v += 1
        c = popc(cl)
        if minN[k] is None or c < minN[k]:
            minN[k] = c
        bal = min(k, N - c)
        if bal > best_bal:
            best_bal = bal
    order, f = harper_profile(m)
    match = all(minN[k] == f[k] for k in range(N + 1))
    Kh = max(k for k in range(N + 1) if f[k] + k <= N)
    brute[m] = {"n": m + 1, "bruteforce_minN": minN, "harper_f": f, "profile_match": match,
                "bruteforce_k": best_bal, "harper_k": Kh, "alpha_eq_bruteforce": 2 * best_bal}
    if not match or best_bal != Kh:
        sanity_ok = False

for n in range(2, n_max + 1):
    if time.time() - t0 > 90:
        results[n] = "skipped_time"
        break
    m = n - 1
    N = 1 << m
    order, f = harper_profile(m)
    K = 0
    for k in range(N + 1):
        if f[k] + k <= N:
            K = k
        else:
            break
    entry = {"K": K, "alpha_eq": 2 * K, "f_K": f[K], "2^(n-1)": N,
             "approx_2^(n-1)-binom(n-1,floor((n-1)/2))": N - math.comb(m, m // 2),
             "ratio_alpha_eq_over_2^(n-1)": 2 * K / N,
             "deficit_2^(n-1)-alpha_eq": N - 2 * K,
             "deficit_over_2^n/sqrt(n)": (N - 2 * K) / (2 ** n / math.sqrt(n))}
    if n <= verify_n_max:
        A = order[:K]
        # recompute N[A]
        cov = bytearray(N)
        for v in A:
            cov[v] = 1
            for i in range(m):
                cov[v ^ (1 << i)] = 1
        B = [z for z in range(N) if not cov[z]][:K]
        ok_sizes = (len(A) == K and len(B) == K)
        # map into Q_n: even vertex from y: y | (par(y)<<m); odd vertex from z: z | ((par(z)^1)<<m)
        S = set()
        for y in A:
            S.add(y | ((popc(y) & 1) << m))
        for z in B:
            S.add(z | (((popc(z) & 1) ^ 1) << m))
        ev = sum(1 for x in S if popc(x) % 2 == 0)
        od = len(S) - ev
        indep = all((x ^ (1 << i)) not in S for x in S for i in range(n))
        entry["construction_verified"] = bool(ok_sizes and indep and ev == K and od == K and len(S) == 2 * K)
        if n == 7:
            # also check the explicit weight-layer construction {even w in {0,2}} u {odd w in {5,7}}
            S7 = [x for x in range(128) if popc(x) in (0, 2, 5, 7)]
            S7s = set(S7)
            entry["layer_construction_Q7_size"] = len(S7)
            entry["layer_construction_Q7_independent"] = all((x ^ (1 << i)) not in S7s for x in S7 for i in range(7))
            entry["layer_construction_Q7_even_odd"] = [sum(1 for x in S7 if popc(x) % 2 == 0), sum(1 for x in S7 if popc(x) % 2 == 1)]
        if not entry["construction_verified"]:
            sanity_ok = False
    results[n] = entry

recorded = {3: 2, 4: 4, 5: 10, 6: 16, 7: 40}
cmp = {n: {"recorded": recorded[n], "computed": results[n]["alpha_eq"]} for n in recorded if isinstance(results.get(n), dict)}
summary = ("Harper-based alpha_=(Q_n) for n=2..%d: " % n_max) + ", ".join(
    "n=%d:%s" % (n, results[n]["alpha_eq"] if isinstance(results[n], dict) else results[n]) for n in sorted(results)) + \
    ". Sanity (brute-force profile match for m<=%d and constructions verified): %s. Comparison with recorded: %s" % (brute_m_max, sanity_ok, cmp)
json.dump({"summary": summary, "sanity_ok": sanity_ok, "bruteforce_small": brute, "results": results,
           "comparison_with_recorded": cmp, "elapsed_s": time.time() - t0}, open("result.json", "w"), indent=1, default=str)
