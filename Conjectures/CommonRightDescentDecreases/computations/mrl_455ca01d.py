# MathResearchLab experiment 455ca01d-dcda-408e-991e-d0c4a9bc907e
# Exact threshold search with resumable endpoint ranges
# sha256(code) = 1733f7333fdb624c58f82845830ad3f704a0792819897ff7050c8932b7466aed
# parameters: {"cursor": [0, 0], "outer_end": 3628800, "seconds": 85, "interval_cap": 20000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from itertools import permutations
from math import factorial

params = json.load(open(os.environ['MRL_PARAMS']))
started = time.monotonic()
deadline = started + min(100.0, float(params.get('seconds', 85)))
cap = int(params.get('interval_cap', 20000))

class Budget(Exception):
    pass

class IntervalCap(Exception):
    pass

def tick():
    if time.monotonic() >= deadline:
        raise Budget

def length(p):
    return sum(x > y for i, x in enumerate(p) for y in p[i + 1:])

def inverse(p):
    ans = [0] * len(p)
    for i, x in enumerate(p):
        ans[x] = i
    return tuple(ans)

def mirror(p):
    return tuple(len(p) - 1 - x for x in reversed(p))

def images(p):
    ip = inverse(p)
    return (p, ip, mirror(p), mirror(ip))

def rank_perm(p):
    return sum(factorial(len(p) - 1 - i) * sum(y < x for y in p[i + 1:]) for i, x in enumerate(p))

def unrank(n, rank):
    rest = list(range(n))
    out = []
    for k in range(n - 1, -1, -1):
        j, rank = divmod(rank, factorial(k))
        out.append(rest.pop(j))
    return tuple(out)

def prefixes(p):
    seq = [0]
    for x in p:
        seq.append(seq[-1] | (1 << x))
    return seq

def signatures(n):
    # Unary counts at every value threshold. Containment of signatures
    # tests componentwise order of sorted prefixes of equal cardinality.
    return [sum(((1 << (mask >> t).bit_count()) - 1) << (n * t) for t in range(n)) for mask in range(1 << n)]

def cycles(a, v):
    ia = inverse(a)
    rel = [ia[y] for y in v]
    used = set()
    parts = []
    for i in range(len(a)):
        if i not in used:
            part = []
            while i not in used:
                used.add(i)
                part.append(i + 1)
                i = rel[i]
            parts.append(part)
    return parts

def swap(p, i, j):
    q = list(p)
    q[i], q[j] = q[j], q[i]
    return tuple(q)

def upper_candidates(a, gap, sig, first, progress):
    # Enumerate precisely the comparable uppers of the requested length
    # whose right and left descents are contained in those of a.
    n = len(a)
    need = [sig[m] for m in prefixes(a)]
    ia = inverse(a)
    target = length(a) + gap
    stack = []
    calls = 0
    def visit(mask, invs, base):
        nonlocal calls
        k = len(stack)
        remaining = n - k
        if base + factorial(remaining) <= first:
            return
        progress[1] = max(base, first)
        calls += 1
        if calls % 256 == 0:
            tick()
        if invs > target or invs + remaining * (remaining - 1) // 2 < target:
            return
        if k == n:
            yield base, tuple(stack)
            return
        block = factorial(remaining - 1)
        digit = 0
        for y in range(n):
            bit = 1 << y
            if mask & bit:
                continue
            child = base + digit * block
            extra = digit
            digit += 1
            if child + block <= first:
                continue
            if k and a[k - 1] < a[k] and stack[-1] > y:
                continue
            if y and ia[y - 1] < ia[y] and not (mask & (bit >> 1)):
                continue
            new_mask = mask | bit
            if need[k + 1] & ~sig[new_mask]:
                continue
            stack.append(y)
            yield from visit(new_mask, invs + extra, child)
            stack.pop()
    yield from visit(0, 0, 0)

def chain_test(a, v, sig):
    n = len(a)
    need = [sig[m] for m in prefixes(a)]
    parent = list(range(n))
    def root(i):
        while i != parent[i]:
            i = parent[i]
        return i
    current = v
    edges = []
    while current != a:
        pre = prefixes(current)
        chosen = None
        for i, high in enumerate(current):
            record = -1
            for j in range(i + 1, n):
                low = current[j]
                if not record < low < high:
                    continue
                record = low
                flip = (1 << low) | (1 << high)
                if all(not (need[k] & ~sig[pre[k] ^ flip]) for k in range(i + 1, j + 1)):
                    chosen = (i, j)
                    break
            if chosen is not None:
                break
        assert chosen is not None, 'comparable unequal endpoints must admit a downward cover'
        i, j = chosen
        parent[root(i)] = root(j)
        edges.append([i + 1, j + 1])
        current = swap(current, i, j)
    assert len(edges) == length(v) - length(a)
    return len({root(i) for i in range(n)}) == 1, list(reversed(edges))

