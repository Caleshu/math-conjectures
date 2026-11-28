# MathResearchLab experiment af634e25-6c36-480c-97c0-8da07d1a37e4
# Verify the small-index exclusion with the other two indices unrestricted
# sha256(code) = 2fe3235cd45433a72280a274cbf8d54432feffae84c4039d9dd34f04788fb27e
# parameters: {"small_index_bound": 20000, "seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic
import numpy as np

params = json.load(open(os.environ['MRL_PARAMS']))
H = int(params['small_index_bound'])
assert 0 <= H <= 20000
started = monotonic()
deadline = started + min(100.0, float(params['seconds']))

def P(n):
    return (25*n**3 + 3*n*n - 22*n) // 6

def f(x):
    return x**3 - 553*x

def bound(D):
    # This power of two is at least the cube root of |D|.
    upper_root = 1 << ((abs(D).bit_length() + 2) // 3)
    return max(67, 2*upper_root)

T = 25*max(H, 10) + 1
max_D = T**3 + 553*T + 9156
assert max_D < 2**63 - 1
limit = bound(max_D)
positive = np.arange(2, limit + 1, 25, dtype=np.int64)
negative = -np.arange(23, limit + 1, 25, dtype=np.int64)

def pairs(D):
    assert D != 0 and abs(D) <= max_D
    same_sign = positive if D > 0 else negative
    opposite_small = [-23] if D > 0 else [2, 27]
    # A prefix may include one extra candidate beyond the proven bound.
    candidates = same_sign[:bound(D)//25 + 1]
    divisors = candidates[np.remainder(D, candidates) == 0].tolist()
    divisors.extend(s for s in opposite_small if D % s == 0)
    answer = []
    for s in divisors:
        three_d_squared = 4*(D//s) - s*s + 2212
        if three_d_squared < 0 or three_d_squared % 3:
            continue
        d_squared = three_d_squared // 3
        d = isqrt(d_squared)
        if d*d != d_squared or (s+d-2) % 50 or (s-d-2) % 50:
            continue
        a, b = (s+d-2)//50, (s-d-2)//50
        assert f(25*a+1) + f(25*b+1) == D
        answer.append((a, b))
    return answer

# Planted pairs exercise both signs of s, repeated indices, and cancellation.
sanities = 0
for a in range(-5, 6):
    for b in range(-5, a+1):
        D = f(25*a+1) + f(25*b+1)
        assert (a, b) in pairs(D)
        assert 3750*P(a) == f(25*a+1) + 552
        sanities += 1

checked = 0
witness = None
for c in range(-H, H+1):
    if monotonic() >= deadline:
        break
    D = -9156 - f(25*c+1)
    assert D % 25 == 21
    extensions = pairs(D)
    checked += 1
    if extensions:
        a, b = extensions[0]
        assert P(a) + P(b) + P(c) == -2
        witness = [a, b, c]
        break

complete = checked == 2*H+1
if witness is not None:
    summary = 'A verified small-index representation proves the conditional lemma.'
elif complete:
    summary = 'The entire small-index interval is excluded, with both other indices unrestricted.'
else:
    summary = 'Partial exclusion only. The time budget ended before the interval was exhausted.'
result = {'summary': summary, 'r': 27, 'target': -2, 'requested_c_interval': [-H, H], 'checked_c_interval': [-H, -H+checked-1] if checked else None, 'checked_c_count': checked, 'interval_exhausted': complete, 'witness': witness, 'planted_pairs_recovered': sanities, 'seconds': monotonic()-started}
with open('result.json', 'w') as out:
    json.dump(result, out)