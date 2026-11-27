# MathResearchLab experiment 4257c2a5-bfa2-4bae-8e7c-55d5d4b4dbfa
# Exact density of indices excluded by valuation one
# sha256(code) = ef5a275bd94f77c8e52f78bc57f73b4273a61228317618fd818804d194884ae8
# parameters: {"prime_max": 97}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from fractions import Fraction
from math import isqrt
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
limit = int(params['prime_max'])
if not 3 <= limit <= 199:
    raise ValueError('prime_max must lie between 3 and 199')
deadline = monotonic() + 85
primes = [p for p in range(2, limit + 1) if all(p % d for d in range(2, isqrt(p) + 1))]

def witnesses(p):
    modulus = p * p
    value = 1
    residues = []
    for r in range(modulus):
        if value and value % p == 0:
            residues.append(r)
        value = (1 - (r + 1) * value) % modulus
    assert value == 1
    return residues

assert witnesses(2) == [3]
assert witnesses(3) == []
# Independently check residue lookup across several period boundaries.
small_d = [1, 0]
for n in range(2, 202):
    small_d.append((n - 1) * (small_d[-1] + small_d[-2]))
for p in (2, 3, 5, 7):
    residues = set(witnesses(p))
    for n in range(3, len(small_d)):
        direct = small_d[n] % p == 0 and small_d[n] % (p * p) != 0
        assert direct == (n % (p * p) in residues)

uncovered = Fraction(1)
profiles = []
for p in primes:
    if monotonic() >= deadline:
        break
    modulus = p * p
    residues = witnesses(p)
    uncovered *= Fraction(modulus - len(residues), modulus)
    profiles.append({'prime': p, 'modulus': modulus, 'count': len(residues), 'valuation_one_residues': residues})
covered = 1 - uncovered
result = {'summary': f'Listed all valuation-one progressions for {len(profiles)} primes. Their union has exact density {covered}.', 'requested_prime_max': limit, 'complete': len(profiles) == len(primes), 'profiles': profiles, 'covered_density': [covered.numerator, covered.denominator], 'sanity_checks_passed': True, 'author_support': 'proved_here', 'justification': 'Periodicity makes each single-prime list exhaustive. The Chinese remainder theorem identifies residues modulo the product of the prime squares with tuples of local residues. A tuple is uncovered exactly when every coordinate lies outside its list, so the uncovered fractions multiply. Omitting indices below 3 preserves natural density.'}
with open('result.json', 'w') as out:
    json.dump(result, out)
