# MathResearchLab experiment 5e06b9f2-82fa-43cc-9404-2a4a9318edd4
# Exhaustive residue test through ten million
# sha256(code) = ce797e50f4a5aaeb4cf3d71df81f258ced9ab48a9f02a6edefb7c08aee9191aa
# parameters: {"m_max": 10000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic

params = json.load(open(os.environ["MRL_PARAMS"]))
limit = params['m_max']
assert 12 <= limit <= 10_000_000
deadline = monotonic() + 85

def residue(m):
    return pow(2, m, m**4 - 1)

# Positive control: 16^4 - 1 = 2^16 - 1. Negative control: 2^12 = 4 mod 11.
assert residue(16) == 1
assert residue(12) % 11 == 4

p_max = limit // 4
prime = bytearray([1]) * (p_max + 1)
prime[:2] = bytes(2)
for q in range(2, isqrt(p_max) + 1):
    if prime[q]:
        start = q*q
        prime[start::q] = bytes((p_max - start) // q + 1)

# Independently check the enumeration on a small prefix by stripping powers of two.
small = min(limit, 2048)
by_m = set()
for m in range(5, small + 1):
    odd = m
    while odd % 2 == 0:
        odd //= 2
    scale = m // odd
    if scale >= 4 and odd >= max(3, scale // 2):
        if all(odd % t for t in range(2, isqrt(odd) + 1)):
            by_m.add(m)

def rows(bound):
    a = 2
    while (1 << (2*a - 1)) <= bound:
        lower = max(3, (1 << (a-1)) + 1)
        yield a, lower, bound >> a
        a += 1

by_p = {p << a for a, lo, hi in rows(small)
        for p in range(lo, hi + 1, 2) if prime[p]}
assert by_m == by_p and 12 in by_p

counts = []
hits = []
complete = True
for a, lo, hi in rows(limit):
    row = {'a': a, 'first_odd_p': lo, 'p_upper_inclusive': hi,
           'last_odd_p_examined': None, 'tested_prime_pairs': 0,
           'pass_minus': 0, 'pass_minus_and_plus': 0, 'pass_full': 0}
    counts.append(row)
    reduced_multiple = (1 << (1 << a)) - 1
    for i, p in enumerate(range(lo, hi + 1, 2)):
        if i % 4096 == 0 and monotonic() >= deadline:
            complete = False
            break
        row['last_odd_p_examined'] = p
        if not prime[p]:
            continue
        m = p << a
        rem = residue(m)
        row['tested_prime_pairs'] += 1
        if rem % (m-1) == 1:
            row['pass_minus'] += 1
            assert reduced_multiple % (m-1) == 0
            assert (m-1) % 3 == 0 and (m-1) % 9 != 0
            if rem % (m+1) == 1:
                row['pass_minus_and_plus'] += 1
                if 'first_passing_both' not in row:
                    row['first_passing_both'] = {'p': p, 'm': m,
                        'residue_mod_m_squared_plus_one': rem % (m*m+1)}
        if rem == 1:
            row['pass_full'] += 1
            hits.append({'a': a, 'p': p, 'm': m, 'modulus': m**4-1, 'residue': rem})
    if not complete:
        break

tested = sum(row['tested_prime_pairs'] for row in counts)
coverage = 'complete' if complete else 'partial at the time cutoff'
result = {'summary': f'Search {coverage}. Tested {tested} eligible pairs and found {len(hits)} counterexamples.',
          'm_max_inclusive': limit, 'complete': complete, 'sanity_prefix_max': small,
          'sanity_prefix_pair_count': len(by_m), 'counts_by_a': counts, 'counterexamples': hits}
with open('result.json', 'w') as out:
    json.dump(result, out)