def kl(a, v, sig):
    # Dyer's reflection-order formula (recalled_literature): an increasing
    # Bruhat path contributes a factor (q-1) q^((h-1)/2) per edge of gap h.
    # The lexicographic order on position transpositions is a reflection order.
    # Reversing it propagates from upper to lower endpoints. All directed
    # reflection edges are needed here, including noncovers.
    n = len(a)
    d = length(v) - length(a)
    if d == 0:
        return [1], 1
    ap, vp = prefixes(a), prefixes(v)
    allowed = []
    for mask, value in enumerate(sig):
        k = mask.bit_count()
        allowed.append(not (sig[ap[k]] & ~value or value & ~sig[vp[k]]))
    verts = []
    depth = []
    layers = [[] for _ in range(d + 1)]
    word = []
    def build(mask, invs):
        if len(word) == n:
            if len(verts) >= cap:
                raise IntervalCap
            if len(verts) % 256 == 0:
                tick()
            level = top_length - invs
            layers[level].append(len(verts))
            verts.append(tuple(word))
            depth.append(level)
            return
        digit = 0
        for y in range(n):
            bit = 1 << y
            if not mask & bit:
                if allowed[mask | bit]:
                    word.append(y)
                    build(mask | bit, invs + digit)
                    word.pop()
                digit += 1
    top_length = length(v)
    build(0, 0)
    index = {p: i for i, p in enumerate(verts)}
    assert len(layers[0]) == len(layers[d]) == 1
    labels = [(i, j) for i in range(n) for j in range(i + 1, n)]
    # Exact packed polynomial arithmetic. With m labels, let C=4m+1.
    # Inductively ||P||_1 <= C^d: from a fixed lower vertex there are at
    # most m^k paths of k edges, of weight norm <= 2^k, leaving gap <= d-k.
    # Summing the resulting geometric series over k>=1 costs less than C^d.
    # The same bound applies to the strict R*P sum before truncation.
    # Thus balanced low digits can be recovered exactly at this base.
    bits = (2 * (4 * len(labels) + 1) ** d + 2).bit_length() + 1
    base = 1 << bits
    degree = (d - 1) // 2
    modulus = 1 << (bits * (degree + 1))
    mask_all = modulus - 1
    edge_groups = []
    for i, j in reversed(labels):
        tick()
        edges = []
        for hi, p in enumerate(verts):
            if p[i] > p[j]:
                lo = index.get(swap(p, i, j))
                if lo is not None:
                    h = depth[lo] - depth[hi]
                    assert h > 0 and h % 2 == 1
                    edges.append((hi, lo, bits * ((h - 1) // 2)))
        edge_groups.append(edges)
    sums = [0] * len(verts)
    for level, layer in enumerate(layers):
        tick()
        flow = [0] * len(verts)
        for u in layer:
            if level == 0:
                value = 1
            else:
                # q^level P(1/q) = P + strict sum R*P. The left side
                # vanishes through degree floor((level-1)/2).
                mod = 1 << (bits * ((level + 1) // 2))
                value = (-sums[u]) % mod
                if 2 * value > mod:
                    value -= mod
            flow[u] = value & mask_all
        if level == d:
            packed = flow[index[a]]
            coeffs = []
            for _ in range(degree + 1):
                c = packed % base
                if 2 * c > base:
                    c -= base
                coeffs.append(c)
                packed = (packed - c) // base
            assert coeffs[0] == 1 and min(coeffs) >= 0
            return coeffs, len(verts)
        for edges in edge_groups:
            for hi, lo, shift in edges:
                f = flow[hi]
                if f:
                    flow[lo] = (flow[lo] + (((f << bits) - f) << shift)) & mask_all
        for deeper in layers[level + 1:]:
            for u in deeper:
                sums[u] = (sums[u] + flow[u]) & mask_all
    raise AssertionError('missing bottom endpoint')

def one_based(p):
    return [x + 1 for x in p]

def sanity():
    sig = signatures(4)
    a = (0, 2, 1, 3)
    v = (2, 3, 0, 1)
    assert kl(a, v, sig)[0] == [1, 1]
    assert kl((0, 1, 2), (2, 1, 0), signatures(3))[0] == [1, 0]
    assert chain_test(a, v, sig)[0]
    assert not chain_test((0, 1, 2, 3), (1, 0, 3, 2), sig)[0]
    # Independent ordinary sorted-prefix and descent tests, including
    # a nonzero restart rank, check the candidate generator on all S4 lowers.
    def desc(p):
        return {i for i in range(3) if p[i] > p[i + 1]}
    perms = list(permutations(range(4)))
    for p in perms:
        for gap in (1, 3):
            expected = [(r, q) for r, q in enumerate(perms) if r >= 5 and length(q) == length(p) + gap and desc(q) <= desc(p) and desc(inverse(q)) <= desc(inverse(p)) and all(all(i <= j for i, j in zip(sorted(p[:k]), sorted(q[:k]))) for k in range(1, 4))]
            assert list(upper_candidates(p, gap, sig, 5, [0, 0])) == expected
    return 'Passed polynomial, connectivity, descent, Bruhat-order and restart checks.'

n = 10
size = factorial(n)
# Rotate the outer lexicographic order to begin at a lower endpoint with
# several left and right descents. Every outer index still occurs once.
pivot = rank_perm((2, 1, 0, 5, 4, 3, 9, 8, 7, 6))
start = list(params.get('cursor', [0, 0]))
end = int(params.get('outer_end', size))
assert len(start) == 2 and 0 <= start[0] <= end <= size and 0 <= start[1] <= size
progress = start.copy()
counts = dict(generated=0, canonical_three_cycle=0, connected_evaluated=0)
best = None
hit = None
checks = 'pending'
status = 'range_complete'
try:
    checks = sanity()
    sig = signatures(n)
    for outer in range(start[0], end):
        first = start[1] if outer == start[0] else 0
        progress[:] = [outer, first]
        tick()
        a = unrank(n, (outer + pivot) % size)
        ai = images(a)
        la = length(a)
        if la <= 17 and a == min(ai):
            ties = [i for i in range(1, 4) if ai[i] == a]
            for r, v in upper_candidates(a, 11, sig, first, progress):
                progress[:] = [outer, r]
                tick()
                counts['generated'] += 1
                parts = cycles(a, v)
                if len(parts) != 3:
                    continue
                vi = images(v)
                if any(vi[i] < v for i in ties):
                    continue
                if la == 17:
                    da = tuple(n - 1 - z for z in v)
                    dv = tuple(n - 1 - z for z in a)
                    if min(zip(images(da), images(dv))) < (a, v):
                        continue
                counts['canonical_three_cycle'] += 1
                connected, chain = chain_test(a, v, sig)
                if connected:
                    coeffs, order = kl(a, v, sig)
                    counts['connected_evaluated'] += 1
                    if best is None or coeffs[5] > best['mu']:
                        best = dict(a=one_based(a), v=one_based(v), lengths=[la, la + 11], relative_cycles=parts, upward_position_swaps=chain, interval_size=order, coefficients_low_to_high=coeffs, mu=coeffs[5], candidate_cursor=[outer, r])
                    if coeffs[5] >= 5:
                        hit = best
                        status = 'witness'
                        break
                progress[1] = r + 1
        if hit is not None:
            break
        progress[:] = [outer + 1, 0]
except Budget:
    status = 'time_budget'
except IntervalCap:
    status = 'interval_cap'

if hit is not None:
    summary = 'An eligible interval attains the threshold.'
elif status == 'range_complete' and start == [0, 0] and end == size:
    summary = 'Exhaustive negative result for the S10 target.'
elif status == 'range_complete':
    summary = 'The specified cursor range contains no witness.'
else:
    summary = 'Partial traversal. Resume at next_cursor, inclusively. For interval_cap, increase interval_cap on retry.'
result = dict(summary=summary, status=status, sanity=checks, start_cursor=start, next_cursor=progress, outer_end=end, full_outer_end=size, lower_rank_rotation=pivot, counters_this_invocation=counts, maximum_among_evaluated=best, witness=hit, elapsed_seconds=round(time.monotonic() - started, 3))
with open('result.json', 'w') as f:
    json.dump(result, f)
