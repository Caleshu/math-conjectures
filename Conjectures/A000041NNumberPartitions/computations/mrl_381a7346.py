# MathResearchLab experiment 381a7346-84f8-4555-a96b-2b2e0506280e
# Extend the antichain by one index and certify any remaining gaps
# sha256(code) = ee593c9dbcfa35abc10110a561890e593c8f7c99cb541a1d67f011fa516c1fde
# parameters: {"lo": 716206, "hi": 1000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from bisect import bisect_right

params = json.load(open(os.environ['MRL_PARAMS']))
lo, hi = params['lo'], params['hi']
assert (lo, hi) == (716206, 1000000)
deadline = time.monotonic() + 85

# Coin-change DP. Increase the cutoff until it includes the first overweight term.
cutoff = 64
while True:
    p = [1] + [0] * cutoff
    for part in range(1, cutoff + 1):
        for n in range(part, cutoff + 1):
            p[n] += p[n - part]
    if p[-1] + 2 > hi:
        break
    cutoff *= 2
assert p[:11] == [1, 1, 2, 3, 5, 7, 11, 15, 22, 30, 42]
first_over = next(k for k in range(1, cutoff + 1) if p[k] + 2 > hi)
w = [v + 2 for v in p[1:first_over]]
assert all(a < b for a, b in zip(w, w[1:]))

proposed = [3,4,5,6,7,8,9,10,12,13,14,15,16,19,21,22,23,24,26,29,30,31,37,38,43,47,49,52,53]
indices = []
for k in proposed:
    if k < first_over and all(w[k-1] % w[j-1] for j in indices):
        indices.append(k)

# Bit s in prefix[i] records a subset of the first i retained weights summing to s.
cap = (1 << (hi + 1)) - 1
prefix = [1]
for k in indices:
    previous = prefix[-1]
    prefix.append((previous | (previous << w[k-1])) & cap)

def decode(n):
    chosen = []
    for i in range(len(indices), 0, -1):
        if not ((prefix[i-1] >> n) & 1):
            k = indices[i-1]
            chosen.append(k)
            n -= w[k-1]
            assert n >= 0
    assert n == 0
    return chosen[::-1]

def validate(n, chosen):
    values = sorted(w[k-1] for k in chosen)
    assert all(1 <= k < first_over for k in chosen)
    assert sum(values) == n
    assert all(b % a for j, b in enumerate(values) for a in values[:j])

# In the exhaustive fallback, picking a weight deletes every divisor and multiple.
conflicts = []
for a in w:
    conflicts.append(sum(1 << j for j, b in enumerate(w) if a % b == 0 or b % a == 0))
all_indices = (1 << len(w)) - 1

def search(n, available):
    if time.monotonic() >= deadline:
        raise TimeoutError
    if n == 0:
        return ()
    available &= (1 << bisect_right(w, n)) - 1
    if not available:
        return None
    j = available.bit_length() - 1
    smaller = available ^ (1 << j)
    used = search(n - w[j], smaller & ~conflicts[j])
    if used is not None:
        return used + (j + 1,)
    return search(n, smaller)

# 3+4 is legal. With only weights 3 and 9, the sum 12 is forbidden.
assert search(7, all_indices) == (1, 2)
assert search(12, (1 << w.index(3)) | (1 << w.index(9))) is None
assert search(6, all_indices) is None

def record(ranges, n):
    if ranges and ranges[-1][1] + 1 == n:
        ranges[-1][1] = n
    else:
        ranges.append([n, n])

packed = prefix[-1].to_bytes((hi + 8) // 8, 'little')
by_status = {s: [] for s in ('FEASIBLE', 'INFEASIBLE', 'UNKNOWN')}
extra_witnesses = {}
samples = {}
expired = False
fast_count = 0
for n in range(lo, hi + 1):
    if packed[n // 8] & (1 << (n % 8)):
        fast_count += 1
        status = 'FEASIBLE'
        if n in (lo, (lo + hi) // 2, hi):
            chosen = decode(n)
            validate(n, chosen)
            samples[str(n)] = chosen
    elif expired:
        status = 'UNKNOWN'
    else:
        try:
            chosen = search(n, all_indices)
        except TimeoutError:
            expired = True
            status = 'UNKNOWN'
        else:
            if chosen is None:
                status = 'INFEASIBLE'
            else:
                validate(n, chosen)
                extra_witnesses[str(n)] = chosen
                status = 'FEASIBLE'
    record(by_status[status], n)

assert sum(b - a + 1 for spans in by_status.values() for a, b in spans) == hi - lo + 1
result = {
    'summary': f'{fast_count} of {hi-lo+1} targets have a witness in the checked antichain. INFEASIBLE ranges are exhaustively certified gaps. UNKNOWN ranges are the exact unfinished scope.',
    'author_support': 'proved_here',
    'justification': 'Coin-change DP counts partitions by the largest allowed part, using the empty partition as its base case. Adding a part of size one injects partitions of k into partitions of k+1, so the first overweight term bounds all eligible indices. The retained weights increase, and each passes the remainder test against every earlier one. The two terms of each prefix update enumerate omission and inclusion of the new weight. Reverse decoding omits that weight whenever omission works and otherwise subtracts it. For each fallback call, positive weights larger than the residual cannot occur. Every legal solution either omits the largest available weight or includes it and omits all its divisibility conflicts. These branches exhaust the possibilities, with zero residual as success and empty availability at positive residual as failure. A time interruption receives UNKNOWN.',
    'scope_inclusive': [lo, hi],
    'first_overweight_index_and_weight': [first_over, p[first_over] + 2],
    'all_29_indices_retained': indices == proposed,
    'antichain_index_weight_pairs': [[k, w[k-1]] for k in indices],
    'antichain_covered_count': fast_count,
    'decoder': 'Rebuild prefix from the reported pairs in order. For any FEASIBLE target absent from fallback_witnesses, apply decode(target) as defined in the program.',
    'decoded_samples': samples,
    'fallback_witnesses': extra_witnesses,
    'inclusive_ranges_by_status': by_status
}
with open('result.json', 'w') as f:
    json.dump(result, f)
