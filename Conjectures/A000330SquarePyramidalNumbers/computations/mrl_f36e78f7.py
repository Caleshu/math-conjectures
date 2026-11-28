# MathResearchLab experiment f36e78f7-3b76-4134-85b2-3df2c1dc2fc3
# Audit the full interval with the signed-divisor test
# sha256(code) = 2dfc297acc9fecda4baee6b34c38054956ca908059dd973f7131deb17d4c6540
# parameters: {"index_bound": 20000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic
import numpy as np

params = json.load(open(os.environ['MRL_PARAMS']))
start = monotonic()
h = params['index_bound']
assert 0 <= h <= 20000

def P(n):
    return n * (n + 1) * (25 * n - 22) // 6

def pairs(c, target):
    x = 25 * c + 1
    D = 3750 * target - 1656 - (x**3 - 553 * x)
    assert 0 < abs(D) < 2**63
    # 2**ceil(bit_length(|D|)/3) is an integer upper bound for its cube root.
    B = max(66, 2 * (1 << ((abs(D).bit_length() + 2) // 3)))
    low, high = (-47, B) if D > 0 else (-B, 47)
    first = low + (2 - low) % 25
    candidates = np.arange(first, high + 1, 25, dtype=np.int64)
    # Only divisibility uses int64. All discriminants and indices use Python integers.
    divisors = candidates[np.remainder(np.int64(D), candidates) == 0]
    hits = []
    for value in divisors:
        s = int(value)
        numerator = 4 * (D // s) - s*s + 2212
        if numerator < 0 or numerator % 3:
            continue
        square = numerator // 3
        d = isqrt(square)
        if d*d != square or (s - d - 2) % 50 or (s + d - 2) % 50:
            continue
        a = (s - d - 2) // 50
        b = (s + d - 2) // 50
        assert a <= b and P(a) + P(b) + P(c) == target
        hits.append([a, b, c])
    return hits, len(divisors)

# Exercise both divisor signs, and the small positive divisor with negative D and d=0.
controls = []
for a, b, c in [(1, 3, -4), (-4, 1, 3), (0, 0, 0)]:
    target = P(a) + P(b) + P(c)
    hits, _ = pairs(c, target)
    assert [a, b, c] in hits
    controls.append({'target': target, 'recovered': [a, b, c]})

witnesses = []
checked = 0
divisors_tested = 0
for c in range(-h, h + 1):
    if monotonic() - start >= 100:
        break
    hits, count = pairs(c, -2)
    witnesses.extend(hits)
    divisors_tested += count
    checked += 1

complete = checked == 2*h + 1
if witnesses:
    summary = 'A verified witness refutes the reported empty list.'
elif complete:
    summary = 'The exhaustive interval audit returned an empty witness list.'
else:
    summary = 'The checked prefix has no witness. The bounded audit is incomplete.'
result = {'summary': summary, 'target': -2, 'requested_interval': [-h, h],
          'complete': complete, 'indices_checked': checked,
          'checked_interval': [-h, -h + checked - 1] if checked else None,
          'signed_divisors_tested': divisors_tested, 'witnesses': witnesses,
          'sanity_controls': controls}
with open('result.json', 'w') as out:
    json.dump(result, out)
