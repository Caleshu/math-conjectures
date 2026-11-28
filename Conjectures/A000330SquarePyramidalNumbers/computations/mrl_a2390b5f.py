# MathResearchLab experiment a2390b5f-26a6-43e1-9afb-65ff2854bf88
# Check the five lifts of the sole candidate modulo $5$
# sha256(code) = 5e138ce24e52e360b6e25088a194f57b8b32a962801e5403f8db109ae43a0c87
# parameters: {"prime": 5}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
p = params['prime']
assert p == 5

def F(c):
    return 25*c**3 + 3*c**2 - 22*c + 12

def D(c):
    x = 25*c + 1
    return -9156 - x**3 + 553*x

# Check the normalization against the original cubic at four distinct inputs.
# Both sides have degree at most three.
assert all(625*F(c) == -D(c)-1104 for c in (-2, 0, 1, 3))
base_pairs = [(c, k) for c in range(p) for k in range(p)
              if (F(c) - 144*k*k) % p == 0]
assert (2, 0) in base_pairs  # A known feasible control at the first stage.
modulus = p*p
lift_checks = []
solutions = []
for c0, k0 in base_pairs:
    rhs = {c: F(c) % modulus for c in range(c0, modulus, p)}
    lhs = {k: 144*k*k % modulus for k in range(k0, modulus, p)}
    lift_checks.append({'base_pair': [c0, k0], 'F_by_c': rhs, 'lhs_by_k': lhs})
    solutions.extend([c, k] for c, r in rhs.items() for k, s in lhs.items() if r == s)
result = {'summary': f'{len(base_pairs)} residue pairs modulo 5 lift to {len(solutions)} residue pairs modulo 25.', 'base_pairs': base_pairs, 'lift_checks': lift_checks, 'solutions_mod_25': solutions}
with open('result.json', 'w') as out:
    json.dump(result, out)
