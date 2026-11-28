# MathResearchLab experiment 7b17facc-fcf9-499d-a272-c15148c7d36c
# Exhaustive divisor and residue log for the four levels
# sha256(code) = e0f1b5b5b5f54a8935cee64bfe768577616f88bff472752be4e8bf90d13ec637
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import prod
from time import monotonic

params = json.load(open(os.environ["MRL_PARAMS"]))
deadline = monotonic() + 95
levels = (7, 8, 9, 10)

# Each row omits its last certified prime, recovered as an exact quotient.
prefixes = [
    [], [], [], [], [],
    [641],
    [274177],
    [59649589127497217],
    [1238926361552897],
    [2424833, 7455602825647884208337395736200454918783366342657],
]
rows = []
for j, prefix in enumerate(prefixes):
    fermat = (1 << (1 << j)) + 1
    last, remainder = divmod(fermat, prod(prefix))
    assert remainder == 0 and last > 1
    row = prefix + [last]
    assert prod(row) == fermat
    rows.append(row)
all_factors = [q for row in rows for q in row]
assert len(set(all_factors)) == len(all_factors)


def residues(m):
    first = pow(2, m, m + 1)
    second = pow(2, m, m*m + 1) if first == 1 else None
    return first, second


# Exercise all three paths, including rejection after the first test passes.
assert residues(8) == (4, None)
assert residues(12) == (1, 36)
assert residues(256) == (1, 1)

reports = []
counterexamples = []
for a in levels:
    factors = [q for row in rows[:a] for q in row]
    N = (1 << (1 << a)) - 1
    assert prod(factors) == N
    # After each step the list contains all subset products of the prefix.
    divisors = [1]
    for q in factors:
        divisors.extend([d*q for d in divisors])
    assert len(set(divisors)) == len(divisors) == 1 << len(factors)
    log = []
    passing = []
    inspected = 0
    for d in divisors:
        if inspected % 128 == 0 and monotonic() >= deadline:
            break
        inspected += 1
        m = d + 1
        if (m & -m) != (1 << a):
            continue
        first, second = residues(m)
        # Decimal strings preserve exact integers in JSON readers using doubles.
        log.append({'D': str(d), 'm': str(m), 'r_m_plus_1': str(first),
                    'r_m_squared_plus_1': None if second is None else str(second)})
        if second == 1:
            passing.append(str(m))
            if m != 256:
                counterexamples.append({'a': a, 'D': str(d), 'm': str(m)})
    complete = inspected == len(divisors)
    if complete and a == 8:
        assert '256' in passing
    reports.append({'a': a, 'complete': complete, 'divisor_count': len(divisors),
                    'divisors_inspected': inspected, 'candidates_logged': len(log),
                    'passing_m': passing, 'log': log})
    if not complete:
        break

complete = len(reports) == len(levels) and all(r['complete'] for r in reports)
if counterexamples:
    summary = 'Falsified. Each counterexample listed passed both tests with m different from 256.'
elif complete:
    summary = 'Verified exhaustively at a = 7, 8, 9, 10. The sole passing m is 256 at a = 8.'
else:
    summary = 'Partial enumeration. No counterexample in the inspected divisors.'
result = {'summary': summary, 'requested_levels': levels, 'complete': complete,
          'factor_table': [[str(q) for q in row] for row in rows],
          'counterexamples': counterexamples, 'levels': reports}
with open('result.json', 'w') as output:
    json.dump(result, output, separators=(',', ':'))
