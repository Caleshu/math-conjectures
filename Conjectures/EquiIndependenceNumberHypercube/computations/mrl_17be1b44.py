# MathResearchLab experiment 17be1b44-7fb1-4d7e-831f-1f8bffc44e5c
# Check the first excluded size in simplicial order
# sha256(code) = aa1ea56496e4303d98f5047c48743c32bb8044c38799fe9246514e9f5b2f4237
# parameters: {"m_max": 14}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from itertools import combinations, islice
from math import comb

params = json.load(open(os.environ["MRL_PARAMS"]))
m_max = params['m_max']
if type(m_max) is not int or not 0 <= m_max <= 14:
    raise ValueError('m_max must be an integer from 0 through 14')

def simplicial_vertices(m):
    for weight in range(m + 1):
        for coords in combinations(range(m), weight):
            yield sum(1 << i for i in coords)

def closed_size(vertices, m):
    seen = set(vertices)
    for x in vertices:
        for i in range(m):
            seen.add(x ^ (1 << i))
    return len(seen)

rows = []
for m in range(m_max + 1):
    total = 1 << m
    s = m // 2
    twice_k = total - (1 << (m - 2*s)) * comb(2*s, s)
    assert twice_k % 2 == 0
    k = twice_k // 2
    first_excluded = k + 1
    segment = list(islice(simplicial_vertices(m), first_excluded))
    assert len(set(segment)) == first_excluded
    size = closed_size(segment, m)
    threshold = total - first_excluded
    row = {'n': m + 1, 'm': m, 'k': k, 'tested_size': first_excluded,
           'closed_size': size, 'threshold': threshold, 'excess': size - threshold}
    if m <= 4:
        # Independent distance test over every subset of the target size.
        balls = [sum(1 << y for y in range(total) if (x ^ y).bit_count() <= 1)
                 for x in range(total)]
        minimum = total
        for subset in combinations(range(total), first_excluded):
            union = 0
            for x in subset:
                union |= balls[x]
            minimum = min(minimum, union.bit_count())
        row['exhaustive_minimum'] = minimum
        row['sanity_passed'] = minimum == size
    rows.append(row)

passed = all(row['excess'] > 0 and row.get('sanity_passed', True) for row in rows)
result = {'summary': ('All checks passed' if passed else 'A check failed') + f' for m=0 through {m_max}.',
          'passed': passed, 'rows': rows}
with open('result.json', 'w') as out:
    json.dump(result, out, indent=2)
