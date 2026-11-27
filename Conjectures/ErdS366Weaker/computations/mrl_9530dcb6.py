# MathResearchLab experiment 9530dcb6-02ee-4472-b48d-ad11a5db26df
# Enumerate all 3-full integers in increasing order
# sha256(code) = 661b92f64102f356a266ceecf2008edd0c53cfd21837f332340bf9805a21133a
# parameters: {"bound": 1000000000000000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import heapq
import json
import math
import os
import time

params = json.load(open(os.environ['MRL_PARAMS']))
bound = int(params['bound'])
assert bound >= 1
deadline = time.monotonic() + 85


def ordered_full(limit):
    largest_b = math.isqrt(math.isqrt(limit))
    squarefree = bytearray([1]) * (largest_b + 1)
    for d in range(2, math.isqrt(largest_b) + 1):
        step = d * d
        squarefree[step::step] = bytes(largest_b // step)
    heap = []
    c = 1
    while c**5 <= limit:
        if squarefree[c]:
            fifth = c**5
            for b in range(1, math.isqrt(math.isqrt(limit // fifth)) + 1):
                if squarefree[b] and math.gcd(b, c) == 1:
                    core = b**4 * fifth
                    heap.append((core, 1, core))
        c += 1
    heapq.heapify(heap)
    while heap:
        value, a, core = heap[0]
        yield value
        following = core * (a + 1)**3
        if following <= limit:
            heapq.heapreplace(heap, (following, a + 1, core))
        else:
            heapq.heappop(heap)


def full_by_division(n):
    d = 2
    while d * d <= n:
        exponent = 0
        while n % d == 0:
            n //= d
            exponent += 1
        if exponent in (1, 2):
            return False
        d += 1
    return n == 1


check_bound = 5000
expected = [v for v in range(1, check_bound + 1) if full_by_division(v)]
assert list(ordered_full(check_bound)) == expected
previous = 0
count = 0
pairs = []
complete = True
for value in ordered_full(bound):
    assert value > previous
    if previous > 0 and value == previous + 1:
        pairs.append([previous, value])
    previous = value
    count += 1
    if count % 8192 == 0 and time.monotonic() >= deadline:
        complete = False
        break
covered = bound if complete else previous
result = {
    'summary': f'Found {len(pairs)} consecutive pairs with both endpoints in [1, {covered}].',
    'complete': complete,
    'requested_bound': bound,
    'verified_through': covered,
    'full_integer_count_in_verified_interval': count,
    'pairs': pairs,
    'sanity_check': {'trial_division_verified_through': check_bound, 'full_count': len(expected)}
}
with open('result.json', 'w') as f:
    json.dump(result, f)
