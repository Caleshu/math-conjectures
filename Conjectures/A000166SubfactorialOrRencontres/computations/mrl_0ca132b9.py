# MathResearchLab experiment 0ca132b9-4c55-4d2e-8523-acf2254016da
# Exhaustive perfect-power test using factors of $n-1$
# sha256(code) = 99e7b81bcfef1c7289f33d347bda9187314287b7841f7191f558feeebb8f7c72
# parameters: {"n_max": 20000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from itertools import permutations
from math import gcd, isqrt
from time import monotonic
from sympy import integer_nthroot

params = json.load(open(os.environ['MRL_PARAMS']))
limit = int(params['n_max'])
if not 3 <= limit <= 50000:
    raise ValueError('n_max must lie between 3 and 50000')
deadline = monotonic() + 85
filter_primes = (7, 11, 13, 17, 19, 31, 37, 43, 61, 73, 97)

def prime_divisors(value):
    p = 2
    while p * p <= value:
        if value % p == 0:
            yield p
            while value % p == 0:
                value //= p
        p = 3 if p == 2 else p + 2
    if value > 1:
        yield value

def classify(n, value):
    exponent_gcd = 0
    for p in prime_divisors(n - 1):
        quotient, remainder = divmod(value, p)
        assert remainder == 0
        valuation = 1
        while quotient % p == 0:
            quotient //= p
            valuation += 1
        exponent_gcd = gcd(exponent_gcd, valuation)
        if exponent_gcd == 1:
            return [], 'valuation_gcd_one'

    powers = []
    tested_root = False
    for q in prime_divisors(exponent_gcd):
        for ell in filter_primes:
            if (ell - 1) % q:
                continue
            residue = value % ell
            # A nonzero q-th power must pass this test by Fermat's theorem.
            if residue and pow(residue, (ell - 1) // q, ell) != 1:
                break
        else:
            tested_root = True
            base = isqrt(value) if q == 2 else int(integer_nthroot(value, q)[0])
            if base ** q == value:
                powers.append((q, base))
    if powers:
        return powers, 'perfect_power'
    return [], 'excluded_after_root_test' if tested_root else 'excluded_by_residues'

# Check the recurrence against the definition and test a value having two prime exponents.
small = 1
for n in range(9):
    if n:
        small = n * small + (-1 if n % 2 else 1)
    direct = sum(all(i != j for i, j in enumerate(perm)) for perm in permutations(range(n)))
    assert small == direct
    if n >= 3:
        assert classify(n, small)[0] == ([(2, 3)] if n == 4 else [])
assert classify(9, 64)[0] == [(2, 8), (3, 4)]
assert classify(9, 192)[0] == []

value = 1  # D_2
through = 2
counts = {}
hits = []
for n in range(3, limit + 1):
    if monotonic() >= deadline:
        break
    value = n * value + (-1 if n % 2 else 1)
    powers, reason = classify(n, value)
    for q, base in powers:
        # Hex also serializes witnesses exceeding Python's decimal digit limit.
        hits.append({'n': n, 'prime_exponent': q, 'base_hex': hex(base)})
    counts[reason] = counts.get(reason, 0) + 1
    through = n
assert sum(counts.values()) == through - 2
result = {'summary': f'Exhaustively classified 3 <= n <= {through} and found {len(hits)} prime-exponent representations.', 'requested_through': limit, 'checked_through': through, 'complete': through == limit, 'representations': hits, 'index_counts': counts, 'sanity_checks_passed': True, 'author_support': 'proved_here', 'justification': 'Each possible prime exponent divides the gcd of the inspected valuations. Each candidate was excluded by a necessary modular condition or decided by an exact integer root.'}
with open('result.json', 'w') as out:
    json.dump(result, out)
