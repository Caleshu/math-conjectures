# MathResearchLab experiment 7232bcf5-b999-4819-8832-39612c5de616
# Search connected length-eleven chains and verify the first lift
# sha256(code) = eabeb6159e0d6003e39885c541e285219fef4733a941ff43f803eded037b3131
# parameters: {"random_seed": 182731, "draw_cap": 40000, "evaluation_cap": 350, "seed_interval_cap": 16000, "lift_interval_cap": 60000, "search_seconds": 58, "total_seconds": 111}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import random
import time
from collections import Counter, defaultdict
import numpy as np

params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()
search_end = start + params['search_seconds']
finish = start + params['total_seconds']
rng = random.Random(params['random_seed'])

class Budget(Exception):
    pass

class SizeCap(Exception):
    pass

def check_time(deadline):
    if time.monotonic() >= deadline:
        raise Budget()

def length(p):
    return sum(a > b for i, a in enumerate(p) for b in p[i+1:])

def swap(p, i, j):
    a = list(p)
    a[i], a[j] = a[j], a[i]
    return tuple(a)

def inverse(p):
    a = [0] * len(p)
    for i, value in enumerate(p):
        a[value] = i
    return tuple(a)

def cycles(p):
    labels = [-1] * len(p)
    parts = []
    for i in range(len(p)):
        if labels[i] >= 0:
            continue
        part = []
        j = i
        while labels[j] < 0:
            labels[j] = len(parts)
            part.append(j + 1)
            j = p[j]
        parts.append(part)
    return labels, parts

def desc(p):
    return {i for i in range(len(p)-1) if p[i] > p[i+1]}

def bruhat(u, v):
    return all(all(a <= b for a, b in zip(sorted(u[:k]), sorted(v[:k]))) for k in range(1, len(u)+1))

def display(p):
    return [i+1 for i in p]

def verify_chain(path):
    u, v = path[0], path[-1]
    n = len(u)
    comp = list(range(n))
    edges = []
    for a, b in zip(path, path[1:]):
        i, j = [h for h in range(n) if a[h] != b[h]]
        assert swap(a, i, j) == b and length(b) == length(a) + 1
        old, new = comp[j], comp[i]
        comp = [new if c == old else c for c in comp]
        edges.append([i+1, j+1])
    inv = inverse(u)
    rel = tuple(inv[t] for t in v)
    deletable = [i+1 for i, t in enumerate(u) if v[i] == t and sum(h >= t for h in u[:i]) == sum(h >= t for h in v[:i])]
    assert bruhat(u, v)
    return dict(lower=display(u), upper=display(v), lengths=[length(u), length(v)], bruhat=True, chain_position_transpositions=edges, graph_components=len(set(comp)), relative_cycles=cycles(rel)[1], deletable_positions=deletable)

def interval(u, w, cap, deadline):
    # A permutation is in the interval exactly when every value-prefix set
    # (the values in its first k positions) passes both sorted-prefix tests.
    n = len(u)
    full = (1 << n) - 1
    lower = [sorted(u[:k]) for k in range(n+1)]
    upper = [sorted(w[:k]) for k in range(n+1)]
    counts = [0] * (full+1)
    options = [[] for _ in counts]
    counts[full] = 1
    for mask in range(full-1, -1, -1):
        k = mask.bit_count()
        values = [j for j in range(n) if mask & (1 << j)]
        if any(not (a <= b <= c) for a, b, c in zip(lower[k], values, upper[k])):
            continue
        for j in range(n):
            bit = 1 << j
            if mask & bit == 0 and counts[mask | bit]:
                options[mask].append((j, mask | bit))
                counts[mask] += counts[mask | bit]
    assert counts[0] > 0
    if counts[0] > cap:
        raise SizeCap(counts[0])
    rows = []
    def emit(mask, prefix):
        if mask == full:
            rows.append(prefix)
            if len(rows) % 1024 == 0:
                check_time(deadline)
            return
        for j, nxt in options[mask]:
            emit(nxt, prefix + (j,))
    emit(0, ())
    assert len(rows) == counts[0]
    return rows

