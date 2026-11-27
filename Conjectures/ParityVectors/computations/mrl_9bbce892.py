# MathResearchLab experiment 9bbce892-3d31-4f29-91e4-a1ee134c21ef
# Exhaustive parity vectors of all Hamiltonian cycles of Q_n, n<=4
# sha256(code) = 6d4d34a9cee875821e3d3879b8ea2271ff3bf1d6ebb67a21e1f567f52beb6d7b
# parameters: {"n_max": 4}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from itertools import combinations
params = json.load(open(os.environ["MRL_PARAMS"]))
NMAX = params.get("n_max", 4)
T0 = time.time()

def popc(x): return bin(x).count("1")
def par_in(u, i): return popc(u & ~(1 << i)) & 1

def ham_cycles(n):
    N = 1 << n
    res = []
    path = [0]
    vis = [False]*N; vis[0] = True
    def dfs(u):
        if len(path) == N:
            if popc(u) == 1 and path[1] < path[-1]:
                res.append(list(path))
            return
        for d in range(n):
            w = u ^ (1 << d)
            if not vis[w]:
                vis[w] = True; path.append(w)
                dfs(w)
                path.pop(); vis[w] = False
    dfs(0)
    return res

def normalizations(h, i):
    N = len(h); out = []
    for l in range(N):
        a = h[l]; b = h[(l+1) % N]
        if a ^ b == (1 << i):
            if (a >> i) & 1 == 0:
                hp = [h[(l+t) % N] for t in range(N)]
            else:
                hp = [h[(l+1-t) % N] for t in range(N)]
            out.append(hp)
    return out

def beta(hp, i):
    N = len(hp)
    assert hp[0] ^ hp[1] == (1 << i) and (hp[0] >> i) & 1 == 0
    js = [l for l in range(N) if hp[l] ^ hp[(l+1) % N] == (1 << i)]
    b = [par_in(hp[0], i)]
    for t in range(1, len(js)):
        b.append((b[-1] + js[t] - js[t-1] + 1) % 2)
    direct = [par_in(hp[j], i) for j in js]
    assert b == direct, (b, direct)
    # side check: tail of m-th i-edge on side m mod 2
    for m, j in enumerate(js):
        assert (hp[j] >> i) & 1 == m % 2
    return tuple(b)

def conds(v, n):
    k = len(v)
    s0 = [0, 0]; s1 = [0, 0]; df = [0, 0]
    for m in range(k):
        s = m % 2
        a, b = v[m-1], v[m]
        if a == b:
            (s0 if b == 0 else s1)[s] += 1
        else:
            df[s] += 1
    A = (sum(v) * 2 == k)
    B = all(s0[s] == s1[s] for s in (0, 1))
    C = all(3*(s0[s]+s1[s]) + 2*df[s] <= (1 << (n-1)) for s in (0, 1))
    return A, B, C

def balanced(k):
    out = []
    for ones in combinations(range(k), k//2):
        v = [0]*k
        for o in ones: v[o] = 1
        out.append(tuple(v))
    return out

def rots(v):
    return {tuple(v[r:] + v[:r]) for r in range(len(v))}

s = lambda v: "".join(map(str, v))
results = {}
known_counts = {2: 1, 3: 6, 4: 1344}
for n in range(2, NMAX+1):
    hc = ham_cycles(n)
    achieved = {}
    ck_seen = set()
    for h in hc:
        for i in range(n):
            for hp in normalizations(h, i):
                v = beta(hp, i)
                achieved.setdefault(len(v), set()).add(v)
                ck_seen.add(len(v))
    per_k = {}
    for k in range(2, (1 << (n-1)) + 1, 2):
        bal = set(balanced(k))
        ach = achieved.get(k, set())
        abc = {v for v in bal if all(conds(v, n))}
        bal_failB = [v for v in bal if not conds(v, n)[1]]
        ach_rot = set()
        for v in ach: ach_rot |= rots(list(v))
        missing = sorted(bal - ach)
        closed_rot2 = all(tuple(v[2:] + v[:2]) in ach for v in ach)
        closed_comp = all(tuple(1-x for x in v) in ach for v in ach)
        per_k[k] = {
            "num_balanced": len(bal),
            "num_achieved": len(ach),
            "achieved_not_balanced": [s(v) for v in sorted(ach - bal)],
            "num_balanced_not_achieved": len(missing),
            "examples_balanced_not_achieved": [s(v) for v in missing[:12]],
            "num_balanced_not_achieved_even_up_to_rotation": len(bal - ach_rot),
            "num_satisfying_ABC": len(abc),
            "achieved_equals_ABC": ach == abc,
            "ABC_not_achieved": [s(v) for v in sorted(abc - ach)][:20],
            "achieved_not_ABC": [s(v) for v in sorted(ach - abc)][:20],
            "num_balanced_failing_B": len(bal_failB),
            "examples_failing_B": [s(v) for v in sorted(bal_failB)[:6]],
            "achieved_closed_under_rot2": closed_rot2,
            "achieved_closed_under_complement": closed_comp,
            "achieved_list": [s(v) for v in sorted(ach)] if len(ach) <= 80 else "omitted",
        }
    results[n] = {
        "num_ham_cycles_undirected": len(hc),
        "sanity_count_matches_known": known_counts.get(n) == len(hc),
        "every_even_k_occurs_as_c_i": all(k in ck_seen for k in range(2, (1 << (n-1)) + 1, 2)),
        "c_i_values_seen": sorted(ck_seen),
        "per_k": per_k,
    }

lines = []
for n, r in results.items():
    for k, d in r["per_k"].items():
        lines.append(f"n={n},k={k}: bal={d['num_balanced']} ach={d['num_achieved']} missing={d['num_balanced_not_achieved']} (up to rot {d['num_balanced_not_achieved_even_up_to_rotation']}) ach==ABC:{d['achieved_equals_ABC']} nonbal_ach={len(d['achieved_not_balanced'])}")
summary = "Exhaustive enumeration. " + " | ".join(lines) + f" | time {time.time()-T0:.1f}s"
json.dump({"summary": summary, "results": results}, open("result.json", "w"), indent=1)
print(summary)
