# MathResearchLab experiment 970c1202-2460-4454-ac37-e7e23a6f1b5c
# Exact suffix scan with 720 upper-endpoint ranks per block
# sha256(code) = 7f97a1c223e8644f5d846e7f3d69474f8531f1b0a73a46979f037419e211c443
# parameters: {"start": [109574, 1365498], "end": [3628800, 0], "seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))
import itertools
import math
import time
from collections import Counter
from functools import lru_cache

started = time.monotonic()
deadline = started + min(100.0, max(1.0, float(params.get('seconds', 95))))
fact = [math.factorial(i) for i in range(11)]
N = fact[10]
frontier = (109574, 1365498)
begin = tuple(params.get('start', frontier))
end = tuple(params.get('end', (N, 0)))
assert frontier <= begin <= end <= (N, 0)
assert all(0 <= j < N for _, j in (begin, end))

class Budget(Exception):
    pass

def check_time():
    if time.monotonic() >= deadline:
        raise Budget

ticks = 0
def tick():
    global ticks
    ticks += 1
    if ticks % 256 == 0:
        check_time()

def unrank(n, r):
    pool = list(range(n))
    p = bytearray()
    for m in reversed(range(n)):
        d, r = divmod(r, fact[m])
        p.append(pool.pop(d))
    return bytes(p)

def rank(p):
    return sum(fact[len(p)-i-1] * sum(y < x for y in p[i+1:]) for i, x in enumerate(p))

@lru_cache(32000)
def length(p):
    return sum(sum(y < x for y in p[i+1:]) for i, x in enumerate(p))

@lru_cache(32000)
def inv(p):
    q = bytearray(len(p))
    for i, x in enumerate(p):
        q[x] = i
    return bytes(q)

@lru_cache(32000)
def desc(p):
    return sum(1 << i for i in range(len(p)-1) if p[i] > p[i+1])

def swap(p, i, j):
    q = bytearray(p)
    q[i], q[j] = q[j], q[i]
    return bytes(q)

def comp(p):
    return bytes(len(p)-1-x for x in p)

def four(p):
    h = comp(p)[::-1]
    return (p, inv(p), h, inv(h))

def prefixes(p):
    cuts = [0]
    for x in p:
        cuts.append(cuts[-1] | (1 << x))
    return cuts

# Each five-bit field stores a count of values at or above one threshold.
# Adding a guard bit before subtraction tests all ten inequalities at once.
guard = sum(16 << (5*j) for j in range(10))
unit = [sum(1 << (5*j) for j in range(x+1)) for x in range(10)]
profiles = [0]*1024
for mask in range(1, 1024):
    b = mask & -mask
    profiles[mask] = profiles[mask ^ b] + unit[b.bit_length()-1]
dom = [bytes(((guard + upper - lower) & guard) == guard for upper in profiles) for lower in profiles]

@lru_cache(50000)
def le(a, v):
    low = high = 0
    for x, y in zip(a, v):
        low |= 1 << x
        high |= 1 << y
        if not dom[low][high]:
            return False
    return True

