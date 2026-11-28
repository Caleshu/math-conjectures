# MathResearchLab experiment 20b6dc0e-7647-4440-9905-67b123247651
# Exact arithmetic audit of the printed specialization
# sha256(code) = b640d4c57b834f6b4dc3cbbb30a1851d56279312d4d7e9a2343235f333549185
# parameters: {"n": 2, "d": 6}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from fractions import Fraction
from itertools import permutations
from math import factorial

params = json.load(open(os.environ['MRL_PARAMS']))
n, d = params['n'], params['d']
assert (n, d) == (2, 6)
# Each entry represents log|root| in units of (log U)/2.
weights = [2, -1, -1]
ratios = [weights[i] - weights[j] for i, j in permutations(range(3), 2)]
assert sorted(ratios) == [-3, -3, 0, 0, 3, 3]
relative = Fraction(sum(max(w, 0) for w in ratios), 2)
absolute = relative / d
prefactor = 18 * factorial(n + 1) * n**(n + 1) * (32*d)**(n + 2)
# Positive Taylor terms certify exp(4) > 2*n*d.
exp_lower = sum(Fraction(4**j, factorial(j)) for j in range(5))
assert exp_lower > 2*n*d
upper = 4 * prefactor
assert relative == 3 and absolute == Fraction(1, 2)
assert upper < 10**13
result = {'summary': 'Checked six ordered ratios and one specialization of the printed constant.', 'twice_log_moduli_over_log_U': ratios, 'relative_height_over_log_U': str(relative), 'absolute_height_over_log_U': str(absolute), 'integer_prefactor': prefactor, 'exp4_lower_bound': str(exp_lower), 'constant_strict_upper_bound': upper}
with open('result.json', 'w') as output:
    json.dump(result, output)
