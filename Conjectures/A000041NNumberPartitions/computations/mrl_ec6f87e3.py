# MathResearchLab experiment ec6f87e3-d112-44a3-a5d8-66dd3e0d681e
# Exact perfect-power census for partition numbers
# sha256(code) = 3fd1bed0ac6a4ce19d79fcd77a5060ecdd4c3aa15e1db2ebcf107d1bf63cb774
# parameters: {"n_max": 20000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
n_max = int(params['n_max'])
assert 0 <= n_max <= 30000
deadline = monotonic() + 85

# Every partition of n >= 1 gives a composition by sorting its parts.
# Thus p(n) <= 2**(n-1), so the sieve includes every required exponent.
sieve_limit = max(8192, n_max)
is_prime = bytearray([1]) * (sieve_limit + 1)
is_prime[:2] = bytes(2)
for d in range(2, isqrt(sieve_limit) + 1):
    if is_prime[d]:
        count = (sieve_limit - d*d) // d + 1
        is_prime[d*d::d] = bytes(count)
primes = [i for i, flag in enumerate(is_prime) if flag]
filters = {}

def moduli(e):
    if e not in filters:
        selected = []
        for ell in range(e + 1, sieve_limit + 1, e):
            if is_prime[ell]:
                selected.append((ell, (ell - 1) // e))
                if len(selected) == 3:
                    break
        filters[e] = selected
    return filters[e]

def exact_root(v, e):
    if e == 2:
        x = isqrt(v)
        return x if x*x == v else None
    lo = 1
    hi = 1 << ((v.bit_length() + e - 1) // e)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if mid**e <= v:
            lo = mid
        else:
            hi = mid
    return lo if lo**e == v else None

def witnesses(v):
    found = []
    for e in primes:
        if e >= v.bit_length():
            break
        if e > 2 and any(pow(v, t, ell) not in (0, 1) for ell, t in moduli(e)):
            continue
        x = exact_root(v, e)
        if x is not None:
            found.append((e, x))
    return found

# Independently enumerate small powers, including overlaps such as 64.
small = {v: [] for v in range(1, 513)}
for x in range(2, isqrt(512) + 1):
    for e in (2, 3, 5, 7):
        if x**e <= 512:
            small[x**e].append((e, x))
assert all(witnesses(v) == sorted(expected) for v, expected in small.items())

check_limit = min(100, n_max)
coin = [1] + [0] * check_limit
for part in range(1, check_limit + 1):
    for total in range(part, check_limit + 1):
        coin[total] += coin[total - part]

offsets = []
k = 1
while k*(3*k-1)//2 <= n_max:
    sign = 1 if k % 2 else -1
    for g in (k*(3*k-1)//2, k*(3*k+1)//2):
        offsets.append((g, sign))
    k += 1

partitions = [1]
hits = []
last = -1
for n in range(n_max + 1):
    if monotonic() >= deadline:
        break
    if n:
        value = 0
        for g, sign in offsets:
            if g > n:
                break
            value += sign * partitions[n-g]
        assert value > 0
        partitions.append(value)
    v = partitions[n]
    if n <= check_limit:
        assert v == coin[n]
    roots = witnesses(v)
    if roots:
        hits.append({'n': n, 'p_n': str(v), 'witnesses': [{'prime_exponent': e, 'base': str(x)} for e, x in roots]})
    last = n

result = {'summary': f'Exact tests completed for 0 <= n <= {last}, with {len(hits)} indices admitting a perfect power.', 'requested_through': n_max, 'completed_through': last, 'complete': last == n_max, 'hits': hits, 'small_power_check_through': 512, 'independent_partition_check_through': min(last, check_limit)}
with open('result.json', 'w') as out:
    json.dump(result, out)
