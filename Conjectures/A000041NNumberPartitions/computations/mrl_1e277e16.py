# MathResearchLab experiment 1e277e16-025b-49e4-9c76-65aa81a71fe6
# Replay the two-sided greedy and certify its covered endpoint
# sha256(code) = edc857b23c5e1792ef1de8f10f8ec1bc6d0e9371be36e7c487d7a94258432846
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from bisect import bisect_right
from itertools import combinations
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
A = 48
START = 1817584
TARGET = 10**40
REPORTED = 17242681614666977586621263007510624361940
out = {'rows': []}
deadline = monotonic() + 85

def require(ok, message):
    if not ok:
        raise ValueError(message)

def compatible(x, y):
    return x % y != 0 and y % x != 0

def run():
    # After processing part d, p[n] counts partitions of n with all parts <= d.
    limit = 2048
    p = [1] + [0] * limit
    for d in range(1, limit + 1):
        for n in range(d, limit + 1):
            p[n] += p[n-d]
    require(p[:11] == [1,1,2,3,5,7,11,15,22,30,42], 'small partition sanity check failed')
    require(not compatible(12, 4) and not compatible(4, 12) and compatible(4, 9), 'two-sided divisibility sanity check failed')
    w = [v + 2 for v in p]
    # For n >= 1, adjoining a 1 injects partitions of n into those of n+1,
    # missing the singleton part n+1. Thus monotonicity extends beyond the table.
    require(all(w[k] < w[k+1] for k in range(1, limit)) and w[-1] > TARGET, 'partition table does not bracket every pre-crossing ceiling')

    tails = [52, 54, 58]
    if 'seed_indices' in params:
        seed = sorted(params['seed_indices'])
        out['seed_source'] = 'supplied index list'
    else:
        # Recover K from reported seed identifiers, without using any trajectory row.
        # The nine anchors are the reported chosen weights 5,7,9,13,17,24,32,1004,6844.
        anchors = [3,4,5,6,7,8,9,22,31]
        fixed = anchors + tails
        require([w[i] for i in anchors] == [5,7,9,13,17,24,32,1004,6844], 'anchor identification failed')
        pool = [i for i in range(3,50) if i not in fixed and all(compatible(w[i],w[j]) for j in fixed)]
        missing = 30 - len(fixed)
        balance = START + A - sum(w[i] for i in fixed)
        matches = []
        for t, extra in enumerate(combinations(pool, missing)):
            if t % 8192 == 0 and monotonic() > deadline:
                raise ValueError('seed recovery stopped at time budget; supply seed_indices')
            if sum(w[i] for i in extra) == balance and all(compatible(w[i],w[j]) for i,j in combinations(extra,2)):
                matches.append(sorted(fixed + list(extra)))
                if len(matches) == 2:
                    break
        out['seed_candidates_found_capped_at_two'] = matches
        require(len(matches) == 1, 'reported seed identifiers did not determine a unique seed; supply seed_indices')
        seed = matches[0]
        out['seed_source'] = 'unique under reported anchor, index-range, sum, size and compatibility constraints'
    require(len(seed) == len(set(seed)) == 30 and seed[-3:] == tails and all(3 <= k <= 49 for k in seed[:-3]), 'seed index shape differs')
    chosen = list(seed)
    vals = [w[k] for k in chosen]
    out['seed_indices'] = seed
    require(sum(vals) == START + A, 'initial total differs')
    require(all(compatible(x,y) for x,y in combinations(vals,2)), 'seed divisibility failure')
    bits = 1
    for x in vals:
        bits |= bits << x
    length = START - A + 1
    mask = (1 << length) - 1
    holes = mask & ~(bits >> A)
    if holes:
        out['first_seed_gap'] = A + (holes & -holes).bit_length() - 1
    require(holes == 0, 'initial coverage failed')
    out['seed_interval'] = [A, START]

    M = START
    used = set(seed)
    log = params.get('logged_steps')
    if log is not None:
        require(isinstance(log,list), 'logged_steps must be a list of objects with a k field')
    for step in range(1,122):
        if M >= TARGET:
            break
        require(monotonic() < deadline, 'replay stopped at time budget')
        ceiling = M - A + 1
        last = bisect_right(w, ceiling, lo=1) - 1
        eligible = [k for k in range(1,last+1) if k not in used and all(compatible(w[k],x) for x in vals)]
        top_count = sum(2*w[k] > ceiling for k in eligible)
        row = {'step': step, 'M_before': M, 'ceiling': ceiling, 'last_index_in_range': last, 'eligible_count': len(eligible), 'top_count': top_count}
        out['rows'].append(row)
        require(eligible, 'no full-range eligible weight at step ' + str(step))
        k = eligible[-1]
        x = w[k]
        row.update(k=k, w=x, M_after=M+x)
        if top_count == 0:
            # Remainder entries follow the seed order, then the preceding pick order.
            row['fallback_candidate_mod_chosen'] = [x % y for y in vals]
            row['fallback_chosen_mod_candidate'] = [y % x for y in vals]
            require(all(row['fallback_candidate_mod_chosen']) and all(row['fallback_chosen_mod_candidate']), 'fallback divisibility failure')
        require(k not in used and x <= ceiling, 'invalid extension')
        if log is not None and step <= len(log) and 'first_log_difference' not in out:
            entry = log[step-1]
            require(isinstance(entry,dict) and 'k' in entry, 'logged row lacks k')
            fields = ('step','k','w','M_before','M_after','ceiling','eligible_count','top_count')
            diff = {f: {'logged': entry[f], 'replayed': row[f]} for f in fields if f in entry and entry[f] != row[f]}
            if diff:
                detail = {'step': step, 'fields': diff}
                j = entry['k']
                if type(j) is int and 1 <= j <= last:
                    detail['logged_pick_blockers'] = [i for i in chosen if w[j] % w[i] == 0 or w[i] % w[j] == 0]
                else:
                    detail['logged_pick_outside_full_range'] = True
                out['first_log_difference'] = detail
        M += x
        chosen.append(k)
        used.add(k)
        vals.append(x)

    # Audit the completed certificate by an ordered-pair scan and an independent sum.
    bad = [[i,j] for i in chosen for j in chosen if i != j and w[j] % w[i] == 0]
    total = sum(w[k] for k in chosen)
    out.update(final_indices=chosen, final_sum=total, final_M=M, final_ceiling=M-47, ordered_pairs=len(chosen)*(len(chosen)-1), divisible_pairs=bad)
    require(len(chosen) == len(set(chosen)) and not bad, 'final antichain audit failed')
    require(M == total-A, 'final endpoint disagrees with independent sum')
    rows = out['rows']
    minimum = min(r['eligible_count'] for r in rows)
    fallbacks = [r['step'] for r in rows if r['top_count'] == 0]
    prefix = [63,68,71,76,80,85,91,96,101,107,110,115,122,125]
    out.update(certified_interval=[A,M], additions=len(rows), min_full_range_count=minimum, minimum_steps=[r['step'] for r in rows if r['eligible_count'] == minimum], fallback_steps=fallbacks, reported_integer=REPORTED)
    out['checks'] = {
        'first_crossing_on_addition_121': len(rows) == 121 and rows[-1]['M_before'] < TARGET <= M,
        'all_121_counts_positive': len(rows) == 121 and minimum >= 1,
        'minimum_equals_four': minimum == 4,
        'first_14_picks_match': [r['k'] for r in rows[:14]] == prefix,
        'first_fallback_matches_checkpoint': fallbacks[:1] == [30] and rows[29]['M_before'] == 159674704389434,
        'last_pick_equals_1558': rows[-1]['k'] == 1558,
        'M_equals_reported_plus_47': M == REPORTED + 47,
        'M_equals_reported_itself': M == REPORTED}
    out['historical_log_comparison'] = ('not supplied' if log is None else 'length or row mismatch' if len(log) != len(rows) or 'first_log_difference' in out else 'all supplied picks and recognized row fields match')
    out['summary'] = f'Certified integer coverage [48,{M}] by {len(chosen)} pairwise nondividing weights. Across {len(rows)} additions the minimum full-range eligible count was {minimum}. The final pick ceiling is {M-47}.'

try:
    run()
except ValueError as exc:
    out['summary'] = 'Audit stopped: ' + str(exc)
with open('result.json','w') as stream:
    json.dump(out,stream)
