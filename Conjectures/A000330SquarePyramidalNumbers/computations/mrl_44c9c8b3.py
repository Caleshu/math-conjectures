# MathResearchLab experiment 44c9c8b3-a2ff-4a77-ae8d-64c8216bbbc6
# Audit every admissible signed divisor across the full interval
# sha256(code) = 757468005fbb65f46e8261c5506c11d6c6c941c5f5e8821f9e13a9ba55030a65
# parameters: {"c_min": -20000, "c_max": 20000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic
import numpy as np

params = json.load(open(os.environ["MRL_PARAMS"]))
deadline = monotonic() + 105

def P(n):
    return n * (n + 1) * (25 * n - 22) // 6

def f(x):
    return x**3 - 553 * x

def scan(indices, target):
    constant = 3750 * target - 1656
    raw = [constant - f(25 * c + 1) for c in indices]
    assert max(map(abs, raw)) < 2**63 - 1
    values = np.array(raw, dtype=np.int64)
    through = {}
    divisor_pairs = 0
    witnesses = []
    for sign, first in [(1, 2), (-1, 23)]:
        oriented = sign * values
        order = np.argsort(oriented)
        ordered = oriented[order]
        maximum = int(ordered[-1])
        m = first
        while True:
            # With s = sign*m, a real difference requires sign*D >= lower.
            lower = (m * (m*m - 2212) + 3) // 4
            if m >= 48 and lower > maximum:
                through[str(sign)] = 'exhausted'
                break
            if monotonic() >= deadline:
                return False, through, divisor_pairs, witnesses
            start = int(ordered.searchsorted(lower))
            tail = ordered[start:]
            s = sign * m
            for offset in np.flatnonzero(tail % m == 0):
                j = start + int(offset)
                divisor_pairs += 1
                q = 4 * (int(ordered[j]) // m) - m*m + 2212
                assert q >= 0
                if q % 3:
                    continue
                d = isqrt(q // 3)
                if 3*d*d != q or (s+d-2) % 50 or (s-d-2) % 50:
                    continue
                a, b = (s+d-2) // 50, (s-d-2) // 50
                c = indices[int(order[j])]
                assert P(a) + P(b) + P(c) == target
                witnesses.append({'a': a, 'b': b, 'c': c, 's': s, 'd': d})
            through[str(sign)] = m
            m += 25
    return True, through, divisor_pairs, witnesses

# Planted pairs exercise a negative divisor, an equal-index pair, and s*D < 0.
sanity = []
for a, b, c in [(1, -2, 3), (1, 1, -1), (0, 0, 2)]:
    target = P(a) + P(b) + P(c)
    complete, _, _, hits = scan([c], target)
    assert complete and any((h['a'], h['b'], h['c']) == (a, b, c) for h in hits)
    sanity.append([a, b, c, target])

lo, hi = params['c_min'], params['c_max']
assert (lo, hi) == (-20000, 20000)
complete, through, pairs, hits = scan(range(lo, hi+1), -2)
if hits:
    summary = 'No. At least one bounded c extends to an integer representation.'
elif complete:
    summary = 'Yes. All 40001 bounded indices are rejected with the other two indices unrestricted.'
else:
    summary = 'Partial scan without a witness. The bounded exclusion is undecided.'
result = {'summary': summary, 'r': 27, 'target': -2, 'c_interval': [lo, hi],
          'complete': complete, 'last_completed_divisor_magnitude_by_sign': through,
          'divisible_pairs_passing_size_bound': pairs, 'witnesses': hits,
          'sanity_triples_and_targets': sanity}
with open('result.json', 'w') as out:
    json.dump(result, out)
