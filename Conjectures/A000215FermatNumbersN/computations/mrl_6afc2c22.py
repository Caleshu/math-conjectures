# MathResearchLab experiment 6afc2c22-0332-481c-9101-a6f0ce33141f
# Check the sole residual prime
# sha256(code) = aa3277871efcab07f6eb6cf0a99989f1cb9ead714304ea3e8fcb1e8baa2bd812
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))

# Positive control: at m=16, the modulus m^4-1 equals 2^m-1.
def full_remainder(m):
    modulus = m**4 - 1
    return (pow(2, m, modulus) - 1) % modulus

control = full_remainder(16)
assert control == 0
p_max = (15 + 1) // 4
# Every odd integer from 3 through this bound is prime.
assert p_max == 4
rows = []
for p in range(3, p_max + 1, 2):
    m = 4 * p
    factor = m - 1
    remainder = full_remainder(m)
    factor_remainder = (pow(2, m, factor) - 1) % factor
    assert remainder % factor == factor_remainder
    rows.append({'p': p, 'factor': factor, 'factor_remainder': factor_remainder, 'full_remainder': remainder})

hits = [row['p'] for row in rows if row['full_remainder'] == 0]
with open('result.json', 'w') as output:
    json.dump({'summary': f'Checked {len(rows)} residual odd prime(s) and found {len(hits)} exception(s).', 'p_max': p_max, 'control_m16_remainder': control, 'rows': rows, 'exceptions': hits}, output)