# MathResearchLab experiment c8b4e4e9-3cc1-4ee6-8a29-c942f2085240
# Least index bound for signed integer targets
# sha256(code) = 4dce2a1ae3925fbb14ea48b53b8350adfdd739289c8f577dff572b1344d8fddd
# parameters: {"r_values": [3, 4, 5, 6, 7, 8, 12, 24, 100, 1009], "index_bound": 192, "target_bound": 300}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from bisect import bisect_left, bisect_right
from collections import Counter
from itertools import product
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
N, Z = params['index_bound'], params['target_bound']
r_values = params['r_values']
assert N >= 1 and Z >= 0 and all(r >= 3 for r in r_values)
deadline = monotonic() + 85

def pyramidal(r, n):
    return (r - 2) * ((n + 1) * n * (n - 1) // 6) + n * (n + 1) // 2

def polygonal(r, n):
    return n + (r - 2) * n * (n - 1) // 2

def search(r, bound, target_bound):
    # Equal summand values are interchangeable. Keep a least-cost index for each.
    representative = {}
    for n in range(-bound, bound + 1):
        v = pyramidal(r, n)
        if v not in representative or abs(n) < abs(representative[v]):
            representative[v] = n
    values = sorted(representative)
    indices = [representative[v] for v in values]
    best = {}
    for i, x in enumerate(values):
        for j in range(i, len(values)):
            pair = x + values[j]
            if pair + values[j] > target_bound:
                break
            lo = bisect_left(values, -target_bound - pair, j)
            hi = bisect_right(values, target_bound - pair, lo)
            pair_cost = max(abs(indices[i]), abs(indices[j]))
            for k in range(lo, hi):
                z = pair + values[k]
                cost = max(pair_cost, abs(indices[k]))
                if z not in best or cost < best[z][0]:
                    best[z] = (cost, (indices[i], indices[j], indices[k]))
    return best

def consecutive_ranges(numbers):
    ranges = []
    for n in numbers:
        if ranges and ranges[-1][1] + 1 == n:
            ranges[-1][1] = n
        else:
            ranges.append([n, n])
    return ranges

rows = []
for r in r_values:
    if monotonic() >= deadline:
        break
    # Independent values from P(0)=0 and the first-difference recurrence.
    direct = {0: 0}
    for n in range(1, N + 1):
        direct[n] = direct[n - 1] + polygonal(r, n)
    for n in range(-1, -N - 1, -1):
        direct[n] = direct[n + 1] - polygonal(r, n + 1)
    assert all(pyramidal(r, n) == v for n, v in direct.items())
    small = min(N, 4)
    brute = {}
    for triple in product(range(-small, small + 1), repeat=3):
        z = sum(direct[n] for n in triple)
        if abs(z) <= Z:
            cost = max(map(abs, triple))
            brute[z] = min(brute.get(z, cost), cost)
    assert brute == {z: rec[0] for z, rec in search(r, small, Z).items()}
    best = search(r, N, Z)
    assert all(sum(direct[n] for n in t) == z and max(map(abs, t)) == cost for z, (cost, t) in best.items())
    targets = range(-Z, Z + 1)
    missing = [z for z in targets if z not in best]
    largest = max(cost for cost, _ in best.values())
    hardest = [z for z in targets if z in best and best[z][0] == largest]
    examples = sorted(set(hardest[:4] + hardest[-4:] + [z for z in (-1, 0, 1) if z in best]))
    rows.append({'r': r, 'represented': len(best), 'missing_ranges_inclusive': consecutive_ranges(missing), 'least_bounds_in_target_order': [best[z][0] if z in best else None for z in targets], 'least_bound_histogram': dict(sorted(Counter(rec[0] for rec in best.values()).items())), 'largest_finite_bound_found': largest, 'sample_witnesses': [{'z': z, 'indices': best[z][1]} for z in examples]})

result = {'summary': f'Completed exhaustive index boxes for {len(rows)} of {len(r_values)} requested r values. Least-bound arrays run from -Z through Z. Null means the box contains no witness.', 'parameters': params, 'completed_all': len(rows) == len(r_values), 'sanity_checks': 'For each completed r, checked the signed recurrence, compared least bounds with a small ordered-triple enumeration, and verified every retained witness.', 'rows': rows}
with open('result.json', 'w') as out:
    json.dump(result, out)
