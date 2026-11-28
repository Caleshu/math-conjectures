# MathResearchLab experiment 9e725688-0642-4326-b817-79ef706aa21d
# Threshold check on the remaining gap-eleven representatives
# sha256(code) = 99c63c6edf2d84b2710f4041294ec85914259f826dc5b8053af84aea7008adb0
# parameters: {"start": [260, 2628690], "stop": [3628800, 0], "seconds": 85}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from functools import lru_cache
from itertools import permutations, islice
from math import factorial
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
deadline = monotonic() + min(95.0, float(params.get('seconds', 85)))
N = 10
F = [factorial(i) for i in range(N + 1)]
old = (260, 2628690)
end = (F[N], 0)
start = tuple(params.get('start', old))
stop = tuple(params.get('stop', end))
assert old <= start <= stop <= end
assert all(0 <= t[1] < F[N] for t in (start, stop))

def tick():
    if monotonic() >= deadline:
        raise TimeoutError

def swap(p, i):
    return p[:i] + (p[i + 1], p[i]) + p[i + 2:]

@lru_cache(24000)
def inv(p):
    r = [0] * len(p)
    for i, j in enumerate(p):
        r[j] = i
    return tuple(r)

@lru_cache(24000)
def length(p):
    return sum(b < a for i, a in enumerate(p) for b in p[i + 1:])

@lru_cache(24000)
def desc(p):
    return sum(1 << i for i in range(len(p) - 1) if p[i] > p[i + 1])

@lru_cache(24000)
def prefixes(p):
    mask = 0
    out = [0]
    for j in p:
        mask |= 1 << j
        out.append(mask)
    return tuple(out)

@lru_cache(48000)
def dominated(m, n):
    # Both sets have the same cardinality. Compare their sorted values.
    while m:
        a, b = m & -m, n & -n
        if a > b:
            return False
        m ^= a
        n ^= b
    return True

def below(p, q):
    return all(dominated(m, n) for m, n in zip(prefixes(p), prefixes(q)))

def uppers(a, gap, lo, hi):
    n = len(a)
    target = length(a) + gap
    dr, dl = desc(a), desc(inv(a))
    lower = prefixes(a)
    full = (1 << n) - 1
    word = []
    def visit(used, cost, rank):
        tick()
        k = len(word)
        remaining = n - k
        if rank >= hi or rank + F[remaining] <= lo:
            return
        if cost > target or cost + remaining * (remaining - 1) // 2 < target:
            return
        if not remaining:
            yield rank, tuple(word)
            return
        available = full ^ used
        options = available
        while options:
            bit = options & -options
            options ^= bit
            j = bit.bit_length() - 1
            if k and word[-1] > j and not (dr & (1 << (k - 1))):
                continue
            if j and available & (bit >> 1) and not (dl & (bit >> 1)):
                continue
            nxt = used | bit
            if not dominated(lower[k + 1], nxt) or (k + 1 < n and lower[k + 1] == nxt):
                continue
            smaller = (available & (bit - 1)).bit_count()
            word.append(j)
            yield from visit(nxt, cost + smaller, rank + smaller * F[remaining - 1])
            word.pop()
    yield from visit(0, 0, 0)

def cycles(a, v):
    rel = tuple(inv(a)[j] for j in v)
    seen = set()
    out = []
    for i in range(len(a)):
        if i in seen:
            continue
        c = []
        while i not in seen:
            seen.add(i)
            c.append(i + 1)
            i = rel[i]
        out.append(c)
    return out

def chain_graph(a, v):
    # A first available upward cover below v always extends to a saturated chain.
    p = a
    edges = []
    components = [{i} for i in range(len(a))]
    while p != v:
        tick()
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                if p[i] >= p[j] or any(p[i] < value < p[j] for value in p[i + 1:j]):
                    continue
                q = list(p)
                q[i], q[j] = q[j], q[i]
                q = tuple(q)
                if below(q, v):
                    break
            else:
                continue
            break
        else:
            raise AssertionError('no upward cover below upper endpoint')
        assert length(q) == length(p) + 1
        edges.append([i + 1, j + 1])
        first = next(c for c in components if i in c)
        second = next(c for c in components if j in c)
        if first is not second:
            first.update(second)
            components.remove(second)
        p = q
    return len(components) == 1, edges

