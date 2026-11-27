# MathResearchLab experiment 2ac8f738-5193-46e0-8280-6ebd44582efa
# Exact onset of periodicity for small odd moduli
# sha256(code) = 742118b7aa8d795490587a38b7d24aac88a066a9635b10120d1e33953370603b
# parameters: {"k_max": 243}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os

params = json.load(open(os.environ["MRL_PARAMS"]))
k_max = params['k_max']
assert 3 <= k_max <= 1000

def factor_odd(k):
    factors = []
    candidate = 3
    while candidate * candidate <= k:
        exponent = 0
        while k % candidate == 0:
            k //= candidate
            exponent += 1
        if exponent:
            factors.append((candidate, exponent))
        candidate += 2
    if k > 1:
        factors.append((k, 1))
    return factors

def residue(k, n):
    total = 0
    for j in range(k):
        term = pow(2 * j + 1, 2 * n, k)
        total += -term if j % 2 else term
    return (-total if n % 2 else total) % k

sanity = [residue(21, n) for n in range(1, 7)]
assert sanity == [1, 5, 19, 20, 16, 2]
rows = []
for k in range(3, k_max + 1, 2):
    factors = factor_odd(k)
    phi = 1
    for p, e in factors:
        phi *= (p - 1) * p ** (e - 1)
    bound = max((e + 1) // 2 for p, e in factors)
    failures = []
    for n in range(1, bound):
        left = residue(k, n)
        right = residue(k, n + phi)
        if left != right:
            failures.append({'n': n, 'a_n': left, 'a_n_plus_phi': right})
    onset = failures[-1]['n'] + 1 if failures else 1
    assert residue(k, bound) == residue(k, bound + phi)
    assert (onset == 1) == all(e <= 2 for p, e in factors)
    rows.append({'k': k, 'prime_factorization': factors, 'phi': phi, 'proved_tail_bound': bound, 'least_onset': onset, 'all_failures': failures})

pure_count = sum(row['least_onset'] == 1 for row in rows)
with open('result.json', 'w') as out:
    json.dump({'summary': f'The totient shift holds from index 1 for {pure_count} of {len(rows)} odd moduli. Each row gives its exact first index of permanent agreement.', 'sanity_mod_21': sanity, 'rows': rows}, out)