def kl(u, w, cap, deadline):
    # Dyer's increasing Bruhat path formula for ordinary R-polynomials.
    # Each upward reflection edge of length jump 2h+1 weighs q^h(q-1).
    # Transport down in reverse reflection order to apply the R matrix.
    rows = interval(u, w, cap, deadline)
    n = len(u)
    top = length(w)
    gaps = [top-length(p) for p in rows]
    gap = top-length(u)
    if gap == 0:
        return [1], 1
    width = (gap-1)//2 + 1
    codes = [sum(v << (4*i) for i, v in enumerate(p)) for p in rows]
    index = {c:r for r, c in enumerate(codes)}
    groups = defaultdict(lambda: ([], []))
    for r, p in enumerate(rows):
        if r % 256 == 0:
            check_time(deadline)
        for i in range(n):
            for j in range(i+1, n):
                if p[i] <= p[j]:
                    continue
                delta = p[i] ^ p[j]
                b = index.get(codes[r] ^ (delta << (4*i)) ^ (delta << (4*j)))
                if b is None:
                    continue
                jump = gaps[b]-gaps[r]
                assert jump > 0 and jump % 2 == 1
                h = jump//2
                if h < width:
                    src, dst = groups[i,j,h]
                    src.append(r)
                    dst.append(b)
    edges = [(h, np.asarray(groups[i,j,h][0]), np.asarray(groups[i,j,h][1])) for i,j,h in sorted(groups, reverse=True)]
    ranks = [np.flatnonzero(np.asarray(gaps) == k) for k in range(gap+1)]
    assert len(ranks[0]) == len(ranks[-1]) == 1
    # Object arrays use exact Python integers. Only degrees below width can
    # affect the requested polynomial because edge weights have no poles.
    accum = np.zeros((len(rows), width), dtype=object)
    for k in range(gap+1):
        check_time(deadline)
        ix = ranks[k]
        keep = 1 if k == 0 else (k-1)//2+1
        # q^k P(q^-1) has zero coefficients in these degrees for k>0.
        # accum holds the contribution of all strict upper endpoints.
        coeff = np.ones((1,1), dtype=object) if k == 0 else -accum[ix,:keep]
        assert np.all(coeff[:,0] == 1) and np.all(coeff >= 0)
        if k == gap:
            return [int(c) for c in coeff[0]], len(rows)
        work = np.zeros_like(accum)
        work[ix,:keep] = coeff
        for h, src, dst in edges:
            vals = work[src,:width-h]
            work[dst,h:] -= vals
            if h+1 < width:
                work[dst,h+1:] += vals[:,:-1]
        accum += work

def sample_chain():
    blocks = rng.choice(((5,5), (5,5), (5,5), (4,6), (4,2,4), (3,4,3), (4,3,3)))
    u = ()
    for size in blocks:
        offset = len(u)
        u += tuple(range(offset+size-1, offset-1, -1))
    perturb = rng.choice((0,0,0,1,2,3))
    for _ in range(perturb):
        i = rng.randrange(9)
        if rng.randrange(2):
            u = swap(u, i, i+1)
        else:
            u = inverse(swap(inverse(u), i, i+1))
    p = u
    inv = inverse(u)
    path = [p]
    comp = list(range(10))
    splits = 0
    for _ in range(11):
        cyc, _parts = cycles(tuple(inv[t] for t in p))
        choices = []
        for i, a in enumerate(p):
            limit = 10
            for j in range(i+1, 10):
                b = p[j]
                if a < b < limit:
                    # A new record minimum above a makes this a Bruhat cover.
                    limit = b
                    if comp[i] != comp[j] or (splits < 2 and cyc[i] == cyc[j]):
                        choices.append((i,j))
        if not choices:
            return None
        i,j = rng.choice(choices)
        old, new = comp[j], comp[i]
        if old == new:
            splits += 1
        else:
            comp = [new if c == old else c for c in comp]
        p = swap(p, i, j)
        path.append(p)
    assert splits == 2 and len(set(comp)) == 1
    return path

def lift(path):
    u, v = path[0], path[-1]
    k = next(i for i in range(len(u)) if u[i] != v[i])
    assert u[k] < v[k]
    threshold = u[k]+1
    def embed(p):
        shifted = tuple(t + int(t >= threshold) for t in p)
        return shifted[:k] + (threshold, len(u)+1) + shifted[k:]
    middle = [embed(p) for p in path]
    x = swap(middle[0], k+1, k+2)
    w = swap(middle[-1], k, k+1)
    return k, [x] + middle + [w]

# The singular S4 interval and its common-descent translate exercise the
# coefficient extraction. A second check exercises the insertion and chain.
u4, w4 = (0,2,1,3), (2,3,0,1)
p4, _ = kl(u4, w4, 100, search_end)
t4, _ = kl(swap(u4,1,2), swap(w4,1,2), 100, search_end)
assert p4 == [1,1] and t4 == [1,0]
small_path = [u4, (2,0,1,3), (2,1,0,3), w4]
# Choose actual successive covers ending at w4.
small_path[-2] = (2,0,3,1)
small_audit = verify_chain(small_path)
si, lifted_small = lift(small_path)
verify_chain(lifted_small)
sl, sh = lifted_small[0], lifted_small[-1]
p6, _ = kl(sl, sh, 720, search_end)
t6, _ = kl(swap(sl,si,si+1), swap(sh,si,si+1), 720, search_end)
assert p6[-1] == 1 and t6[-1] == 0

