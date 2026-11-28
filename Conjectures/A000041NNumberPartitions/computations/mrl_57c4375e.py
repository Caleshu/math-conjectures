# MathResearchLab experiment 57c4375e-b958-4a6d-b30c-99aaf62c356c
# Print the certificate and independently audit its three conditions
# sha256(code) = 1f04a9ce549841d3b9dbd1da5cd19f33782e84a2cb8ec87005fa9a6a00a84051
# parameters: {"base": [3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 19, 21, 22, 23, 24, 26, 29, 30, 31, 37, 38, 43, 47, 49, 52, 54, 58], "index_cap": 1600}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from itertools import combinations

params = json.load(open(os.environ["MRL_PARAMS"]))
base = params['base']
cap = params['index_cap']
target = 17242681614666977586621263007510624361940
start = 1817584

# Candidate generation only. Euler's recurrence supplies these weights.
def euler_partitions(n):
    offsets = []
    j = 1
    while j * (3*j - 1) // 2 <= n:
        sign = 1 if j % 2 else -1
        offsets.append((j * (3*j - 1) // 2, sign))
        offsets.append((j * (3*j + 1) // 2, sign))
        j += 1
    p = [1] + [0] * n
    for k in range(1, n + 1):
        for offset, sign in offsets:
            if offset > k:
                break
            p[k] += sign * p[k - offset]
    return p

def run():
    if len(base) != 30 or len(set(base)) != 30 or not all(1 <= k <= cap for k in base):
        raise ValueError('Invalid base indices')
    p = euler_partitions(cap)
    chosen = {k: p[k] + 2 for k in base}
    endpoint = start
    for step in range(1, 122):
        limit = endpoint - 47
        if p[cap] + 2 <= limit:
            return {'summary': 'Candidate reconstruction incomplete at the index cap.', 'step': step, 'limit': limit, 'indices_so_far': sorted(chosen)}
        for k in range(cap, 0, -1):
            w = p[k] + 2
            if k not in chosen and w <= limit and all(w % v and v % w for v in chosen.values()):
                chosen[k] = w
                endpoint += w
                break
        else:
            return {'summary': 'Candidate reconstruction stopped with no compatible weight.', 'step': step, 'limit': limit, 'indices_so_far': sorted(chosen)}

    # The audit consumes only the printed indices. It does not use the
    # generator's weights, running endpoint, or pick order.
    certificate = {'base': sorted(base), 'added': sorted(set(chosen).difference(base))}
    printed = json.dumps(certificate, separators=(',', ':'))
    print(printed, flush=True)
    cert = json.loads(printed)
    indices = sorted(cert['base'] + cert['added'])
    if (len(cert['base']), len(cert['added']), len(set(indices))) != (30, 121, 151):
        raise ValueError('Certificate cardinality mismatch')

    # After processing part d, q[t] counts partitions of t with parts <= d.
    # Ascending t permits any multiplicity of d, including zero.
    n = max(indices)
    q = [1] + [0] * n
    for d in range(1, n + 1):
        for t in range(d, n + 1):
            q[t] += q[t - d]
    known = [1, 1, 2, 3, 5, 7, 11, 15, 22, 30, 42]
    if q[:11] != known or p[:11] != known:
        raise ArithmeticError('Small partition sanity check failed')
    weights = {k: q[k] + 2 for k in indices}
    conflicts = []
    pair_count = 0
    for a, b in combinations(indices, 2):
        pair_count += 1
        if weights[b] % weights[a] == 0:
            conflicts.append({'a': a, 'b': b, 'divisor': weights[a], 'multiple': weights[b], 'quotient': weights[b] // weights[a]})
    if pair_count != 11325:
        raise ArithmeticError('Pair enumeration incomplete')

    ordered = sorted(cert['added'], key=weights.__getitem__)
    prefix = 0
    violations = []
    min_slack = None
    for i, k in enumerate(ordered, 1):
        bound = start + prefix - 47
        slack = bound - weights[k]
        if min_slack is None or slack < min_slack['slack']:
            min_slack = {'i': i, 'k': k, 'weight': weights[k], 'bound': bound, 'slack': slack}
        if slack < 0:
            violations.append({'i': i, 'k': k, 'weight': weights[k], 'bound': bound})
        prefix += weights[k]

    base_sum = sum(weights[k] for k in cert['base'])
    total = sum(weights.values())
    actual = total - 48
    checks = {'a': not conflicts, 'b': not violations, 'c': actual == target}
    return {'summary': 'All three checks pass for the printed set.' if all(checks.values()) else 'The printed set fails at least one target check.', 'certificate': cert, 'checks': checks, 'pairs_checked': pair_count, 'divisible_pairs': conflicts, 'inequalities_checked': len(ordered), 'minimum_slack': min_slack, 'violated_inequalities': violations, 'base_sum': base_sum, 'base_sum_minus_48_equals_start': base_sum - 48 == start, 'sum_all_weights': total, 'sum_minus_48': actual, 'claimed_endpoint': target, 'endpoint_difference': actual - target}

result = run()
with open('result.json', 'w') as output:
    json.dump(result, output)
