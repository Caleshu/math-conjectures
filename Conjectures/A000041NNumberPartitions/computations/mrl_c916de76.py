# MathResearchLab experiment c916de76-2ff3-4cc3-b411-4c813259bf4b
# Exact greedy trace from the 27 seed indices and index 58
# sha256(code) = 2d5516dc536682716710e633821b817ad9ad4a9585c3a72c9a3d0b9c3079b869
# parameters: {"start": 1000000, "target": 10000000000000000000000000000000000000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from bisect import bisect_right

params = json.load(open(os.environ['MRL_PARAMS']))
start = params['start']
target = params['target']
seed = [3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 19, 21, 22, 23, 24, 26, 29, 30, 31, 37, 38, 43, 47, 49, 58]


def partitions(limit):
    counts = [1] + [0] * limit
    for part in range(1, limit + 1):
        for n in range(part, limit + 1):
            counts[n] += counts[n - part]
    return counts


# p(n) is nondecreasing by adjoining a part 1. One value above the
# terminal cutoff certifies that the table contains every candidate.
limit = 64
p = partitions(limit)
while p[-1] + 2 <= target - 47:
    limit *= 2
    p = partitions(limit)
w = [v + 2 for v in p]


def first_comparable_pair(indices):
    for pos, i in enumerate(indices):
        for j in indices[:pos]:
            if w[i] % w[j] == 0 or w[j] % w[i] == 0:
                return [j, i]
    return None


def first_missing(indices, lo, hi):
    sums = 1
    for i in indices:
        sums |= sums << w[i]
    missing = (~(sums >> lo)) & ((1 << (hi - lo + 1)) - 1)
    return lo + (missing & -missing).bit_length() - 1 if missing else None


def run(increasing):
    chosen = seed.copy()
    M = start
    trace = []
    minimum = None
    conflict = None
    # Index 52 is only an auxiliary coverage certificate. It never
    # filters candidates or changes the specified greedy choices.
    interval_certified_through = start if augmented_seed_ok else None
    while M < target:
        lower = max(chosen) + 1 if increasing else 1
        upper = bisect_right(w, M - 47) - 1
        eligible = []
        blockers = []
        for k in range(lower, upper + 1):
            divisor = next((i for i in chosen if w[k] % w[i] == 0), None)
            if divisor is None:
                eligible.append(k)
            else:
                blockers.append([k, divisor])
        if minimum is None or len(eligible) < minimum['count']:
            minimum = dict(M=M, lower_k=lower, upper_k=upper, count=len(eligible), eligible_k=eligible, blocked_k_and_divisor_k=blockers)
        k = eligible[-1] if eligible else None
        trace.append(dict(M=M, count=len(eligible), chosen_k=k))
        if k is None:
            break
        # For a backward choice the one-way test can miss divisibility.
        reverse = next((i for i in chosen if w[i] % w[k] == 0), None)
        if reverse is not None and conflict is None:
            conflict = dict(M=M, divisor_k=k, multiple_k=reverse)
        if interval_certified_through == M and reverse is None and w[k] % w[52] and w[52] % w[k]:
            interval_certified_through += w[k]
        chosen.append(k)
        M += w[k]
    reached = M >= target
    status = 'reached_target' if reached else 'empty_window'
    return dict(status=status, final_M=M, reached_with_antichain=reached and conflict is None, first_antichain_conflict=conflict, minimum_window=minimum, trace=trace, interval_from_48_certified_through=interval_certified_through)


small_ok = p[:11] == [1, 1, 2, 3, 5, 7, 11, 15, 22, 30, 42]
seed_conflict = first_comparable_pair(seed)
seed_ok = small_ok and w[58] == 715222 and seed_conflict is None
checks = dict(small_partition_check=small_ok, seed_weights=[w[k] for k in seed], seed_conflict=seed_conflict, table_limit=limit, last_table_weight=w[-1])
result = dict(checks=checks, start=start, target=target)
if not seed_ok:
    result['summary'] = 'Seed or partition sanity check failed. No greedy conclusion.'
else:
    augmented = seed + [52]
    aug_conflict = first_comparable_pair(augmented)
    aug_missing = first_missing(augmented, 48, start)
    augmented_seed_ok = aug_conflict is None and aug_missing is None
    checks.update(seed_first_missing_from_48=first_missing(seed, 48, start), augmented_seed_conflict=aug_conflict, augmented_seed_first_missing_from_48=aug_missing)
    result['runs'] = {name: run(flag) for name, flag in [('increasing', True), ('literal', False)]}
    result['summary'] = ' | '.join(f"{name}: {r['status']}, final M={r['final_M']}, minimum eligible={r['minimum_window']['count']} at M={r['minimum_window']['M']}" for name, r in result['runs'].items())
    result['author_support'] = 'proved_here'
    result['justification'] = 'After the pass for part d, counts[n] counts partitions using parts at most d: each partition either omits d or removes one d and leaves a partition counted at n-d in the current pass. Each window scans every index in its stated range and tests every candidate against the chosen divisors. The largest survivor gives the next step. In the minimum window each rejected index has a divisor witness. The auxiliary interval certificate starts from exact subset sums, obtained by adjoining each weight once. While every new weight b is compatible with that entire antichain, [48,M] and [48+b,M+b] overlap or adjoin because b is at most M-47. This certifies precisely the reported interval bound by this argument. The trace gives no bound on the eligible count in future windows.'
with open('result.json', 'w') as out:
    json.dump(result, out)