out = dict(parameters=params, family='Lower endpoint is a direct sum of decreasing blocks of sizes (5,5), (4,6), (4,2,4), (3,4,3), or (4,3,3), followed by zero to three adjacent position or value swaps. Upper endpoint comes from an eleven-cover random ascent allowing only component joins or at most two cycle splits. Retain pairs for which both upper descent sets are contained in the corresponding lower descent sets.', sampling='Heuristic, with deduplication. Permutations and chain positions in the output are one-based.', polynomial_method='Exact integer increasing-path R-polynomial transform and triangular Kazhdan–Lusztig inversion. Coefficients are listed from constant term upwards.', formula_attribution={'name':'Dyer increasing-path formula for R-polynomials', 'author_support':'recalled_literature'}, sanity={'S4_polynomials':[p4,t4], 'S6_lift_polynomials':[p6,t6]}, hit=None, best=None)
seen = set()
stats = Counter(draws=0, completed_chains=0, distinct_after_descent_filters=0, eligible_evaluated=0, seed_interval_cap_skips=0, interrupted_seed_evaluations=0)
hist = Counter()
reason = 'draw cap'
for _ in range(params['draw_cap']):
    if time.monotonic() >= search_end:
        reason = 'search wall-clock cap'
        break
    if stats['eligible_evaluated'] >= params['evaluation_cap']:
        reason = 'seed evaluation cap'
        break
    stats['draws'] += 1
    path = sample_chain()
    if path is None:
        continue
    stats['completed_chains'] += 1
    u, v = path[0], path[-1]
    if not desc(v) <= desc(u) or not desc(inverse(v)) <= desc(inverse(u)) or (u,v) in seen:
        continue
    seen.add((u,v))
    stats['distinct_after_descent_filters'] += 1
    audit = verify_chain(path)
    assert audit['lengths'][1]-audit['lengths'][0] == 11 and audit['graph_components'] == 1 and len(audit['relative_cycles']) == 3
    try:
        poly, size = kl(u, v, params['seed_interval_cap'], search_end)
    except SizeCap:
        stats['seed_interval_cap_skips'] += 1
        continue
    except Budget:
        stats['interrupted_seed_evaluations'] += 1
        reason = 'search wall-clock cap'
        break
    mu = poly[5]
    stats['eligible_evaluated'] += 1
    hist[mu] += 1
    if out['best'] is None or mu > out['best']['q5']:
        out['best'] = dict(q5=mu, polynomial=poly, interval_size=size, verification=audit)
    if mu < 5:
        continue
    reason = 'seed hit'
    k, big_path = lift(path)
    x, w = big_path[0], big_path[-1]
    xs, ws = swap(x,k,k+1), swap(w,k,k+1)
    big = verify_chain(big_path)
    assert big['lengths'][1]-big['lengths'][0] == 13 and big['graph_components'] == 1 and len(big['relative_cycles']) == 3 and not big['deletable_positions']
    assert k in desc(x) & desc(w) and bruhat(xs,ws) and length(ws)-length(xs) == 13
    hit = dict(seed=audit, seed_polynomial=poly, seed_q5=mu, seed_interval_size=size, lift=big, common_right_descent=k+1, xs=display(xs), ws=display(ws), translated_lengths=[length(xs),length(ws)], translated_bruhat=True)
    out['hit'] = hit
    try:
        for label, a, b in [('original',x,w), ('translated',xs,ws)]:
            p, count = kl(a, b, params['lift_interval_cap'], finish)
            hit[label] = dict(polynomial=p, q6=p[6], interval_size=count)
        drop = hit['original']['q6']-hit['translated']['q6']
        hit.update(drop=drop, proposed_identity_verified=(drop == mu and hit['translated']['q6'] == 0), counterexample_verified=(hit['original']['q6'] > 0 and drop > 4))
    except SizeCap as err:
        hit['verification_incomplete'] = {'interval_size':err.args[0], 'cap':params['lift_interval_cap'], 'pair':label}
    except Budget:
        hit['verification_incomplete'] = {'cause':'total wall-clock cap', 'pair':label}
    break
out.update(counts=dict(stats), q5_histogram=dict(sorted(hist.items())), stopping_condition=reason, elapsed_seconds=round(time.monotonic()-start,3))
num = stats['eligible_evaluated']
if out['hit'] is None:
    out['summary'] = f'No hit among {num} distinct eligible seeds with exact coefficient evaluations. Stopped at {reason}.'
elif 'drop' in out['hit']:
    h = out['hit']
    out['summary'] = f"Seed coefficient {h['seed_q5']} found after {num} evaluations. The directly evaluated lift has coefficients {h['original']['q6']} and {h['translated']['q6']}, giving drop {h['drop']}."
else:
    out['summary'] = f'Seed hit after {num} evaluations. Direct lift verification reached a reported cap.'
with open('result.json','w') as f:
    json.dump(out, f)
