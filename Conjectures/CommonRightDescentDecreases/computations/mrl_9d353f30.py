# MathResearchLab experiment 9d353f30-d9af-4063-bc91-85808b3f2419
# Canonical suffix search by inversion number and descent sets
# sha256(code) = 47fea451f42b59c80713d5477d328908fd84ff8f80ab5b6d7ceb8ba5cf3a6388
# parameters: {"start": [87175, 980034], "end": [3628800, 0], "seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import itertools
import math
import time
from collections import Counter
from functools import lru_cache

started = time.monotonic()
deadline = started + max(1.0, min(100.0, float(params.get('seconds', 95))))
fact = [math.factorial(i) for i in range(11)]
N = fact[10]
frontier = (87175, 980034)
begin = tuple(params.get('start', frontier))
end = tuple(params.get('end', [N, 0]))
assert frontier <= begin <= end <= (N, 0)
assert all(0 <= j < N for i, j in (begin, end))

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
    for m in range(n-1, -1, -1):
        digit, r = divmod(r, fact[m])
        p.append(pool.pop(digit))
    return bytes(p)

def rank(p):
    return sum(fact[len(p)-1-j] * sum(y < x for y in p[j+1:]) for j, x in enumerate(p))

@lru_cache(maxsize=32000)
def length(p):
    return sum(sum(y < x for y in p[j+1:]) for j, x in enumerate(p))

@lru_cache(maxsize=32000)
def inverse(p):
    q = bytearray(len(p))
    for j, x in enumerate(p):
        q[x] = j
    return bytes(q)

@lru_cache(maxsize=32000)
def desc(p):
    return sum(1 << j for j in range(len(p)-1) if p[j] > p[j+1])

def complement(p):
    return bytes(len(p)-1-x for x in p)

def swap(p, i, j):
    q = bytearray(p)
    q[i], q[j] = q[j], q[i]
    return bytes(q)

@lru_cache(maxsize=100000)
def dominated(lower, upper):
    # The masks have equal cardinality. Compare their sorted elements.
    while lower:
        x = lower & -lower
        y = upper & -upper
        if x > y:
            return False
        lower ^= x
        upper ^= y
    return True

@lru_cache(maxsize=60000)
def le(a, v):
    lo = hi = 0
    for x, y in zip(a, v):
        lo |= 1 << x
        hi |= 1 << y
        if not dominated(lo, hi):
            return False
    return True

def choices(mask, last, right, left):
    # Bit 0 of right permits a descent at the boundary before the next value.
    available = mask & (1 | ((~mask | left) << 1))
    if not (right & 1):
        available &= ~((1 << (last+1))-1)
    return available

@lru_cache(maxsize=90000)
def degrees(mask, last, right, left):
    tick()
    if not mask:
        return 1
    bits = choices(mask, last, right, left)
    result = 0
    while bits:
        b = bits & -bits
        bits ^= b
        digit = (mask & (b-1)).bit_count()
        x = b.bit_length()-1
        next_last = -1 if right & 2 else x
        result |= degrees(mask ^ b, next_last, right >> 1, left) << digit
    return result

