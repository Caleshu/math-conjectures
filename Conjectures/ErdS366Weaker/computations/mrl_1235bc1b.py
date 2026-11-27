# MathResearchLab experiment 1235bc1b-28c5-4539-aaa7-f589e87e1d91
# Search small coefficients with cube multipliers up to $10^{60}$
# sha256(code) = 99bf260b4eb06b67e357c935cde12bb16e35697b0c5f9fdeb5ec5e2993b86143
# parameters: {"core_bound": 100000, "root_bound": 1000000000000000000000000000000000000000000000000000000000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import itertools
import json
import math
import os
import time

params = json.load(open(os.environ['MRL_PARAMS']))
core_bound = int(params['core_bound'])
root_bound = int(params['root_bound'])
assert core_bound >= 1 and root_bound >= 1
deadline = time.monotonic() + 85


def icbrt(n):
    low = 0
    high = 1 << ((n.bit_length() + 2) // 3)
    while high - low > 1:
        mid = (low + high) // 2
        if mid**3 <= n:
            low = mid
        else:
            high = mid
    return low if high**3 > n else high


def candidates(A, B, Q):
    scale = 8 * Q**2
    numerator = icbrt(B * scale**3 // A)
    denominator = scale
    p0, p1 = 0, 1
    q0, q1 = 1, 0
    hits = set()
    while denominator:
        term, rem = divmod(numerator, denominator)
        p = term * p1 + p0
        q = term * q1 + q0
        if q > Q:
            break
        if 1 <= p <= Q and abs(A * p**3 - B * q**3) == 1:
            hits.add((p, q))
        numerator, denominator = denominator, rem
        p0, p1 = p1, p
        q0, q1 = q1, q
    return hits


def squarefree(n):
    return all(n % (d*d) for d in range(2, math.isqrt(n) + 1))


# Exercise both signs and a nonintegral convergent with denominator greater than one.
assert (7, 2) in candidates(1, 43, 7)
assert (10, 3) in candidates(1, 37, 10)
check_Q = 12
for A, B in itertools.combinations(range(1, 46), 2):
    expected = {(x, y) for x in range(1, check_Q + 1) for y in range(1, check_Q + 1)
                if abs(A*x**3 - B*y**3) == 1}
    assert candidates(A, B, check_Q) == expected

cores = []
for b in range(1, math.isqrt(math.isqrt(core_bound)) + 1):
    if not squarefree(b):
        continue
    c = 1
    while b**4 * c**5 <= core_bound:
        if squarefree(c) and math.gcd(b, c) == 1:
            cores.append(b**4 * c**5)
        c += 1
cores.sort()
assert len(cores) == len(set(cores))
checked = 0
coprime_checked = 0
last = None
witnesses = []
for A, B in itertools.combinations(cores, 2):
    if time.monotonic() >= deadline:
        break
    if math.gcd(A, B) == 1:
        for x, y in sorted(candidates(A, B, root_bound)):
            left, right = sorted((A*x**3, B*y**3))
            witnesses.append({'pair': [left, right], 'A': A, 'B': B, 'x': x, 'y': y})
        coprime_checked += 1
    checked += 1
    last = [A, B]
total = math.comb(len(cores), 2)
result = {
    'summary': f'Checked {checked} of {total} distinct coefficient pairs and found {len(witnesses)} witnesses.',
    'complete': checked == total,
    'core_bound': core_bound,
    'root_bound': root_bound,
    'cores': cores,
    'coefficient_pairs_checked_in_lexicographic_order': checked,
    'last_checked': last,
    'coprime_pairs_checked_by_convergents': coprime_checked,
    'witnesses': witnesses,
    'sanity_check': {'coefficient_range': [1, 45], 'brute_force_root_bound': check_Q, 'passed': True}
}
with open('result.json', 'w') as f:
    json.dump(result, f)
