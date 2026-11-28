# MathResearchLab experiment 947b181d-5304-4c7d-ab30-53f4b2f70182
# Exact constant check at degree six
# sha256(code) = cd8ac0ff733962754cf85df4dbd710aefc2cc3539ffa43ad6d59955dd1a9b624
# parameters: {"s": 2, "d": 6}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from fractions import Fraction
from math import factorial

params = json.load(open(os.environ["MRL_PARAMS"]))
s, d = params['s'], params['d']
assert (s, d) == (2, 6)

def prefactor(s, d):
    return 18 * factorial(s + 1) * s ** (s + 1) * (32 * d) ** (s + 2)

# Independent hand substitution at (1, 1) checks the factorial and both exponents.
assert prefactor(1, 1) == 36 * 32768
factor = prefactor(s, d)
assert factor == 864 * 192**4
log_argument = 2 * s * d
exp_lower = sum(Fraction(4**j, factorial(j)) for j in range(5))
upper = 4 * factor
certified = exp_lower > log_argument and upper < 10**13
result = {
    'summary': 'The rational certificate succeeds.' if certified else 'The rational certificate fails.',
    's': s, 'd': d, 'prefactor': factor, 'log_argument': log_argument,
    'strict_lower_bound_for_exp_4': str(exp_lower),
    'candidate_upper_bound_for_C': upper, 'target': 10**13,
    'certified_from_supplied_formula': certified
}
with open('result.json', 'w') as output:
    json.dump(result, output)
