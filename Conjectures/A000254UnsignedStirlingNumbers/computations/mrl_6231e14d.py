# MathResearchLab experiment 6231e14d-bdbe-4e25-94b0-07d0c06ae77d
# Exhaustive check of the four clauses and the square-difference quotient
# sha256(code) = e7f21568695b25da54e9e44842fd4c532ed3684ef542ec8e54752f13906f51b6
# parameters: {"n_max": 1000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from itertools import permutations
from math import isqrt

params = json.load(open(os.environ["MRL_PARAMS"]))
limit = params['n_max']
if type(limit) is not int or not 6 <= limit <= 2000:
    raise ValueError('n_max must be an integer from 6 through 2000')

# Independently check the indexing and initial value by counting permutations.
def count_two_cycles(size):
    total = 0
    for perm in permutations(range(size)):
        seen = set()
        cycles = 0
        for start in range(size):
            if start in seen:
                continue
            cycles += 1
            vertex = start
            while vertex not in seen:
                seen.add(vertex)
                vertex = perm[vertex]
        if cycles == 2:
            total += 1
    return total

sanity = [count_two_cycles(n + 1) for n in range(7)]
a = 0
factorial = 1
names = ['first_residue', 'square_difference', 'cubic_difference', 'square_sum', 'quotient_identity']
checked = dict.fromkeys(names, 0)
failures = dict.fromkeys(names, 0)
examples = []
boundary = []

def check(name, n, actual, expected):
    checked[name] += 1
    if actual != expected:
        failures[name] += 1
        if len(examples) < 20:
            examples.append(dict(check=name, n=n, actual=actual, expected=expected))

for n in range(limit + 1):
    if n < len(sanity) and a != sanity[n]:
        raise AssertionError(f'Permutation count disagrees at n={n}')
    next_a = (n + 1) * a + factorial
    if n >= 2:
        prime = all(n % divisor != 0 for divisor in range(2, isqrt(n) + 1))
        if n != 4:
            check('first_residue', n, a % n, n - 1 if prime else 0)
        modulus = n * n
        square_difference = next_a**2 - a**2
        quotient, remainder = divmod(square_difference, n)
        if remainder:
            raise AssertionError(f'Nonintegral square-difference quotient at n={n}')
        previous_factorial = factorial // n
        check('quotient_identity', n, quotient % n, 4 * (previous_factorial % n)**2 % n)
        square_residue = square_difference % modulus
        cube_residue = (next_a**3 - a**2) % n
        sum_residue = (a**2 + next_a**2) % n
        if n >= 3:
            check('square_difference', n, square_residue, (4 * n) % modulus if prime else 0)
            check('cubic_difference', n, cube_residue, n - 2 if prime else 0)
            check('square_sum', n, sum_residue, 2 if prime else 0)
        if n <= 5:
            boundary.append(dict(n=n, a=a, next_a=next_a, first_residue=a % n, square_difference=square_residue, cubic_difference=cube_residue, square_sum=sum_residue))
    a = next_a
    factorial *= n + 1

result = {
    'summary': f'Checked all applicable indices through {limit}. Found {sum(failures.values())} failed checks.',
    'n_max': limit,
    'permutation_counts_for_n_0_through_6': sanity,
    'checks_performed': checked,
    'failure_counts': failures,
    'first_failures': examples,
    'boundary_cases': boundary,
}
with open('result.json', 'w') as output:
    json.dump(result, output)
