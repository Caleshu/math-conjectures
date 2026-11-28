# MathResearchLab experiment 25d43eba-a974-4126-bd97-93b60c9c8738
# Replay the two-sided greedy and audit its final antichain
# sha256(code) = 0a0388dad17aeb86f57ca054a4e6bf4f2168fd8c20ef68a6463a061abf7f3f4b
# parameters: {"target": "10000000000000000000000000000000000000000"}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from bisect import bisect_right
from time import monotonic

params = json.load(open(os.environ["MRL_PARAMS"]))

def run():
    deadline = monotonic() + 100
    target = int(params['target'])
    initial_M = 1817584
    assert initial_M < target <= 10**40
    seed = [3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 19, 21, 22, 23, 24, 26, 29, 30, 31, 37, 38, 43, 47, 49, 52, 54, 58]

    # After processing part d, p[n] counts partitions using parts at most d.
    bound = 64
    while True:
        p = [1] + [0] * bound
        for d in range(1, bound + 1):
            for n in range(d, bound + 1):
                p[n] += p[n - d]
            if d % 64 == 0 and monotonic() >= deadline:
                return {'summary': 'Partial partition table. No greedy state was tested.', 'bound': bound, 'last_part_processed': d}
        if p[bound] + 2 > target - 47:
            break
        bound *= 2
    assert p[:11] == [1, 1, 2, 3, 5, 7, 11, 15, 22, 30, 42]
    w = [v + 2 for v in p]
    assert all(w[k] < w[k + 1] for k in range(1, bound))

    def audit(indices):
        violations = []
        checked = 0
        for i in indices:
            for j in indices:
                if i != j:
                    checked += 1
                    if w[j] % w[i] == 0:
                        violations.append({'divisor_index': i, 'multiple_index': j, 'quotient': w[j] // w[i]})
        assert checked == len(indices) * (len(indices) - 1)
        return {'ordered_pairs_checked': checked, 'violations': violations}

    # Bit t records the existence of a seed subset with sum t.
    sums = 1
    for k in seed:
        sums |= sums << w[k]
    width = initial_M - 48 + 1
    mask = (1 << width) - 1
    missing = mask & ~(sums >> 48)
    seed_check = audit(seed)
    seed_check['first_missing_in_interval'] = 48 + (missing & -missing).bit_length() - 1 if missing else None
    seed_check['weights'] = [w[k] for k in seed]
    if missing or seed_check['violations']:
        return {'summary': 'The specified starting state failed validation.', 'seed_indices': seed, 'seed_check': seed_check}

    chosen = seed.copy()
    used = set(chosen)
    M = initial_M
    min_window = None
    min_all = None
    first_empty = None
    trace = []
    status = 'reached_target'
    while M < target:
        if monotonic() >= deadline:
            status = 'partial_time_limit'
            break
        limit = M - 47
        stop = bisect_right(w, limit, lo=1)
        eligible = []
        for k in range(1, stop):
            if k not in used and all(w[k] % w[j] != 0 and w[j] % w[k] != 0 for j in chosen):
                eligible.append(k)
        top = [k for k in eligible if 2 * w[k] > limit]
        if min_window is None or len(top) < min_window['count']:
            min_window = {'count': len(top), 'M_before': M, 'inclusive_weight_bounds': [limit // 2 + 1, limit], 'eligible_indices': top}
        min_all = len(eligible) if min_all is None else min(min_all, len(eligible))
        if not top and first_empty is None:
            blocked = []
            for k in range(bisect_right(w, limit // 2, lo=1), stop):
                j = next(j for j in chosen if w[k] % w[j] == 0 or w[j] % w[k] == 0)
                blocked.append([k, j])
            first_empty = {'M_before': M, 'candidate_and_blocking_chosen_index': blocked}
        best = eligible[-1] if eligible else None
        trace.append({'chosen_k': best, 'top_count': len(top)})
        if best is None:
            status = 'no_eligible_index'
            break
        M += w[best]
        chosen.append(best)
        used.add(best)

    final_check = audit(chosen)
    count = None if min_window is None else min_window['count']
    if first_empty is not None or status == 'no_eligible_index' or final_check['violations']:
        verdict = 'false'
    elif status == 'reached_target':
        verdict = 'true'
    else:
        verdict = 'undecided'
    return {
        'summary': f'Finite trajectory claim {verdict}. Status {status}. Minimum top-window count observed {count}. Final audit found {len(final_check["violations"])} divisibilities in {final_check["ordered_pairs_checked"]} ordered pairs.',
        'author_support': 'proved_here',
        'justification': 'The ascending coin-change recurrence counts partitions by the multiplicity of each allowed part. Appending a part 1 injects partitions of k into partitions of k+1, so the table endpoint rules out every omitted index at every tested state. The seed bit shifts enumerate its subset sums. Each step examines every positive index within the upper limit, tests both divisibility directions, and chooses the largest survivor. The final audit independently tests every ordered pair. If [48,M] is covered and the selected weight is b <= M-47, then the translated interval [48+b,M+b] starts at or before M+1, proving coverage through M+b.',
        'target': target, 'initial_M': initial_M, 'status': status, 'finite_claim': verdict,
        'partition_table_last_index': bound, 'partition_table_last_weight': w[bound],
        'seed_indices': seed, 'seed_check': seed_check, 'states_tested': len(trace),
        'trace_in_step_order': trace, 'minimum_top_window': min_window,
        'minimum_eligible_count_under_full_limit': min_all, 'first_empty_top_window': first_empty,
        'final_M': M, 'final_indices': chosen, 'final_weights': [w[k] for k in chosen],
        'final_antichain_check': final_check
    }

with open('result.json', 'w') as out:
    json.dump(run(), out)
