# MathResearchLab experiment 5932ea7c-c43f-4df9-b063-a3c9233b1397
# Threshold scan from the first unsettled cursor
# sha256(code) = d40c655e3c67ae7a4152d8f70d7edadb143c9020fb367c1c10bd4d19179310c6
# parameters: {"start": [68089, 926592], "end": [3628800, 0], "seconds": 96}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import itertools
import math
import time
from functools import lru_cache
from collections import Counter

started = time.monotonic()
import numpy as np

N = math.factorial(10)
frontier = (68089, 926592)
begin = tuple(params.get('start', frontier))
end = tuple(params.get('end', [N, 0]))
assert frontier <= begin <= end <= (N, 0)
assert all(0 <= j < N for i, j in (begin, end))
deadline = started + min(105.0, float(params.get('seconds', 96)))
FACT = [math.factorial(i) for i in range(11)]

class Budget(Exception):
    pass

def clock_check():
    if time.monotonic() >= deadline:
        raise Budget

@lru_cache(maxsize=20000)
def word(r):
    unused = list(range(10))
    p = []
    for m in range(9, -1, -1):
        digit, r = divmod(r, FACT[m])
        p.append(unused.pop(digit))
    return bytes(p)

def rank(p):
    return sum(sum(y < x for y in p[i+1:]) * FACT[len(p)-1-i] for i, x in enumerate(p))

@lru_cache(maxsize=30000)
def inv(p):
    z = bytearray(len(p))
    for i, x in enumerate(p):
        z[x] = i
    return bytes(z)

@lru_cache(maxsize=50000)
def length(p):
    return sum(sum(y < x for y in p[i+1:]) for i, x in enumerate(p))

@lru_cache(maxsize=50000)
def desc(p):
    return sum(1 << i for i in range(len(p)-1) if p[i] > p[i+1])

def swap(p, i, j):
    b = bytearray(p)
    b[i], b[j] = b[j], b[i]
    return bytes(b)

# One base-32 digit per value threshold. Each prefix-count difference is
# between -10 and 10, so a bias of 16 keeps digits independent.
weight = [sum(1 << (5*t) for t in range(x)) for x in range(10)]
bias = sum(16 << (5*t) for t in range(10))

@lru_cache(maxsize=90000)
def le(a, v):
    b = bias
    for x, y in zip(a, v):
        b += weight[y] - weight[x]
        if (b & bias) != bias:
            return False
    return True

def possible_connected(a, v):
    # Equal proper prefix sets are fixed throughout the interval by the
    # rank inequalities. No chain transposition can cross that cut.
    b = bias
    for i in range(len(a)-1):
        b += weight[v[i]] - weight[a[i]]
        if b == bias or (b & bias) != bias:
            return False
    return True

def three_cycles(a, v):
    ai = inv(a)
    seen = 0
    count = 0
    for i in range(len(a)):
        if seen & (1 << i):
            continue
        count += 1
        if count > 3:
            return False
        j = i
        while not (seen & (1 << j)):
            seen |= 1 << j
            j = ai[v[j]]
    return count == 3

@lru_cache(maxsize=14000)
def down(v):
    out = []
    for i, top in enumerate(v):
        largest = -1
        for j in range(i+1, len(v)):
            y = v[j]
            if largest < y < top:
                out.append((i, j, swap(v, i, j)))
                largest = y
    return tuple(out)

def graph_certificate(a, v):
    components = [{i} for i in range(len(a))]
    chain = []
    while v != a:
        for i, j, z in down(v):
            if le(a, z):
                chain.append([i+1, j+1])
                left = next(c for c in components if i in c)
                right = next(c for c in components if j in c)
                if left is not right:
                    components.remove(right)
                    left.update(right)
                v = z
                break
        else:
            raise AssertionError('no downward cover in a comparable interval')
    return len(components) == 1, chain

calls = 0
BOUND, EXACT, SCREEN = range(3)

