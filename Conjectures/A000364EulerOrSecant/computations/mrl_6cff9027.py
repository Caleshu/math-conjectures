# MathResearchLab experiment 6cff9027-8d37-4df8-8ae3-18f6760976fe
# Independent recurrence check of the counterexample
# sha256(code) = a57488df2dc21e28f19413b5ce1320c35790302222a644ce651b11bdc25b4cb7
# parameters: {"k_max": 128, "n_max": 48}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import comb, lcm

params = json.load(open(os.environ["MRL_PARAMS"]))
k_max = params['k_max']
n_max = params['n_max']
assert 1 <= k_max <= 256 and 1 <= n_max <= 100

phi = list(range(k_max + 1))
for prime in range(2, k_max + 1):
    if phi[prime] == prime:
        for multiple in range(prime, k_max + 1, prime):
            phi[multiple] -= phi[multiple] // prime

# Work modulo one common multiple so every requested reduction is exact.
modulus = lcm(21, 27, *range(1, k_max + 1))
last = max(19, n_max + max(phi[1:]))
a = [1]
for n in range(1, last + 1):
    total = 0
    for j in range(1, n + 1):
        term = comb(2 * n, 2 * j) * a[n - j]
        total += term if j % 2 else -term
    a.append(total % modulus)

example = [a[n] % 21 for n in range(1, 13)]
assert example == [1, 5, 19, 20, 16, 2] * 2
witness = [a[1] % 27, a[19] % 27]
assert witness == [1, 10]
rows = []
for k in range(1, k_max + 1):
    shift = phi[k]
    failure = None
    for n in range(1, n_max + 1):
        left = a[n] % k
        right = a[n + shift] % k
        if left != right:
            failure = {'n': n, 'a_n': left, 'a_n_plus_phi': right}
            break
    rows.append({'k': k, 'phi': shift, 'first_failure': failure})

count = sum(row['first_failure'] is not None for row in rows)
with open('result.json', 'w') as out:
    json.dump({'summary': f'{count} of {k_max} moduli have a mismatch at an index from 1 through {n_max}.', 'n_max': n_max, 'sanity_mod_21': example, 'witness_mod_27': witness, 'rows': rows}, out)
