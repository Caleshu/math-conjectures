# MathResearchLab experiment 4c3722d4-ff13-4e60-ae01-5a46cb534d45
# Measure Lucas entry indices and all hit residues modulo prime powers
# sha256(code) = 2707b54384fad9806fd656f48d04be69172ba4953f67ac3563394030b81b7228
# parameters: {"prime_bound": 100, "modulus_bound": 2000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt, lcm
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
P, Q = int(params['prime_bound']), int(params['modulus_bound'])
assert 2 <= P <= 500 and 2 <= Q <= 10000
deadline = monotonic() + 70

def lucas_cycle(q):
    start = (2 % q, 1)
    a, b = start
    hits = []
    n = 0
    while True:
        if a == 0:
            hits.append(n)
        a, b = b, (a+b) % q
        n += 1
        if (a, b) == start:
            return n, hits
        if n % 2048 == 0 and monotonic() >= deadline:
            return None

def exact_lucas(n):
    a, b = 2, 1
    for _ in range(n):
        a, b = b, a+b
    return a

def valuation(x, p):
    v = 0
    while x % p == 0:
        x //= p
        v += 1
    return v

assert lucas_cycle(2) == (3, [0])
assert lucas_cycle(4) == (6, [3])
assert exact_lucas(4) == 7 and valuation(exact_lucas(3), 2) == 2
cases = []
for p in range(2, min(P, Q)+1):
    if any(p % d == 0 for d in range(2, isqrt(p)+1)):
        continue
    m, q = 1, p
    while q <= Q:
        cases.append((p, m, q))
        m, q = m+1, q*p

rows, mismatches = [], []
base = {}
for p, m, q in cases:
    if monotonic() >= deadline:
        break
    cycle = lucas_cycle(q)
    if cycle is None:
        break
    period, hits = cycle
    entry = min((h if h > 0 else period for h in hits), default=None)
    if m == 1:
        base[p] = (entry, valuation(exact_lucas(entry), p) if entry is not None else None)
    e, v = base[p]
    predicted_entry = None
    # Represent each nonempty prediction as a single residue modulo a step.
    residue, step = None, 1
    if p == 2:
        if m == 1:
            predicted_entry, residue, step = 3, 0, 3
        elif m == 2:
            predicted_entry, residue, step = 3, 3, 6
    elif e is not None:
        predicted_entry = e * p**max(0, m-v)
        residue, step = predicted_entry, 2*predicted_entry
    # Compare whole periodic sets. A shared hit requires step to divide
    # the observed period for equality with one predicted residue class.
    if residue is None:
        same_set = not hits
    else:
        same_set = period % step == 0 and hits == list(range(residue, period, step))
    if entry != predicted_entry or not same_set:
        mismatches.append(q)
    rows.append({'p': p, 'm': m, 'modulus': q, 'least_period': period, 'zero_residues': hits, 'first_positive_hit': entry, 'base_entry_valuation': v, 'predicted_entry': predicted_entry, 'predicted_residue': residue, 'predicted_step': step if residue is not None else None, 'matches': same_set and entry == predicted_entry})

result = {'summary': f'Completed {len(rows)} of {len(cases)} prime-power cycles. Each completed residue list describes every index for its modulus by periodicity.', 'complete': len(rows) == len(cases), 'mismatching_moduli': mismatches, 'rows': rows}
with open('result.json', 'w') as out:
    json.dump(result, out)