@lru_cache(maxsize=120000)
def coefficient(a, v, k, mode):
    global calls
    calls += 1
    if calls % 256 == 0:
        clock_check()
    if k < 0:
        return 0
    gap = length(v) - length(a)
    if k == 0:
        return int(le(a, v))
    if gap <= 2*k or not le(a, v):
        return 0
    dv = desc(v)
    missing = dv & ~desc(a)
    if missing:
        i = (missing & -missing).bit_length()-1
        return coefficient(swap(a, i, i+1), v, k, mode)
    ai, vi = inv(a), inv(v)
    missing = desc(vi) & ~desc(ai)
    if missing:
        i = (missing & -missing).bit_length()-1
        return coefficient(swap(ai, i, i+1), vi, k, mode)
    # Every remaining right descent of v is common, hence c=1.
    i = (dv & -dv).bit_length()-1
    assert i >= 0
    u = swap(v, i, i+1)
    child = BOUND if mode == BOUND else EXACT
    value = coefficient(swap(a, i, i+1), u, k, child)
    if mode == BOUND and value >= 5:
        return 5
    value += coefficient(a, u, k-1, child)
    if mode == BOUND:
        return min(5, value)
    if value == 0 or (mode == SCREEN and value < 5) or not le(a, u):
        return value
    layer = {u}
    for g in range(1, min(2*k-1, length(u)-length(a))+1):
        clock_check()
        nxt = set()
        for h, p in enumerate(layer):
            if h % 128 == 0:
                clock_check()
            for _, _, z in down(p):
                if z not in nxt and le(a, z):
                    nxt.add(z)
        layer = nxt
        if not layer:
            break
        if g % 2 == 0:
            continue
        for h, z in enumerate(layer):
            if h % 128 == 0:
                clock_check()
            if z[i] < z[i+1]:
                continue
            mu = coefficient(z, u, (g-1)//2, EXACT)
            if mu:
                value -= mu * coefficient(a, z, k-(g+1)//2, EXACT)
                assert value >= 0
                if value == 0 or (mode == SCREEN and value < 5):
                    return value
    return value

def sanity():
    perms = [bytes(p) for p in itertools.permutations(range(4))]
    for v in perms:
        covers = {z for _, _, z in down(v)}
        for a in perms:
            slow = all(all(x <= y for x, y in zip(sorted(a[:j]), sorted(v[:j]))) for j in range(1, 5))
            assert le(a, v) == slow
            assert (a in covers) == (slow and length(v)-length(a) == 1)
            if slow:
                for k in range(1, 3):
                    exact = coefficient(a, v, k, EXACT)
                    assert min(5, exact) <= coefficient(a, v, k, BOUND)
                    screen = coefficient(a, v, k, SCREEN)
                    assert (screen == exact) if screen >= 5 else (exact <= screen < 5)
    e = bytes(range(4))
    singular = bytes([2, 3, 0, 1])
    assert coefficient(bytes([0, 2, 1, 3]), singular, 1, EXACT) == 1
    assert coefficient(e, singular, 1, EXACT) == 1
    assert coefficient(e, e[::-1], 1, EXACT) == 0
    assert graph_certificate(e, e[::-1])[0]
    assert not graph_certificate(e, bytes([1, 0, 3, 2]))[0]
    for r in (0, frontier[0], frontier[1], N-1):
        assert rank(word(r)) == r
    return 'S4 Bruhat comparisons and covers checked exhaustively, coefficient modes cross-checked, singular and smooth coefficients and graph controls passed'

# Stable buckets let the scan jump straight to the required length and
# right descents. A vectorized mask then enforces the left descents.
def upper_index():
    keys = np.empty(N, dtype=np.uint16)
    left = np.empty(N, dtype=np.uint16)
    bits = np.array([1 << i for i in range(9)], dtype=np.uint16)
    it = itertools.permutations(range(10))
    for lo in range(0, N, 16384):
        clock_check()
        size = min(16384, N-lo)
        p = np.fromiter(it, dtype=np.dtype((np.uint8, (10,))), count=size)
        q = np.argsort(p, axis=1)
        dr = ((p[:, :-1] > p[:, 1:]) * bits).sum(axis=1, dtype=np.uint16)
        dl = ((q[:, :-1] > q[:, 1:]) * bits).sum(axis=1, dtype=np.uint16)
        ell = np.zeros(size, dtype=np.uint16)
        for j in range(9):
            ell += (p[:, j, None] > p[:, j+1:]).sum(axis=1, dtype=np.uint16)
        keys[lo:lo+size] = ell*512 + dr
        left[lo:lo+size] = dl
    for r in (0, frontier[0], frontier[1], N-1):
        p = word(r)
        assert int(keys[r]) == 512*length(p) + desc(p) and int(left[r]) == desc(inv(p))
    order = np.argsort(keys, kind='stable').astype(np.int32)
    offsets = np.r_[0, np.cumsum(np.bincount(keys, minlength=46*512))]
    @lru_cache(maxsize=128)
    def pool(ell, dr, dl):
        chunks = []
        mask = dr
        while True:
            key = 512*ell + mask
            rows = order[offsets[key]:offsets[key+1]]
            if len(rows):
                chunks.append(rows[(left[rows] & (511 ^ dl)) == 0])
            if mask == 0:
                break
            mask = (mask-1) & dr
        return np.sort(np.concatenate(chunks)) if chunks else np.empty(0, dtype=np.int32)
    return pool

def orbit_cursors(a, v):
    def comp(p):
        return bytes(9-x for x in p)
    out = set()
    for x, y in ((a, v), (comp(v), comp(a))):
        if length(x) > 17:
            continue
        for b, c in ((x, y), (comp(x)[::-1], comp(y)[::-1])):
            out.add((rank(b), rank(c)))
            out.add((rank(inv(b)), rank(inv(c))))
    return sorted(out)

cursor = begin
counts = Counter()
other_hits = []
witness = None
check = 'pending'
status = 'partial'
try:
    check = sanity()
    if begin < end:
        pool = upper_index()
    for i in range(begin[0], min(N, end[0]+1)):
        if cursor >= end:
            break
        clock_check()
        a = word(i)
        if length(a) <= 17:
            rows = pool(length(a)+11, desc(a), desc(inv(a)))
            stop_j = end[1] if i == end[0] else N
            low, high = rows.searchsorted([cursor[1], stop_j])
            for index in range(int(low), int(high)):
                j = int(rows[index])
                cursor = (i, j)
                clock_check()
                v = word(j)
                if possible_connected(a, v) and three_cycles(a, v):
                    if coefficient(a, v, 5, BOUND) < 5:
                        counts['discarded_by_saturated_bound'] += 1
                    else:
                        t = coefficient(a, v, 5, SCREEN)
                        if t < 5:
                            counts['discarded_by_exact_initial_terms_or_subtractions'] += 1
                        else:
                            connected, chain = graph_certificate(a, v)
                            if connected:
                                orbit = orbit_cursors(a, v)
                                hit = dict(cursor=cursor, a=[x+1 for x in a], v=[x+1 for x in v], mu=t, downward_chain_position_swaps=chain, orbit_with_length_cap=orbit)
                                if cursor == orbit[0]:
                                    witness = hit
                                else:
                                    other_hits.append(hit)
                            else:
                                counts['disconnected_exact_threshold_hits'] += 1
                cursor = (i, j+1) if j+1 < N else (i+1, 0)
                if witness:
                    break
        if witness:
            break
        cursor = min((i+1, 0), end)
    status = 'witness' if witness else 'range_exhausted'
except Budget:
    status = 'partial'

if witness:
    summary = 'Exact canonical threshold witness with a saturated chain certificate.'
elif status == 'range_exhausted' and not other_hits:
    summary = 'No admissible threshold hit in the requested range, before any canonical tie-break.'
elif status == 'range_exhausted':
    summary = 'No canonical threshold hit in the requested range under the stated tie-break. Other admissible hits are listed.'
else:
    summary = 'Partial scan. The first unsettled cursor is included in the remaining range.'
result = dict(summary=summary, status=status, sanity=check, requested=[begin, end], processed_half_open=[begin, cursor], unscanned_half_open=[cursor, end], next_start=cursor, counts=dict(counts), witness=witness, other_admissible_threshold_hits=other_hits, coefficient_cache_misses=calls, elapsed_seconds=round(time.monotonic()-started, 3))
with open('result.json', 'w') as f:
    json.dump(result, f)
