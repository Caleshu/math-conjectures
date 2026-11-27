# MathResearchLab experiment 31b15f25-207f-4dfa-be34-cca892c6b2d6
# Exact coefficient drops for pairs with common descents inside four triples
# sha256(code) = 8a0241fac45412575ceae5f5552616ea4ba3f2c809ca0d4954d66feb2fa62775
# parameters: {"seconds": 90, "interval_cap": 4500, "seed": 130412}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import random
import time
from bisect import bisect_right
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import permutations

params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()
deadline = start + min(105.0, float(params['seconds']))
node_cap = int(params['interval_cap'])
rng = random.Random(params['seed'])

class TimeLimit(Exception):
    pass

class IntervalLimit(Exception):
    pass

class WitnessFound(Exception):
    pass

def check_time():
    if time.monotonic() >= deadline:
        raise TimeLimit

def inverse(p):
    ans = [0] * len(p)
    for i, v in enumerate(p):
        ans[v] = i
    return tuple(ans)

def swap(p, i, j):
    a = list(p)
    a[i], a[j] = a[j], a[i]
    return tuple(a)

def desc(p):
    return {i for i in range(len(p) - 1) if p[i] > p[i + 1]}

def length(p):
    return sum(a > b for i, a in enumerate(p) for b in p[i + 1:])

def cycles(p):
    seen = set()
    count = 0
    for i in range(len(p)):
        if i not in seen:
            count += 1
            while i not in seen:
                seen.add(i)
                i = p[i]
    return count

def relative(x, w):
    inv = inverse(x)
    return tuple(inv[v] for v in w)