def uppers(a, total, lo, hi):
    n = len(a)
    full = (1 << n)-1
    left = desc(inverse(a))
    prefixes = [0]
    for x in a:
        prefixes.append(prefixes[-1] | (1 << x))
    word = bytearray(n)
    def visit(mask, last, right, need, base):
        tick()
        m = mask.bit_count()
        if base >= hi or base + fact[m] <= lo or not (0 <= need <= m*(m-1)//2):
            return
        depth = n-m
        if 0 < depth < n:
            used = full ^ mask
            if prefixes[depth] == used or not dominated(prefixes[depth], used):
                return
        if not m:
            yield base, bytes(word)
            return
        if m <= 6 and not ((degrees(mask, last, right, left) >> need) & 1):
            return
        bits = choices(mask, last, right, left)
        while bits:
            b = bits & -bits
            bits ^= b
            x = b.bit_length()-1
            digit = (mask & (b-1)).bit_count()
            word[depth] = x
            yield from visit(mask ^ b, -1 if right & 2 else x, right >> 1, need-digit, base+digit*fact[m-1])
    yield from visit(full, -1, 1 | (desc(a) << 1), total, 0)

def four(p):
    q = complement(p)[::-1]
    return (p, inverse(p), q, inverse(q))

def canonical_images(a, v):
    images = set(zip(four(a), four(v)))
    # The reversed interval has lower length 45-(length(a)+11).
    if 45-length(v) <= 17:
        images.update(zip(four(complement(v)), four(complement(a))))
    return images

def cycles(a, v):
    ai = inverse(a)
    unseen = set(range(len(a)))
    out = []
    while unseen:
        j = min(unseen)
        cycle = []
        while j in unseen:
            unseen.remove(j)
            cycle.append(j+1)
            j = ai[v[j]]
        out.append(cycle)
    return out

@lru_cache(maxsize=9000)
def covers(v):
    out = []
    for i, x in enumerate(v):
        largest = -1
        for j in range(i+1, len(v)):
            y = v[j]
            if largest < y < x:
                out.append((i, j, swap(v, i, j)))
                largest = y
    return tuple(out)

def chain_graph(a, v):
    groups = [{i} for i in range(len(a))]
    steps = []
    while a != v:
        for i, j, z in covers(v):
            if le(a, z):
                steps.append([i+1, j+1])
                p = next(h for h in groups if i in h)
                q = next(h for h in groups if j in h)
                if p is not q:
                    groups.remove(q)
                    p.update(q)
                v = z
                break
        else:
            raise AssertionError('comparable interval has no downward step')
    return len(groups) == 1, steps

@lru_cache(maxsize=110000)
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
    ai, vi = inverse(a), inverse(v)
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
    if not value or not le(a, u):
        return value
    layer = {u}
    for g in range(1, min(2*k-1, gap-1)+1):
        nxt = set()
        for h in layer:
            tick()
            for _, _, z in covers(h):
                if z not in nxt and le(a, z):
                    nxt.add(z)
        layer = nxt
        if g % 2:
            for z in layer:
                tick()
                if z[i] > z[i+1]:
                    mu = coeff(z, u, (g-1)//2, True)
                    if mu:
                        value -= mu*coeff(a, z, k-(g+1)//2, True)
                        assert value >= 0
                        if value == 0:
                            return 0
    return value

def sanity():
    perms = [bytes(p) for p in itertools.permutations(range(4))]
    for ra, a in enumerate(perms):
        assert rank(a) == ra and unrank(4, ra) == a
        expected = [[] for _ in range(7)]
        for rv, v in enumerate(perms):
            slow = all(all(x <= y for x, y in zip(sorted(a[:j]), sorted(v[:j]))) for j in range(1,5))
            assert le(a, v) == slow
            assert (a in {z for _, _, z in covers(v)}) == (slow and length(v)-length(a) == 1)
            if not slow or any(set(a[:j]) == set(v[:j]) for j in range(1,4)):
                continue
            if desc(v) & ~desc(a) or desc(inverse(v)) & ~desc(inverse(a)):
                continue
            expected[length(v)].append((rv, v))
        for ell in range(7):
            assert list(uppers(a, ell, 0, 24)) == expected[ell]
            assert list(uppers(a, ell, 5, 19)) == [e for e in expected[ell] if 5 <= e[0] < 19]
    e = perms[0]
    v = bytes([2,3,0,1])
    assert coeff(e, v, 1, True) == coeff(bytes([0,2,1,3]), v, 1, True) == 1
    assert coeff(e, e[::-1], 1, True) == 0
    for a in perms:
        for v in perms:
            for k in (1,2):
                assert min(5, coeff(a,v,k,True)) <= coeff(a,v,k,False)
    assert chain_graph(e, e[::-1])[0]
    assert not chain_graph(e, bytes([1,0,3,2]))[0]
    assert all(rank(unrank(10,r)) == r for r in frontier)

def one_based(p):
    return [x+1 for x in p]

def descent_list(p):
    return [i+1 for i in range(len(p)-1) if p[i] > p[i+1]]

cursor = begin
counts = Counter()
witness = None
checked = False
status = 'partial'
try:
    sanity()
    checked = True
    for i in range(begin[0], min(N, end[0]+1)):
        if cursor >= end:
            break
        check_time()
        a = unrank(10, i)
        if length(a) <= 17 and min(four(a)) == a:
            lo = cursor[1]
            hi = end[1] if i == end[0] else N
            for j, v in uppers(a, length(a)+11, lo, hi):
                cursor = (i,j)
                check_time()
                images = canonical_images(a,v)
                if min(images) != (a,v):
                    counts['noncanonical'] += 1
                else:
                    relative = cycles(a,v)
                    if len(relative) != 3:
                        counts['wrong_cycle_count'] += 1
                    elif coeff(a,v,5,False) < 5:
                        counts['rejected_by_capped_bound'] += 1
                    else:
                        connected, steps = chain_graph(a,v)
                        if not connected:
                            counts['disconnected_after_bound'] += 1
                        else:
                            mu = coeff(a,v,5,True)
                            if mu < 5:
                                counts['rejected_by_exact_coefficient'] += 1
                            else:
                                fixed = [[h+1, sum(t >= x for t in v[:h])-sum(t >= x for t in a[:h])] for h,x in enumerate(a) if v[h] == x]
                                assert all(delta != 0 for _,delta in fixed)
                                assert rank(v) == j and le(a,v) and len(steps) == 11
                                witness = dict(ranks=[i,j], a=one_based(a), v=one_based(v), lengths=[length(a),length(v)], bruhat_comparable=True, right_descents=[descent_list(a),descent_list(v)], left_descents=[descent_list(inverse(a)),descent_list(inverse(v))], relative_cycles=relative, fixed_positions_and_count_differences=fixed, downward_chain_position_swaps=steps, connected=True, orbit_ranks_with_length_cap=sorted([rank(b),rank(c)] for b,c in images), exact_q5=mu)
                cursor = (i,j+1) if j+1 < N else (i+1,0)
                if witness:
                    break
        if witness:
            break
        cursor = min((i+1,0),end)
    status = 'witness' if witness else 'range_exhausted'
except Budget:
    pass
if witness:
    summary = 'A canonical admissible pair reaches the threshold.'
elif status == 'range_exhausted':
    summary = 'Every canonical admissible pair in the requested range has coefficient at most four.'
else:
    summary = 'Only the processed half-open prefix is settled. Resume at next_start, inclusively.'
result = dict(summary=summary, status=status, sanity_passed=checked, requested_half_open=[begin,end], processed_half_open=[begin,cursor], unscanned_half_open=[cursor,end], next_start=cursor, counts=dict(counts), witness=witness, elapsed_seconds=round(time.monotonic()-started,3))
with open('result.json','w') as f:
    json.dump(result,f)
