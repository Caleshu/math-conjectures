# MathResearchLab experiment 26805883-e632-4b07-a751-93153ac08d4f
# Exact divisibility-antichain coverage through $250000$
# sha256(code) = 8906af751a763c7716406bb48cd7c728daa15775affd4ae8ce2871da15657118
# parameters: {"bounds": [40, 7140, 50000, 250000]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from functools import lru_cache
from itertools import combinations
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))


def shifted_partitions(bound):
    last = 16
    while True:
        counts = [1] + [0] * last
        for part in range(1, last + 1):
            for total in range(part, last + 1):
                counts[total] += counts[total - part]
        if counts[last] + 2 > bound:
            return sorted({p + 2 for p in counts[1:] if p + 2 <= bound})
        last *= 2


def attainable(values, bound, deadline):
    size = len(values)
    edges = [0] * size
    for i in range(size):
        for j in range(i + 1, size):
            if values[j] % values[i] == 0:
                edges[i] |= 1 << j
                edges[j] |= 1 << i
    limit = (1 << (bound + 1)) - 1

    @lru_cache(maxsize=256)
    def sums(mask):
        if monotonic() >= deadline:
            raise TimeoutError
        if not mask:
            return 1
        isolated = 0
        highest_degree = 0
        pivot = -1
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            i = bit.bit_length() - 1
            degree = (edges[i] & mask).bit_count()
            if degree == 0:
                isolated |= bit
            elif degree > highest_degree:
                highest_degree = degree
                pivot = i
            remaining ^= bit
        if isolated:
            reachable = sums(mask ^ isolated)
            while isolated:
                bit = isolated & -isolated
                weight = values[bit.bit_length() - 1]
                reachable |= (reachable << weight) & limit
                isolated ^= bit
            return reachable
        rest = mask ^ (1 << pivot)
        without_pivot = sums(rest)
        with_pivot = sums(rest & ~edges[pivot]) << values[pivot]
        return without_pivot | (with_pivot & limit)

    try:
        return sums((1 << size) - 1)
    finally:
        sums.cache_clear()


def direct_small_sums():
    # p(1)+2 through p(9)+2. The next value is p(10)+2 = 44.
    small = [3, 4, 5, 7, 9, 13, 17, 24, 32]
    totals = set()
    for length in range(len(small) + 1):
        for selected in combinations(small, length):
            total = sum(selected)
            if total <= 40 and all(b % a != 0 for a, b in combinations(selected, 2)):
                totals.add(total)
    return totals


def main():
    deadline = monotonic() + 105
    bounds = sorted(set(params['bounds']))
    all_values = shifted_partitions(max([7141, *bounds]))
    small_values = [v for v in all_values if v <= 40]
    small_bits = attainable(small_values, 40, deadline)
    direct = direct_small_sums()
    mismatches = [t for t in range(41) if bool(small_bits & (1 << t)) != (t in direct)]

    witness = [137, 178, 299, 1960, 4567]
    valid = (sum(witness) == 7141 and all(v in all_values for v in witness)
             and all(b % a != 0 for a, b in combinations(sorted(witness), 2)))
    checks = []
    eligible = None
    for bound in bounds:
        values = [v for v in all_values if v <= bound]
        try:
            bits = small_bits if bound == 40 else attainable(values, bound, deadline)
        except TimeoutError:
            break
        packed = bits.to_bytes((bound + 8) // 8, 'little')
        missing = [t for t in range(3, bound + 1) if not (packed[t // 8] & (1 << (t % 8)))]
        checks.append({'bound': bound, 'missing': missing})
        eligible = len(values)

    if mismatches or not valid:
        summary = 'Sanity check failed.'
    elif len(checks) < len(bounds):
        summary = f'Partial run completed {len(checks)} of {len(bounds)} exact coverage checks.'
    else:
        summary = f'Completed {len(checks)} of {len(bounds)} exact coverage checks.'
    return {'summary': summary, 'checks': checks,
            'eligible_at_largest_completed_bound': eligible,
            'direct_subset_check': {'range': [0, 40], 'mismatches': mismatches},
            'witness_7141': {'summands': witness, 'valid': valid}}


with open('result.json', 'w') as output:
    json.dump(main(), output)
