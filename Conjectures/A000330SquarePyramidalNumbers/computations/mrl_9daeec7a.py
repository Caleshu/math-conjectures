# MathResearchLab experiment 9daeec7a-66c0-4115-81b9-07400c98d702
# One lift test for the entire divisor class
# sha256(code) = 8ccfe3d50302bfce779524d2d4f2990838633c861e93a761e79df4c6f1e1048f
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))


def D(c):
    z = 25*c + 1
    return -9156 - z**3 + 553*z


def F(c):
    return 25*c**3 + 3*c*c - 22*c + 12


def residual(c, s, d):
    return 4*D(c) - s**3 + 2212*s - 3*s*d*d


# The two lists cover each variable separately modulo 5.
lhs = [144*h*h % 5 for h in range(5)]
rhs = [F(c) % 5 for c in range(5)]
base_pairs = [[c, h] for c in range(5) for h in range(5) if lhs[h] == rhs[c]]

# Positive control in the original coordinates, with nonzero shifts
# in s, c, and h from their base representatives.
c0, s0, d0 = 7, 1202, 250
control = residual(c0, s0, d0)
assert (s0 + 48) % 1250 == 0
assert (s0 + d0) % 50 == (s0 - d0) % 50 == 2
assert control % 3125 == 0
assert control % 15625 == 2500*(144*(d0//50)**2 - F(c0)) % 15625

lift_tests = []
for c, h in base_pairs:
    # Both partial derivatives vanish mod 5, so the value mod 25
    # is constant on all 25 lifts of this pair.
    assert (75*c*c + 6*c - 22) % 5 == 0 and (288*h) % 5 == 0
    reduced = (144*h*h - F(c)) % 25
    original = residual(c, -48, 50*h) % 15625
    assert original == 2500*reduced % 15625
    lift_tests.append({'c_mod_5': c, 'h_mod_5': h, 'reduced_mod_25': reduced, 'original_mod_15625': original})

possible = any(row['original_mod_15625'] == 0 for row in lift_tests)
result = {
    'summary': 'The congruences have a solution.' if possible else 'The congruences have no solution in the specified divisor class.',
    'lhs_by_h_mod_5': lhs,
    'rhs_by_c_mod_5': rhs,
    'lift_tests': lift_tests,
    'positive_control_mod_3125': control % 3125,
    'positive_control_mod_15625': control % 15625
}
with open('result.json', 'w') as out:
    json.dump(result, out)
