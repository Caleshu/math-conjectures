# MathResearchLab experiment 0467fb53-13fc-41ad-a6cd-be7b16b045fb
# Residue-class obstructions mod q<=50 and the set P* for p<=10^5
# sha256(code) = 535502fc30508381db6f17149f4dac6c89c5fb75c098e15adfd05cbf8b05d259
# parameters: {"q_max": 50, "p_max": 100000, "time_limit": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time, itertools
import numpy as np

params = json.load(open(os.environ["MRL_PARAMS"]))
QMAX = int(params.get("q_max", 50))
PMAX = int(params.get("p_max", 100000))
TLIM = float(params.get("time_limit", 95))
t0 = time.time()

def primes_upto(N):
    s = bytearray([1]) * (N + 1)
    s[0] = 0
    if N >= 1:
        s[1] = 0
    i = 2
    while i * i <= N:
        if s[i]:
            s[i*i::i] = bytearray(len(range(i*i, N + 1, i)))
        i += 1
    return [i for i in range(N + 1) if s[i]]

def prime_factors(m):
    out = set(); d = 2
    while d * d <= m:
        while m % d == 0:
            out.add(d); m //= d
        d += 1
    if m > 1:
        out.add(m)
    return out

# ---------- exact derangement numbers + sanity ----------
NMAX = 4 * QMAX + 10
D = [1, 0]
for n in range(2, NMAX + 1):
    D.append(n * D[-1] + (-1) ** n)
D2 = [1, 0]
for n in range(2, NMAX + 1):
    D2.append((n - 1) * (D2[-1] + D2[-2]))
rec_ok = (D == D2)
brute = [sum(1 for s in itertools.permutations(range(n)) if all(s[i] != i for i in range(n))) for n in range(9)]
brute_ok = (brute == D[:9])

# ---------- Part 1 ----------
part1 = {}
residue_count_ok = True
for q in primes_upto(QMAX):
    vals = [D[n] % q for n in range(2 * q)]
    per_ok = all(D[n] % q == vals[n % (2 * q)] for n in range(NMAX + 1))
    anti_ok = all((D[n + q] + D[n]) % q == 0 for n in range(NMAX + 1 - q))
    entry = {"residues_n0_to_2q_minus_1": vals, "periodic_2q_ok": per_ok, "antiperiod_q_ok": anti_ok,
             "zero_classes_mod_2q": [n for n in range(2 * q) if vals[n] == 0], "nonresidue_classes_mod_2q": {}}
    for k in sorted(prime_factors(q - 1)) if q > 2 else []:
        e = (q - 1) // k
        # sanity: number of nonzero k-th power residues must be (q-1)/k
        cnt = sum(1 for r in range(1, q) if pow(r, e, q) == 1)
        if cnt != e:
            residue_count_ok = False
        entry["nonresidue_classes_mod_2q"][str(k)] = [n for n in range(2 * q) if vals[n] != 0 and pow(vals[n], e, q) != 1]
    part1[str(q)] = entry

m7 = part1["7"]["nonresidue_classes_mod_2q"]
table7 = [((-1) ** n * D[n]) % 7 for n in range(7)]
claims = {
    "C-9e6d13_mod7_square_nonres_mod14": {"claimed": [5, 6, 7, 8, 10, 12], "computed": m7["2"],
                                          "match": m7["2"] == [5, 6, 7, 8, 10, 12]},
    "C-9e6d13_mod3_square_nonres_mod6": {"claimed": [3, 5], "computed": part1["3"]["nonresidue_classes_mod_2q"]["2"],
                                         "match": part1["3"]["nonresidue_classes_mod_2q"]["2"] == [3, 5]},
    "C-9e6d13_mod5_square_nonres_mod10": {"claimed": [3, 8], "computed": part1["5"]["nonresidue_classes_mod_2q"]["2"],
                                          "match": part1["5"]["nonresidue_classes_mod_2q"]["2"] == [3, 8]},
    "C-62ce82_mod5_n3mod5_gives_pm2": {"values": [D[n] % 5 for n in (3, 8)],
                                       "match": all(D[n] % 5 in (2, 3) for n in (3, 8))},
    "C-62ce82_mod7_table_(-1)^nD(n)_for_n_mod7": {"claimed": [1, 0, 1, 5, 2, 5, 6], "computed": table7,
                                                 "match": table7 == [1, 0, 1, 5, 2, 5, 6]},
    "C-62ce82_mod7_cube_nonres_mod14": {"claimed": [3, 4, 5, 10, 11, 12], "computed": m7["3"],
                                        "match": m7["3"] == [3, 4, 5, 10, 11, 12]},
    "n=4_class_never_obstructed": all(4 % (2*int(q)) not in v for q, e in part1.items() for v in e["nonresidue_classes_mod_2q"].values()),
}

