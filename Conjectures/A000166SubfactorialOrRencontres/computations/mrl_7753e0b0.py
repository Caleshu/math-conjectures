# MathResearchLab experiment 7753e0b0-6fa2-4c3c-8441-054ba1d263a9
# Exact 3-adic valuations of D_n for n<=5000, the valuation lemma for all p | n-1, and the Kurepa-type congruence
# sha256(code) = a5b10602d93298b7b5e2e0df2ffb02c4e0950cdb4f193ffa88b56726ff021e14
# parameters: {"n_max": 5000, "n_kurepa": 2000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, itertools
from collections import Counter, defaultdict

params = json.load(open(os.environ["MRL_PARAMS"]))
N = int(params.get("n_max", 5000))
NK = int(params.get("n_kurepa", 2000))
t0 = time.time()

D = [1, 0]
for n in range(2, N + 1):
    D.append(n * D[-1] + (-1) ** n)
rec_ok = all(D[n] == (n - 1) * (D[n - 1] + D[n - 2]) for n in range(2, N + 1))
brute = [sum(1 for s in itertools.permutations(range(n)) if all(s[i] != i for i in range(n))) for n in range(9)]
brute_ok = brute == D[:9]

def vp(x, p):
    if x == 0:
        return None
    c = 0
    while x % p == 0:
        x //= p; c += 1
    return c

def factor(m):
    out = {}; d = 2
    while d * d <= m:
        while m % d == 0:
            out[d] = out.get(d, 0) + 1; m //= d
        d += 1
    if m > 1:
        out[m] = out.get(m, 0) + 1
    return out

def primes_upto(M):
    s = bytearray([1]) * (M + 1); s[0] = s[1] = 0
    i = 2
    while i * i <= M:
        if s[i]:
            s[i*i::i] = bytearray(len(range(i*i, M + 1, i)))
        i += 1
    return [i for i in range(M + 1) if s[i]]

# P* for primes < N (direct)
Pstar = set()
for p in primes_upto(N):
    f = 1; s = 0
    for j in range(1, p):
        f = f * j % p; s = (s + f) % p
    if s == 0:
        Pstar.add(p)

# ---------- Part 2: v_3 ----------
tab = Counter()
viol_A = []; viol_B = []; viol_iv = []; viol_55 = []
v3_eq2_detail = []
for n in range(3, N + 1):
    a = vp(n - 1, 3); b = vp(D[n], 3)
    tab[(a, b)] += 1
    sg = (-1) ** n
    if n % 3 != 1 and D[n] % 3 != sg % 3:
        viol_A.append(n)
    if n % 3 == 1 and n % 9 != 1 and D[n] % 27 != (sg * 9) % 27:
        viol_B.append(n)
    if n % 24 in (5, 21):
        if not (vp(D[n], 2) == 2 and D[n] % 3 == 2):
            viol_iv.append(n)
    if a >= 3 and b != a + 2:
        viol_55.append((n, a, b))
    if a == 2:
        v3_eq2_detail.append((n, b))
table = defaultdict(dict)
for (a, b), c in sorted(tab.items()):
    table[str(a)][str(b)] = c

# F_3'(1) = sum_{m>=1} m! in Z_3, truncated: v_3(m!) >= 14 for m >= 30
mod = 3 ** 12
Fp1 = sum(__import__('math').factorial(m) for m in range(1, 31)) % mod
v3_Fp1 = vp(Fp1, 3) if Fp1 else ">=12"

# ---------- valuation lemma for all p | n-1, p not in P* ----------
lemma_viol = []
checks = 0
excess_bad = defaultdict(Counter)
for n in range(3, N + 1):
    for p, e in factor(n - 1).items():
        v = vp(D[n], p)
        if p in Pstar:
            excess_bad[str(p)][str(v - e)] += 1
        else:
            checks += 1
            if v != e:
                lemma_viol.append((n, p, e, v))

# ---------- Part 3: Kurepa-type congruence ----------
kur_viol = []
for n in range(1, NK + 1):
    m = n * n
    lf = 0; f = 1
    for i in range(n):
        if i > 0:
            f = f * i % m
        lf = (lf + f) % m
    if (D[n] - (-1) ** n * (1 - n * lf)) % m != 0:
        kur_viol.append(n)

res = {
    "sanity": {"recurrences_agree_to_N": rec_ok, "brute_force_n_le_8": brute_ok,
               "D4_is_9": D[4] == 9, "Pstar_contains_3_and_11": (3 in Pstar and 11 in Pstar),
               "Pstar_excludes_2_5_7_13": not any(p in Pstar for p in (2, 5, 7, 13))},
    "Pstar_below_N": sorted(Pstar),
    "v3_table_rows_v3(n-1)_cols_v3(D_n)": table,
    "C-f782d1": {"A_mod3_violations": viol_A[:50], "num_A": len(viol_A),
                 "B_mod27_violations": viol_B[:50], "num_B": len(viol_B),
                 "iv_n_5_21_mod24_violations": viol_iv[:50], "num_iv": len(viol_iv)},
    "C-55c254": {"violations_v3ge3": viol_55[:50], "num": len(viol_55),
                 "v3_of_F3prime(1)_mod_3^12": v3_Fp1,
                 "v3(n-1)=2_cases_(n,v3(D))": v3_eq2_detail[:80]},
    "valuation_lemma_good_primes": {"pairs_checked": checks, "violations": lemma_viol[:50], "num": len(lemma_viol),
                                    "bad_prime_excess_v_p(D)-v_p(n-1)": {k: dict(v) for k, v in excess_bad.items()}},
    "C-7add77_kurepa": {"n_range": [1, NK], "violations": kur_viol[:50], "num": len(kur_viol)},
    "elapsed_s": round(time.time() - t0, 2),
}
res["summary"] = (f"N={N}. Sanity rec={rec_ok}, brute={brute_ok}. v3 table={dict(table)}. "
                  f"C-f782d1 violations: A={len(viol_A)}, B={len(viol_B)}, iv={len(viol_iv)}. "
                  f"C-55c254 (v3(n-1)>=3) violations={len(viol_55)}; v3(F3'(1))={v3_Fp1}. "
                  f"Good-prime valuation lemma: {checks} pairs, {len(lemma_viol)} violations. "
                  f"Kurepa congruence n<={NK}: {len(kur_viol)} violations. P* below N: {sorted(Pstar)}.")
json.dump(res, open("result.json", "w"), default=str)
print(res["summary"])