@lru_cache(None)
def suffix_shape(m):
    size = 1 << (m-1)
    right = [0]*size
    left = [0]*size
    by_length = [0]*(m*(m-1)//2+1)
    by_first = [0]*(m+1)
    by_subset = [0]*(1 << m)
    for r, word in enumerate(itertools.permutations(range(m))):
        p = bytes(word)
        bit = 1 << r
        right[desc(p)] |= bit
        left[desc(inv(p))] |= bit
        by_length[length(p)] |= bit
        by_first[p[0]] |= bit
        for subset in prefixes(p)[1:-1]:
            by_subset[subset] |= bit
    # Subset unions turn exact descent masks into permitted descent masks.
    for i in range(m-1):
        for mask in range(size):
            if mask & (1 << i):
                right[mask] |= right[mask ^ (1 << i)]
                left[mask] |= left[mask ^ (1 << i)]
    for j in reversed(range(m)):
        by_first[j] |= by_first[j+1]
    return right, left, by_length, by_first, by_subset

@lru_cache(None)
def tail_data(n, mask):
    alphabet = tuple(x for x in range(n) if mask & (1 << x))
    m = len(alphabet)
    used = ((1 << n)-1) ^ mask
    classes = [[] for _ in range(m)]
    by_subset = suffix_shape(m)[4]
    for subset in range(1, (1 << m)-1):
        actual = used | sum(1 << x for j, x in enumerate(alphabet) if subset & (1 << j))
        classes[subset.bit_count()].append((actual, by_subset[subset]))
    words = tuple(bytes(p) for p in itertools.permutations(alphabet))
    return alphabet, classes, words

@lru_cache(60000)
def legal_cut(n, mask, lower):
    m = mask.bit_count()
    j = lower.bit_count() - (n-m)
    bits = 0
    for upper, group in tail_data(n, mask)[1][j]:
        if lower != upper and dom[lower][upper]:
            bits |= group
    return bits

@lru_cache(20000)
def local_left(n, mask, allowed):
    vals = tail_data(n, mask)[0]
    return sum(1 << i for i, (x, y) in enumerate(zip(vals, vals[1:])) if y != x+1 or allowed & (1 << x))

def uppers(a, total, lo, hi):
    n = len(a)
    full = (1 << n)-1
    cuts = prefixes(a)
    rd, ld = desc(a), desc(inv(a))
    width = min(6, n)
    right, left, by_length, by_first, _ = suffix_shape(width)
    prefix = bytearray(n-width)
    def visit(mask, last, need, base):
        tick()
        m = mask.bit_count()
        d = n-m
        if need < 0 or need > m*(m-1)//2 or base >= hi or base+fact[m] <= lo:
            return
        if d and (cuts[d] == (full ^ mask) or not dom[cuts[d]][full ^ mask]):
            return
        ascent = d > 0 and not (rd & (1 << (d-1)))
        if m == width:
            bits = by_length[need] & right[(rd >> d) & ((1 << (m-1))-1)]
            if not bits:
                return
            bits &= left[local_left(n, mask, ld)]
            if ascent:
                bits &= by_first[(mask & ((1 << (last+1))-1)).bit_count()]
            if base < lo:
                bits &= ~((1 << (lo-base))-1)
            if base+fact[m] > hi:
                bits &= (1 << (hi-base))-1
            for h in range(d+1, n):
                if not bits:
                    return
                bits &= legal_cut(n, mask, cuts[h])
            if bits:
                head = bytes(prefix)
                words = tail_data(n, mask)[2]
                while bits:
                    b = bits & -bits
                    bits ^= b
                    r = b.bit_length()-1
                    yield base+r, head+words[r]
            return
        choices = mask & (1 | ((~mask | ld) << 1))
        if ascent:
            choices &= ~((1 << (last+1))-1)
        while choices:
            b = choices & -choices
            choices ^= b
            digit = (mask & (b-1)).bit_count()
            x = b.bit_length()-1
            prefix[d] = x
            yield from visit(mask ^ b, x, need-digit, base+digit*fact[m-1])
    yield from visit(full, -1, total, 0)

def cycles(a, v):
    ai = inv(a)
    unseen = (1 << len(a))-1
    result = []
    while unseen:
        j = (unseen & -unseen).bit_length()-1
        cycle = []
        while unseen & (1 << j):
            unseen ^= 1 << j
            cycle.append(j+1)
            j = ai[v[j]]
        result.append(cycle)
    return result

@lru_cache(7000)
def covers(v):
    result = []
    for i, x in enumerate(v):
        largest = -1
        for j in range(i+1, len(v)):
            y = v[j]
            if largest < y < x:
                result.append((i, j, swap(v, i, j)))
                largest = y
    return tuple(result)

def chain(a, v):
    # Descend by covers that stay above a. Labels below are one-based.
    groups = list(range(len(v)))
    steps = []
    while a != v:
        for i, j, z in covers(v):
            if le(a, z):
                steps.append([i+1, j+1])
                old, new = groups[j], groups[i]
                if old != new:
                    groups = [new if g == old else g for g in groups]
                v = z
                break
        else:
            raise AssertionError('No saturated step')
    return len(set(groups)) == 1, steps

@lru_cache(100000)
def coeff(a, v, k, exact):
    tick()
    if k < 0:
        return 0
    if k == 0:
        return int(le(a, v))
    gap = length(v)-length(a)
    if gap <= 2*k or not le(a, v):
        return 0
    dv = desc(v)
    missing = dv & ~desc(a)
    if missing:
        if gap == 2*k+1:
            return 0
        i = (missing & -missing).bit_length()-1
        return coeff(swap(a, i, i+1), v, k, exact)
    ai, vi = inv(a), inv(v)
    missing = desc(vi) & ~desc(ai)
    if missing:
        if gap == 2*k+1:
            return 0
        i = (missing & -missing).bit_length()-1
        return coeff(swap(ai, i, i+1), vi, k, exact)
    i = (dv & -dv).bit_length()-1
    assert i >= 0
    u = swap(v, i, i+1)
    value = coeff(swap(a, i, i+1), u, k, exact)
    if not exact and value == 5:
        return 5
    value += coeff(a, u, k-1, exact)
    if not exact:
        return min(5, value)
    if value and le(a, u):
        for z, g in correction_indices(a, u, i, k):
            mu = coeff(z, u, (g-1)//2, True)
            if mu:
                value -= mu * coeff(a, z, k-(g+1)//2, True)
                assert value >= 0
                if value == 0:
                    break
    return value

def correction_indices(a, u, i, k):
    layer = {u}
    for g in range(1, min(2*k-1, length(u)-length(a))+1):
        nxt = set()
        for h in layer:
            tick()
            for _, _, z in covers(h):
                if z not in nxt and le(a, z):
                    nxt.add(z)
        layer = nxt
        if g % 2:
            for z in layer:
                if z[i] > z[i+1]:
                    yield z, g

def one(p):
    return [x+1 for x in p]

def desc_list(p):
    return [i+1 for i in range(len(p)-1) if p[i] > p[i+1]]

def recurrence_record(a, v):
    i = (desc(v) & -desc(v)).bit_length()-1
    u = swap(v, i, i+1)
    initial = [coeff(swap(a, i, i+1), u, 5, True), coeff(a, u, 4, True)]
    corrections = []
    for z, g in correction_indices(a, u, i, 5):
        mu = coeff(z, u, (g-1)//2, True)
        c = coeff(a, z, 5-(g+1)//2, True) if mu else 0
        if mu and c:
            corrections.append(dict(z=one(z), gap_to_u=g, mu_z_u=mu, lower_coefficient=c))
    corrections.sort(key=lambda t: (t['gap_to_u'], t['z']))
    value = sum(initial)-sum(t['mu_z_u']*t['lower_coefficient'] for t in corrections)
    return dict(right_descent=i+1, initial_terms=initial, nonzero_corrections=corrections, value=value)

def sanity():
    perms = [bytes(p) for p in itertools.permutations(range(4))]
    for i, a in enumerate(perms):
        assert rank(a) == i and unrank(4, i) == a
        expected = [[] for _ in range(7)]
        for j, v in enumerate(perms):
            slow = all(all(x <= y for x, y in zip(sorted(a[:h]), sorted(v[:h]))) for h in range(1, 5))
            assert le(a, v) == slow
            assert (a in {z for _, _, z in covers(v)}) == (slow and length(v)-length(a) == 1)
            if not slow or any(set(a[:h]) == set(v[:h]) for h in range(1, 4)):
                continue
            if not (desc(v) & ~desc(a) or desc(inv(v)) & ~desc(inv(a))):
                expected[length(v)].append((j, v))
        for ell in range(7):
            assert list(uppers(a, ell, 0, 24)) == expected[ell]
            assert list(uppers(a, ell, 5, 19)) == [p for p in expected[ell] if 5 <= p[0] < 19]
    # Exercise a nonempty prefix before the six-value bitset, including a cut inside a block.
    a = bytes([1, 0, 3, 2, 5, 4, 6])
    expected = [[] for _ in range(22)]
    for j in range(613, 2451):
        v = unrank(7, j)
        if not le(a, v) or desc(v) & ~desc(a) or desc(inv(v)) & ~desc(inv(a)):
            continue
        if all(x != y for x, y in zip(prefixes(a)[1:-1], prefixes(v)[1:-1])):
            expected[length(v)].append((j, v))
    for ell in range(22):
        assert list(uppers(a, ell, 613, 2451)) == expected[ell]
    e = perms[0]
    assert coeff(e, bytes([2, 3, 0, 1]), 1, True) == 1
    assert coeff(e, e[::-1], 1, True) == 0
    for a in perms:
        for v in perms:
            for k in (1, 2):
                assert min(5, coeff(a, v, k, True)) <= coeff(a, v, k, False)
    assert chain(e, e[::-1])[0] and not chain(e, bytes([1, 0, 3, 2]))[0]
    assert all(rank(unrank(10, j)) == j for j in frontier)

cursor = begin
counts = Counter()
witness = None
sanity_passed = False
status = 'partial'
try:
    sanity()
    sanity_passed = True
    for i in range(begin[0], min(N, end[0]+1)):
        if cursor >= end:
            break
        check_time()
        a = unrank(10, i)
        ell = length(a)
        if ell <= 17:
            orbit_a = four(a)
            if a == min(orbit_a):
                stabilizer = [h for h in range(1, 4) if orbit_a[h] == a]
                reverse_uppers = four(comp(a)) if ell == 17 else ()
                hi = end[1] if i == end[0] else N
                for j, v in uppers(a, ell+11, cursor[1], hi):
                    cursor = (i, j)
                    check_time()
                    noncanonical = False
                    if stabilizer:
                        orbit_v = four(v)
                        noncanonical = any(orbit_v[h] < v for h in stabilizer)
                    # A reversed image has lower length 34-ell. It meets the cap only at ell=17.
                    if not noncanonical and reverse_uppers:
                        noncanonical = any(pair < (a, v) for pair in zip(four(comp(v)), reverse_uppers))
                    if noncanonical:
                        counts['noncanonical'] += 1
                    else:
                        relative = cycles(a, v)
                        if len(relative) != 3:
                            counts['wrong_cycle_count'] += 1
                        elif coeff(a, v, 5, False) < 5:
                            counts['capped_bound_below_five'] += 1
                        else:
                            connected, steps = chain(a, v)
                            if not connected:
                                counts['disconnected'] += 1
                            else:
                                fixed = [[h+1, sum(t >= x for t in v[:h])-sum(t >= x for t in a[:h])] for h, x in enumerate(a) if v[h] == x]
                                if any(delta == 0 for _, delta in fixed):
                                    counts['compressible'] += 1
                                else:
                                    value = coeff(a, v, 5, True)
                                    if value < 5:
                                        counts['exact_below_five'] += 1
                                    else:
                                        assert rank(a) == i and rank(v) == j and le(a, v)
                                        assert length(v)-ell == len(steps) == 11
                                        assert not (desc(v) & ~desc(a) or desc(inv(v)) & ~desc(inv(a)))
                                        images = list(zip(four(a), four(v)))
                                        if 45-length(v) <= 17:
                                            images += list(zip(four(comp(v)), four(comp(a))))
                                        assert min(images) == (a, v)
                                        record = recurrence_record(a, v)
                                        assert record['value'] == value
                                        witness = dict(ranks=[i, j], a=one(a), v=one(v), lengths=[ell, length(v)], right_descents=[desc_list(a), desc_list(v)], left_descents=[desc_list(inv(a)), desc_list(inv(v))], relative_cycles=relative, fixed_positions_and_count_differences=fixed, downward_chain_position_swaps=steps, canonical_orbit_ranks=sorted({(rank(b), rank(c)) for b, c in images}), exact_q5=value, recurrence=record)
                    cursor = (i, j+1) if j+1 < N else (i+1, 0)
                    if witness:
                        break
        if witness:
            break
        cursor = min((i+1, 0), end)
    status = 'witness' if witness else 'range_exhausted'
except Budget:
    pass

if witness:
    summary = 'An admissible canonical S10 pair reaches five. The recurrence record gives its exact coefficient.'
elif status == 'range_exhausted':
    summary = 'Every admissible canonical pair in the requested half-open range has coefficient at most four.'
else:
    summary = 'The processed half-open prefix contains no witness. Resume inclusively at next_start.'
result = dict(summary=summary, status=status, sanity_passed=sanity_passed, requested_half_open=[begin, end], processed_half_open=[begin, cursor], unscanned_half_open=[cursor, end], next_start=cursor, counts=dict(counts), witness=witness, elapsed_seconds=round(time.monotonic()-started, 3))
with open('result.json', 'w') as f:
    json.dump(result, f)
