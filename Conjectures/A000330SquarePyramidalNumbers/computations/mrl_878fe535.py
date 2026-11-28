# MathResearchLab experiment 878fe535-6b2f-44fd-94ec-c292b0aad929
# Check the divisor condition modulo $13$
# sha256(code) = 404a54386f205ec6505f5bc2497ed4572d33c732fc397a00e1538fdfa62bd632
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))

modulus = 13
target = -9156

def f(x):
    return x**3 - 553*x

def remainder(c, constant):
    return (constant - f(25*c + 1)) % modulus

# Plant a pair of shifted coordinates 1 and 51, whose sum is 52.
control_c = -20001
control_z = 25*control_c + 1
control_constant = f(control_z) + f(1) + f(51)
control_D = control_constant - f(control_z)
assert control_D % 52 == 0
assert remainder(control_c % modulus, control_constant) == 0

residues = [remainder(c, target) for c in range(modulus)]
passing = [c for c, value in enumerate(residues) if value == 0]
result = {
    'summary': f'{len(passing)} of 13 index classes satisfy the necessary divisibility condition.',
    'D_mod_13_by_c_mod_13': residues,
    'passing_c_mod_13': passing,
    'positive_control': {'c': control_c, 'modified_constant': control_constant, 'D': control_D}
}
with open('result.json', 'w') as output:
    json.dump(result, output)
