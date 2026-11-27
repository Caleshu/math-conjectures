# MathResearchLab experiment bea0e081-e8ed-4afc-935b-b21a9a8ab9c6
# Classify each prime by a complete recurrence cycle and test the choice of $k$
# sha256(code) = 8ce5af4837aab3bd59af27888dc2aeaa216596d348b2654c2ac25df58e3116fd
# parameters: {"prime_bound": 1500}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
B = int(params['prime_bound'])
assert 2 <= B <= 5000
deadline = monotonic() + 70

def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))

def fib_mod(n, p):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * (2*b - a) % p
        d = (a*a + b*b) % p
        a, b = (c, d) if bit == '0' else (d, (c+d) % p)
    return a

def classify(p):
    # Include parity so an odd-index witness in a later cycle cannot be missed.
    a, b, u, v = 0, 1, 2 % p, 1
    n = 0
    rank = odd_zero = lucas_zero = None
    while True:
        if a == 0 and n > 0 and rank is None:
            rank = n
        if a == 0 and n % 2 and odd_zero is None:
            odd_zero = n
        if u == 0 and lucas_zero is None:
            lucas_zero = n
        a, b = b, (a+b) % p
        u, v = v, (u+v) % p
        n += 1
        if (a, b, u, v, n % 2) == (0, 1, 2 % p, 1, 0):
            return {'p': p, 'cycle_with_parity': n, 'rank': rank or n, 'first_odd_fib_zero': odd_zero, 'first_lucas_zero': lucas_zero}
        if n % 2048 == 0 and monotonic() >= deadline:
            return None

assert [fib_mod(n, 101) for n in range(9)] == [0, 1, 1, 2, 3, 5, 8, 13, 21]
assert classify(7)['first_lucas_zero'] == 4
assert classify(13)['first_odd_fib_zero'] == 7
assert classify(2)['first_lucas_zero'] == 0
rows = []
failures = {'odd_index_equivalence_for_odd_p': [], 'maximal_k': [], 'any_k': []}
primes = [p for p in range(2, B+1) if is_prime(p)]
for p in primes:
    if monotonic() >= deadline:
        break
    row = classify(p)
    if row is None:
        break
    missing = row['first_lucas_zero'] is None
    if p % 2 and not (missing == (row['first_odd_fib_zero'] is not None) == bool(row['rank'] % 2)):
        failures['odd_index_equivalence_for_odd_p'].append(p)
    if p > 5:
        if p % 5 in (2, 3):
            indices = [p+1, (p+1)//2]
            residues = [fib_mod(i, p) for i in indices]
            maximal = any_k = all(x == 0 for x in residues)
        else:
            odd_part = p-1
            indices = []
            while odd_part % 2 == 0:
                odd_part //= 2
                indices.append(odd_part)
            residues = [fib_mod(i, p) for i in indices]
            maximal = residues[0] == 0 and residues[-1] == 0
            any_k = residues[0] == 0 and any(x == 0 for x in residues)
        row.update(indices=indices, fib_residues=residues, maximal_k_test=maximal, any_k_test=any_k)
        if maximal != missing:
            failures['maximal_k'].append(p)
        if any_k != missing:
            failures['any_k'].append(p)
    rows.append(row)

quoted = {5, 13, 17, 37, 53, 61, 73, 89, 97, 109, 113, 137, 149}
checked_small = {r['p'] for r in rows if r['p'] < 150}
absent = [r['p'] for r in rows if r['first_lucas_zero'] is None]
difference = sorted((quoted ^ set(absent)) & checked_small)
result = {'summary': f'Completed exact parity-aware cycles for {len(rows)} of {len(primes)} primes through {B}.', 'complete': len(rows) == len(primes), 'absent_primes': absent, 'quoted_list_symmetric_difference_on_checked_primes': difference, 'counterexamples': failures, 'rows': rows}
with open('result.json', 'w') as out:
    json.dump(result, out)