def interval(x, u):
    # Permutations are paths through prefix sets lying between the endpoint sets.
    lower, upper = prefixes(x), prefixes(u)
    n = len(x)
    full = (1 << n) - 1
    word = []
    def visit(used):
        tick()
        if used == full:
            yield tuple(word)
            return
        k = len(word) + 1
        options = full ^ used
        while options:
            bit = options & -options
            options ^= bit
            nxt = used | bit
            if dominated(lower[k], nxt) and dominated(nxt, upper[k]):
                word.append(bit.bit_length() - 1)
                yield from visit(nxt)
                word.pop()
    yield from visit(0)

def coatoms(u):
    for i, high in enumerate(u):
        for j in range(i + 1, len(u)):
            low = u[j]
            if low < high and not any(low < b < high for b in u[i + 1:j]):
                z = list(u)
                z[i], z[j] = z[j], z[i]
                yield tuple(z)

def first_index(mask):
    return (mask & -mask).bit_length() - 1

@lru_cache(50000)
def coeff(x, y, k):
    value, exact = calculate(x, y, k, 0)
    assert exact
    return value

def calculate(x, y, k, threshold):
    tick()
    if k < 0 or not below(x, y):
        return 0, True
    if k == 0:
        return 1, True
    if 2 * k >= length(y) - length(x):
        return 0, True
    # With a descent of y, moving x upward by that reflection preserves P.
    missing = desc(y) & ~desc(x)
    if missing:
        return calculate(swap(x, first_index(missing)), y, k, threshold)
    missing = desc(inv(y)) & ~desc(inv(x))
    if missing:
        return calculate(inv(swap(inv(x), first_index(missing))), y, k, threshold)
    i = first_index(desc(y))
    assert i >= 0
    u = swap(y, i)
    score = coeff(swap(x, i), u, k)
    if not below(x, u):
        return score, True
    score += coeff(x, u, k - 1)
    if score == 0 or score < threshold:
        return score, score == 0
    # Corrections with length(u)-length(z)=1 have mu(z,u)=1.
    for z in coatoms(u):
        if z[i] > z[i + 1] and below(x, z):
            score -= coeff(x, z, k - 1)
            assert score >= 0
            if score == 0 or score < threshold:
                return score, score == 0
    if k >= 2:
        for z in interval(x, u):
            g = length(u) - length(z)
            if g < 3 or g % 2 == 0 or g + 1 > 2 * k or z[i] < z[i + 1]:
                continue
            # At odd gap >=3, a missing descent normalizes z upward and the
            # degree bound then makes the leading coefficient zero.
            if desc(u) & ~desc(z) or desc(inv(u)) & ~desc(inv(z)):
                continue
            lower_term = coeff(x, z, k - (g + 1) // 2)
            if lower_term:
                score -= lower_term * coeff(z, u, (g - 1) // 2)
                assert score >= 0
                if score == 0 or score < threshold:
                    return score, score == 0
    return score, True

def diagram(p):
    return tuple(len(p) - 1 - j for j in reversed(p))

def orbit(a, v):
    for p, q in ((a, v), (inv(a), inv(v))):
        yield p, q
        yield diagram(p), diagram(q)

def unrank(r):
    pool = list(range(N))
    word = []
    for k in reversed(range(N)):
        index, r = divmod(r, F[k])
        word.append(pool.pop(index))
    return tuple(word)

old_pair = tuple(unrank(r) for r in old)
settled_a = (3, 2, 1, 0, 5, 4, 9, 8, 7, 6)
settled_v = (9, 3, 2, 1, 5, 4, 8, 7, 6, 0)
settled_orbit = set(orbit(settled_a, settled_v))

def sanity():
    a = (1, 0, 3, 2)
    v = (3, 1, 2, 0)
    generated = list(uppers(a, 3, 0, F[4]))
    brute = [(r, q) for r, q in enumerate(permutations(range(4)))
             if length(q) == length(a) + 3 and below(a, q)
             and not (desc(q) & ~desc(a) or desc(inv(q)) & ~desc(inv(a)))
             and all(prefixes(a)[i] != prefixes(q)[i] for i in range(1, 4))]
    assert generated == brute and any(q == v for _, q in brute)
    assert coeff(a, v, 1) == 1 and calculate(a, v, 1, 2)[0] < 2
    # Direct product of two copies has polynomial (1+q)^2.
    aa = a + tuple(j + 4 for j in a)
    vv = v + tuple(j + 4 for j in v)
    assert [coeff(aa, vv, k) for k in range(3)] == [1, 2, 1]
    assert chain_graph((0, 1, 2), (2, 1, 0))[0]
    assert not chain_graph(tuple(range(4)), a)[0]
    return {'S4_generator_matches_brute_force': True, 'S4_q1': 1, 'product_coefficients': [1, 2, 1]}

cursor = start
out = {'status': 'partial', 'start': start, 'stop': stop, 'global_end': end,
       'decided_representatives': 0, 'rejections_by_certified_upper_bound': {}, 'first_rejection': None}
try:
    out['sanity'] = sanity()
    rows = islice(permutations(range(N)), start[0], min(F[N], stop[0] + 1))
    for r, a in enumerate(rows, start[0]):
        low = start[1] if r == start[0] else 0
        high = stop[1] if r == stop[0] else F[N]
        cursor = (r, low)
        tick()
        if length(a) > 17 or a[0] == N - 1 or a[-1] == 0:
            continue
        for t, v in uppers(a, 11, low, high):
            cursor = (r, t)
            pair = (a, v)
            cs = cycles(a, v)
            if len(cs) != 3 or pair in settled_orbit:
                continue
            if any(old_pair <= image < pair for image in orbit(a, v)):
                continue
            # Apply the common-entry deletion criterion directly as well.
            if any(a[i] == v[i] and sum(b >= a[i] for b in a[:i]) == sum(b >= a[i] for b in v[:i]) for i in range(N)):
                continue
            connected, edges = chain_graph(a, v)
            if not connected:
                continue
            value, exact = calculate(a, v, 5, 5)
            out['decided_representatives'] += 1
            record = {'cursor': [r, t], 'a': [j + 1 for j in a], 'v': [j + 1 for j in v],
                      'lengths': [length(a), length(v)], 'relative_cycles': cs,
                      'chain_position_swaps': edges, 'q5_upper_bound': value, 'coefficient_exact': exact}
            if value >= 5:
                assert exact
                out.update(status='hit', witness=record, summary='An admissible remaining S10 pair meets the coefficient threshold.')
                break
            hist = out['rejections_by_certified_upper_bound']
            hist[str(value)] = hist.get(str(value), 0) + 1
            if out['first_rejection'] is None:
                out['first_rejection'] = record
            cursor = (r, t + 1) if t + 1 < F[N] else (r + 1, 0)
        if out['status'] == 'hit':
            break
    else:
        cursor = stop
        out.update(status='range_exhausted', summary='Every remaining canonical representative in the requested half-open range has coefficient at most four.')
except TimeoutError:
    out['summary'] = 'Time budget reached. Every remaining canonical representative before next_cursor in this run was excluded. Resume at next_cursor.'
if out['status'] != 'hit':
    out['next_cursor'] = cursor
    out['certified_half_open_range'] = [start, cursor]
    out['remaining_in_requested_range'] = [cursor, stop]
with open('result.json', 'w') as f:
    json.dump(out, f)
