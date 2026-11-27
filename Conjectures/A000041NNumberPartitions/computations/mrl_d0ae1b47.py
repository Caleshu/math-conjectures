# MathResearchLab experiment d0ae1b47-5ad0-4d1d-aa41-13c7c860278f
# All sums of pairwise nondividing shifted partition numbers
# sha256(code) = 1c8662e51e772ccaec2692c6a01ea1891fe72de2c5ceadffd72596bab2b39bc4
# parameters: {"bounds": [40, 7140, 50000, 250000]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from functools import lru_cache
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
bounds = sorted(set(int(b) for b in params['bounds']))
assert bounds and 3 <= bounds[0] <= bounds[-1] <= 250000
deadline = monotonic() + 85

def candidates(bound):
    limit = 8
    while True:
        p = [1] + [0] * limit
        for part in range(1, limit + 1):
            for n in range(part, limit + 1):
                p[n] += p[n-part]
        if p[-1] + 2 > bound:
            return [(k, p[k] + 2) for k in range(1, limit + 1) if p[k] + 2 <= bound]
        limit *= 2

def solve(bound):
    items = candidates(bound)
    weights = [w for _, w in items]
    size = len(weights)
    full = (1 << size) - 1
    cap = (1 << (bound + 1)) - 1
    neighbors = [0] * size
    for j, w in enumerate(weights):
        for i in range(j):
            if w % weights[i] == 0:
                neighbors[i] |= 1 << j
                neighbors[j] |= 1 << i

    @lru_cache(maxsize=256)
    def sums(mask):
        if monotonic() >= deadline:
            raise TimeoutError
        pivot = -1
        max_degree = 0
        vertices = mask
        while vertices:
            bit = vertices & -vertices
            vertices ^= bit
            i = bit.bit_length() - 1
            degree = (neighbors[i] & mask).bit_count()
            if degree > max_degree:
                pivot, max_degree = i, degree
        if pivot < 0:
            bits = 1
            while mask:
                bit = mask & -mask
                mask ^= bit
                w = weights[bit.bit_length() - 1]
                bits |= (bits << w) & cap
            return bits
        rest = mask ^ (1 << pivot)
        omit = sums(rest)
        take = sums(rest & ~neighbors[pivot])
        return omit | ((take << weights[pivot]) & cap)

    try:
        reachable = sums(full)
        # Independently inspect every subset that could contribute up to 40.
        small_bound = min(40, bound)
        small_weights = [w for w in weights if w <= small_bound]
        direct = 0
        for mask in range(1 << len(small_weights)):
            chosen = [w for i, w in enumerate(small_weights) if mask & (1 << i)]
            total = sum(chosen)
            if total <= small_bound and all(b % a for i, a in enumerate(chosen) for b in chosen[i+1:]):
                direct |= 1 << total
        assert reachable & ((1 << (small_bound + 1)) - 1) == direct
        if bound >= 8:
            assert weights[:4] == [3, 4, 5, 7]
            assert direct & (1 << 8) and not direct & (1 << 6)

        packed = reachable.to_bytes((bound + 8) // 8, 'little')
        missing = [n for n in range(3, bound + 1) if not (packed[n // 8] & (1 << (n % 8)))]
        result = {'bound': bound, 'candidate_count': size, 'missing': missing, 'direct_subset_check_through': small_bound, 'witnesses': {}}
        for target in sorted({bound, 7141}):
            if target > bound or not ((reachable >> target) & 1):
                continue
            mask, remaining = full, target
            chosen = []
            try:
                while remaining:
                    assert mask
                    bit = mask & -mask
                    i = bit.bit_length() - 1
                    mask ^= bit
                    if (sums(mask) >> remaining) & 1:
                        continue
                    chosen.append(items[i])
                    remaining -= weights[i]
                    assert remaining >= 0
                    mask &= ~neighbors[i]
            except TimeoutError:
                result['witness_recovery_stopped_at'] = target
                break
            values = [w for _, w in chosen]
            assert sum(values) == target and all(b % a and a % b for i, a in enumerate(values) for b in values[i+1:])
            result['witnesses'][str(target)] = [{'k': k, 'value': w} for k, w in chosen]
        return result
    finally:
        sums.cache_clear()

rows = []
for bound in bounds:
    try:
        rows.append(solve(bound))
    except TimeoutError:
        break
last = rows[-1]['bound'] if rows else None
result = {'summary': f'Completed {len(rows)} of {len(bounds)} exact coverage checks. Largest completed bound: {last}.', 'requested_bounds': bounds, 'complete': len(rows) == len(bounds), 'checks': rows}
with open('result.json', 'w') as out:
    json.dump(result, out)