# ---------- Part 4: vectorised sieve over primes ----------
P = np.array(primes_upto(PMAX), dtype=np.int64)
fact = np.ones_like(P)          # j! mod p
S = np.zeros_like(P)            # sum_{i=1}^{j} i! mod p
Dm = np.ones_like(P) % P        # D(j) mod p ; D(0)=1
lo = 0
j_done = 0
timed_out = False
for j in range(1, PMAX):
    while lo < len(P) and P[lo] <= j:
        lo += 1
    if lo >= len(P):
        break
    Pa = P[lo:]
    f = (fact[lo:] * j) % Pa
    fact[lo:] = f
    S[lo:] = (S[lo:] + f) % Pa
    sgn = 1 if j % 2 == 0 else -1
    Dm[lo:] = (Dm[lo:] * j + sgn) % Pa
    j_done = j
    if (j & 1023) == 0 and time.time() - t0 > TLIM:
        timed_out = True
        break

complete = P <= j_done + 1   # prime p is complete iff p-1 <= j_done
Pc = P[complete]; Sc = S[complete]; Dc = Dm[complete]; Fc = fact[complete]
wilson_ok = bool(np.all(Fc == Pc - 1))
set_S = [int(p) for p, s in zip(Pc, Sc) if s == 0]
set_lf = [int(p) for p, s in zip(Pc, Sc) if (1 + s) % p == 1]   # !p = L_p = 1 + S
set_D = [int(p) for p, d in zip(Pc, Dc) if d == 1]
Deq_lf_odd = all(int(d) == int((1 + s) % p) for p, s, d in zip(Pc, Sc, Dc) if p > 2)
kurepa_zero = [int(p) for p, s in zip(Pc, Sc) if (1 + s) % p == 0]

# pure-python cross-check for p < 3000
py_ok = True
for p in primes_upto(min(3000, int(Pc[-1]) if len(Pc) else 2)):
    f = 1; s = 0; d = 1
    for jj in range(1, p):
        f = f * jj % p; s = (s + f) % p; d = (d * jj + (-1) ** jj) % p
    i = int(np.searchsorted(P, p))
    if not (S[i] == s and Dm[i] == d):
        py_ok = False

spot = {str(p): (p in set_S) for p in (2, 3, 5, 7, 11, 13)}
spot_ok = spot == {"2": False, "3": True, "5": False, "7": False, "11": True, "13": False}

res = {
    "sanity": {"recurrences_agree": rec_ok, "brute_force_n_le_8": brute_ok, "residue_count_ok": residue_count_ok,
               "wilson_ok": wilson_ok, "numpy_vs_python_p_lt_3000": py_ok,
               "kurepa_primes_with_p_divides_!p": kurepa_zero, "spot_C-0c22cb": spot, "spot_ok": spot_ok},
    "part1_by_q": part1,
    "part1_claim_checks": claims,
    "part4": {"p_max_requested": PMAX, "largest_complete_prime": int(Pc[-1]) if len(Pc) else None,
              "timed_out": timed_out, "num_primes_checked": int(len(Pc)),
              "Pstar": set_S, "criteria_sets_equal": (set_S == set_lf == set_D),
              "D(p-1)==!p_mod_p_for_all_odd_p": Deq_lf_odd},
    "elapsed_s": round(time.time() - t0, 2),
}
res["summary"] = (f"Sanity: rec={rec_ok}, brute={brute_ok}, wilson={wilson_ok}, py_xcheck={py_ok}, spot={spot_ok}. "
                  f"Mod-7 square nonres classes mod 14 = {m7['2']} (C-9e6d13 claim match={claims['C-9e6d13_mod7_square_nonres_mod14']['match']}); "
                  f"mod-7 cube classes = {m7['3']} (C-62ce82 match={claims['C-62ce82_mod7_cube_nonres_mod14']['match']}); "
                  f"C-62ce82 table match={claims['C-62ce82_mod7_table_(-1)^nD(n)_for_n_mod7']['match']}. "
                  f"P* up to {res['part4']['largest_complete_prime']}: {set_S}; three criteria equal={res['part4']['criteria_sets_equal']}; "
                  f"Kurepa zero primes={kurepa_zero}; timed_out={timed_out}.")
json.dump(res, open("result.json", "w"))
print(res["summary"])
