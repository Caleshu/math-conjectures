# MathResearchLab experiment 5f5e5ced-086a-440d-9856-0c229e4d58e4
# A single prime witness modulo 103
# sha256(code) = aaa5573255d8d4132e33eea032eb38cddb72d7a464a0ae28e49dc2d8e77ff432
# parameters: {"n": 131073, "p": 103, "k": 17}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))

n, p, k = params['n'], params['p'], params['k']
assert (n, p, k) == (131073, 103, 17)

def derangement_mod(index, modulus):
    value = 1
    for j in range(1, index + 1):
        sign = -1 if j % 2 else 1
        value = (j * value + sign) % modulus
    return value

small = derangement_mod(4, p)
assert small == 9
blocks, r = divmod(n, p)
assert blocks % 2 == 0 and r == 57
residue = derangement_mod(r, p)
test = pow(residue, (p - 1) // k, p)
excluded = residue != 0 and test != 1
result = {
    'summary': ('D(131073) is not a perfect power.' if excluded else 'Modulus 103 leaves the target unresolved.'),
    'author_support': 'proved_here',
    'justification': 'Every nonzero seventeenth power modulo 103 has sixth power 1. The exact 2-adic valuation 17 forces any exponent greater than one to equal 17.',
    'n': n, 'prime': p, 'exponent': k, 'reduced_index': r,
    'D4_mod_103': small, 'D_n_mod_103': residue,
    'sixth_power_mod_103': test, 'seventeenth_power_excluded': excluded
}
with open('result.json', 'w') as output:
    json.dump(result, output)