def endpoint_family(n, block):
    # The inverse descents require values in each block to appear largest first.
    assert n % block == 0
    left = [block] * (n // block)
    prefix = []
    def visit():
        if len(prefix) == n:
            yield tuple(prefix)
            return
        for group, remaining in enumerate(left):
            if remaining == 0:
                continue
            v = group * block + remaining - 1
            if len(prefix) % block and prefix[-1] < v:
                continue
            prefix.append(v)
            left[group] -= 1
            yield from visit()
            left[group] += 1
            prefix.pop()
    yield from visit()

@lru_cache(None)
def masks_by_size(n):
    layers = [[] for _ in range(n + 1)]
    for m in range(1 << n):
        layers[m.bit_count()].append(m)
    return layers

@lru_cache(None)
def sorted_values(mask):
    return tuple(i for i in range(mask.bit_length()) if mask & (1 << i))

def dominated(a, b):
    # Callers supply masks with equal cardinality.
    return all(i <= j for i, j in zip(sorted_values(a), sorted_values(b)))

def prefixes(p):
    out = [0]
    for v in p:
        out.append(out[-1] | (1 << v))
    return out

def uncompressible(x, w, px, pw):
    return all(a != b or (px[i] >> a).bit_count() != (pw[i] >> a).bit_count()
               for i, (a, b) in enumerate(zip(x, w)))

def interval(x, w):
    # The sorted-prefix criterion tests both Bruhat bounds at each depth.
    n = len(x)
    lo, hi = prefixes(x), prefixes(w)
    allowed = [{m for m in layer if dominated(lo[k], m) and dominated(m, hi[k])}
               for k, layer in enumerate(masks_by_size(n))]
    full = (1 << n) - 1
    lengths = {}
    path = []
    visits = 0
    def visit(mask, inv):
        nonlocal visits
        visits += 1
        if visits % 512 == 0:
            check_time()
        if mask == full:
            if len(lengths) >= node_cap:
                raise IntervalLimit
            lengths[tuple(path)] = inv
            return
        unused = full ^ mask
        choices = unused
        layer = allowed[len(path) + 1]
        while choices:
            bit = choices & -choices
            choices -= bit
            if mask | bit in layer:
                path.append(bit.bit_length() - 1)
                visit(mask | bit, inv + (unused & (bit - 1)).bit_count())
                path.pop()
    visit(0, 0)
    assert x in lengths and w in lengths
    return lengths

@lru_cache(None)
def reflections(n):
    return tuple((i, j) for i in range(n) for j in range(i + 1, n))

def connected(x, w, lengths):
    n = len(x)
    part = list(range(n))
    p = x
    rel = tuple(range(n))
    old_cycles = n
    internal_joins = 0
    joins = 0
    splits = 0
    while p != w:
        for i, j in reflections(n):
            if p[i] >= p[j]:
                continue
            y = swap(p, i, j)
            if lengths.get(y) == lengths[p] + 1:
                break
        else:
            raise AssertionError('No saturated-chain continuation')
        rel = swap(rel, i, j)
        new_cycles = cycles(rel)
        same = part[i] == part[j]
        if new_cycles < old_cycles:
            joins += 1
            internal_joins += int(same)
        else:
            assert same and new_cycles == old_cycles + 1
            splits += 1
        if not same:
            a, b = part[i], part[j]
            part = [a if c == b else c for c in part]
        old_cycles = new_cycles
        p = y
    assert rel == relative(x, w)
    answer = len(set(part)) == 1
    if n == 12 and lengths[w] - lengths[x] == 13 and cycles(rel) == 3:
        assert (joins, splits) == (11, 2)
        assert answer == (internal_joins == 0)
    return answer

def kl(x, w, lengths):
    # Dyer's increasing-path formula for ordinary R-polynomials gives an
    # upward reflection edge of length jump j the weight q^((j-1)/2)*(q-1).
    # For each p, store suffix sums over the allowable first reflection.
    # Each path ending at z contributes its weight times P_{z,w}.
    top = lengths[w]
    degree = max(0, (top - lengths[x] - 1) // 2)
    width = degree + 1
    zero = (0,) * width
    order = reflections(len(w))
    table = {}
    for index, p in enumerate(sorted(lengths, key=lengths.get, reverse=True)):
        if index % 32 == 0:
            check_time()
        keys = [len(order)]
        suffix = [zero]
        total = [0] * width
        for r in range(len(order) - 1, -1, -1):
            i, j = order[r]
            if p[i] >= p[j]:
                continue
            y = swap(p, i, j)
            if y not in lengths:
                continue
            shift = (lengths[y] - lengths[p] - 1) // 2
            if shift > degree:
                continue
            ykeys, ysums = table[y]
            term = ysums[bisect_right(ykeys, r)]
            for k in range(width - shift):
                total[k + shift] -= term[k]
                if k + shift + 1 < width:
                    total[k + shift + 1] += term[k]
            keys.append(r)
            suffix.append(tuple(total))
        # q^d P_{p,w}(1/q) = P_{p,w}(q) + sum_{z>p} R_{p,z} P_{z,w}.
        # The left side vanishes through degree floor((d-1)/2) for d>0.
        if p == w:
            poly = (1,) + zero[1:]
        else:
            bound = (top - lengths[p] - 1) // 2
            poly = tuple(-total[k] if k <= bound else 0 for k in range(width))
        assert poly[0] == 1
        if p == x:
            return poly
        table[p] = (keys[::-1], [tuple(a + b for a, b in zip(row, poly))
                                 for row in reversed(suffix)])
    raise AssertionError('Missing lower endpoint')

def sanity():
    forced = {0, 2}
    brute = {p for p in permutations(range(4)) if forced <= desc(p) and forced <= desc(inverse(p))}
    listed = list(endpoint_family(4, 2))
    assert len(listed) == len(brute) and set(listed) == brute
    e = (0, 1, 2, 3)
    longest = e[::-1]
    whole = interval(e, longest)
    assert len(whole) == 24 and all(length(p) == d for p, d in whole.items())
    assert kl(e, longest, whole) == (1, 0, 0)
    x, w = (0, 2, 1, 3), (2, 3, 0, 1)
    small = interval(x, w)
    assert connected(x, w, small)
    assert kl(x, w, small) == (1, 1)
    ws = swap(w, 1, 2)
    assert kl(e, ws, interval(e, ws)) == (1, 0)
    assert not connected(e, swap(e, 0, 1), interval(e, swap(e, 0, 1)))
    return {'endpoint_generator_matches_brute_force_S4': True, 'full_S4_interval_size': 24,
            'common_descent_drop_for_1324_3412': 1}

def one_line(p):
    return [v + 1 for v in p]

def record(x, w, i, a, b):
    return {'x': one_line(x), 'w': one_line(w), 'descent': i + 1,
            'mu': a, 'shifted_mu': b, 'drop': a - b}

checks = sanity()
family = list(endpoint_family(12, 3))
rng.shuffle(family)
by_length = defaultdict(list)
pref = {}
right = {}
left = {}
for p in family:
    by_length[length(p)].append(p)
    pref[p] = prefixes(p)
    right[p] = desc(p)
    left[p] = desc(inverse(p))
counts = Counter()
mu_hist = Counter()
drop_hist = Counter()
best = None
witness = None
first_skipped = None
status = 'family_exhausted'
try:
    for w in family:
        check_time()
        for x in by_length.get(length(w) - 13, ()):
            check_time()
            counts['length_matched_pairs_visited'] += 1
            # An unshared upper descent implies mu=0 at odd gap 13 by KL
            # descent invariance and the degree bound at gap 12. Inversion
            # symmetry gives the same test for left descents.
            if not right[w] <= right[x] or not left[w] <= left[x]:
                continue
            if cycles(relative(x, w)) != 3:
                continue
            if not uncompressible(x, w, pref[x], pref[w]):
                continue
            if not all(dominated(a, b) for a, b in zip(pref[x], pref[w])):
                continue
            counts['pairs_passing_endpoint_filters'] += 1
            try:
                base = interval(x, w)
            except IntervalLimit:
                counts['base_intervals_over_cap'] += 1
                if first_skipped is None:
                    first_skipped = {'x': one_line(x), 'w': one_line(w), 'stage': 'base'}
                continue
            if not connected(x, w, base):
                counts['disconnected'] += 1
                continue
            a = kl(x, w, base)[6]
            mu_hist[a] += 1
            del base
            if a == 0:
                continue
            assert a > 0
            counts['positive_pairs'] += 1
            all_done = True
            for i in sorted(right[x] & right[w]):
                xs, ws = swap(x, i, i + 1), swap(w, i, i + 1)
                assert length(ws) - length(xs) == 13
                try:
                    shifted = interval(xs, ws)
                except IntervalLimit:
                    counts['shifted_intervals_over_cap'] += 1
                    all_done = False
                    if first_skipped is None:
                        first_skipped = {'x': one_line(x), 'w': one_line(w), 'descent': i + 1, 'stage': 'shifted'}
                    continue
                b = kl(xs, ws, shifted)[6]
                del shifted
                drop_hist[a - b] += 1
                if best is None or a - b > best['drop']:
                    best = record(x, w, i, a, b)
                if a - b >= 5:
                    witness = record(x, w, i, a, b)
                    raise WitnessFound
            counts['positive_pairs_with_every_descent_checked'] += int(all_done)
        counts['upper_endpoints_finished'] += 1
except TimeLimit:
    status = 'time_budget_reached'
except WitnessFound:
    status = 'counterexample_found'

complete = (status == 'family_exhausted' and counts['base_intervals_over_cap'] == 0
            and counts['shifted_intervals_over_cap'] == 0)
result = {'summary': f'{status}. Evaluated {sum(drop_hist.values())} common-descent drops for positive pairs. Complete for the four-triple family: {complete}.',
          'status': status, 'complete_for_selected_family': complete, 'family_size': len(family),
          'parameters': params, 'sanity': checks, 'counts': dict(counts),
          'base_mu_histogram_for_connected_pairs_evaluated': dict(mu_hist),
          'drop_histogram': dict(drop_hist), 'largest_evaluated_drop': best,
          'counterexample': witness, 'first_interval_over_cap': first_skipped,
          'seconds_elapsed': round(time.monotonic() - start, 3)}
with open('result.json', 'w') as out:
    json.dump(result, out)
