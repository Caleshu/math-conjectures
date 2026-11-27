# MathResearchLab experiment 21dffd1d-d220-4d45-bd67-3287e81e9303
# Targeted search along genus-zero chains in $S_{10}$ and $S_{11}$
# sha256(code) = f4a1977f42cbcbb2bf8506db118a4c2715eb76bcbd82e423b34e6fa6b1c7ff83
# parameters: {"ranks": [10, 11], "seed": 7319, "chains": 120000, "node_cap": 4500, "seconds_per_pair": 4, "seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import random
import time
from collections import Counter

params = json.load(open(os.environ['MRL_PARAMS']))
rng = random.Random(int(params.get('seed', 7319)))
ranks = list(params.get('ranks', [10,11]))
assert ranks and all(4 <= m <= 11 for m in ranks)
stop = time.monotonic() + min(105, float(params.get('seconds', 95)))
node_cap = int(params.get('node_cap', 4500))
per_pair = float(params.get('seconds_per_pair', 4))

class TooLarge(Exception):
    pass

class OutOfTime(Exception):
    pass

def check(t):
    if time.monotonic() >= t:
        raise OutOfTime

def swap(p, i, j):
    q = list(p)
    q[i], q[j] = q[j], q[i]
    return tuple(q)

def length(p):
    return sum(a > b for i, a in enumerate(p) for b in p[i+1:])

def inverse(p):
    q = [0]*len(p)
    for i, a in enumerate(p):
        q[a] = i
    return tuple(q)

def desc(p):
    return {i for i in range(len(p)-1) if p[i] > p[i+1]}

def cycles(p):
    label = [-1]*len(p)
    for i in range(len(p)):
        j = i
        while label[j] == -1:
            label[j] = i
            j = p[j]
    return label

def uncompressible(x,w):
    return all(a != w[i] or sum(t >= a for t in x[:i]) != sum(t >= a for t in w[:i]) for i,a in enumerate(x))

def up_edges(p):
    for i, a in enumerate(p):
        least = len(p)
        for j in range(i+1,len(p)):
            b = p[j]
            if a < b < least:
                yield i,j
                least = b

def growing_chain(m):
    x = tuple(rng.sample(range(m), m))
    ix = inverse(x)
    w = x
    components = list(range(m))
    chain = []
    dx, dix = desc(x), desc(ix)
    for d in range(1,2*m-1):
        cyc = cycles(tuple(ix[a] for a in w))
        joins, splits = [], []
        for i,j in up_edges(w):
            if components[i] != components[j]:
                joins.append((i,j))
            elif cyc[i] == cyc[j]:
                splits.append((i,j))
        if not joins and not splits:
            break
        choices = joins if joins and (not splits or rng.random() < 0.78) else splits
        i,j = rng.choice(choices)
        old, new = components[j], components[i]
        components = [new if t == old else t for t in components]
        w = swap(w,i,j)
        chain.append((i+1,j+1))
        if d % 2 and len(set(components)) == 1:
            c = len(set(cycles(tuple(ix[a] for a in w))))
            assert length(w)-length(x) == d == m+c-2
            if desc(w) <= dx and desc(inverse(w)) <= dix and uncompressible(x,w):
                yield x,w,c,list(chain)

def interval(x,w,cap,t):
    # Bruhat comparison uses the sorted values in each initial segment.
    m = len(x)
    lower = [sorted(x[:i]) for i in range(m+1)]
    allowed = []
    for mask in range(1 << m):
        vals = [i for i in range(m) if mask & (1 << i)]
        allowed.append(all(a <= b for a,b in zip(lower[len(vals)],vals)))
    def above_x(p):
        mask = 0
        for b in p:
            mask |= 1 << b
            if not allowed[mask]:
                return False
        return True
    nodes, depth, index = [w], [0], {w: 0}
    for k,p in enumerate(nodes):
        if k % 64 == 0:
            check(t)
        for i,a in enumerate(p):
            largest = -1
            for j in range(i+1,m):
                b = p[j]
                if largest < b < a:
                    largest = b
                    q = swap(p,i,j)
                    if q not in index and above_x(q):
                        if len(nodes) >= cap:
                            raise TooLarge
                        index[q] = len(nodes)
                        nodes.append(q)
                        depth.append(depth[k]+1)
    assert x in index and depth[index[x]] == length(w)-length(x)
    return nodes, depth, index

def kl(x,w,cap,t):
    nodes, depth, index = interval(x,w,cap,t)
    n, m, d = len(nodes), len(x), depth[index[x]]
    if d == 0:
        return [1],n
    top = (d-1)//2
    # Dyer's increasing-path formula for ordinary R-polynomials. Process
    # transpositions in reverse lexicographic order to send mass downward.
    # An upward edge of length 2h+1 has ordinary weight q^h*(q-1).
    groups = []
    for i in reversed(range(m)):
        for j in reversed(range(i+1,m)):
            check(t)
            edges = []
            for b,p in enumerate(nodes):
                if p[i] > p[j]:
                    a = index.get(swap(p,i,j))
                    if a is not None:
                        gap = depth[a]-depth[b]
                        assert gap > 0 and gap % 2
                        h = (gap-1)//2
                        if h <= top:
                            edges.append((b,a,h))
            groups.append(edges)
    layers = [[] for _ in range(d+1)]
    for a,k in enumerate(depth):
        layers[k].append(a)
    sums = [[0]*(top+1) for _ in nodes]
    for k,layer in enumerate(layers):
        check(t)
        mass = [None]*n
        for a in layer:
            if k == 0:
                p = [1]
            else:
                # Low-degree part of the KL inversion identity gives P_{u,w}
                # from the already accumulated sum over u < v <= w.
                p = [-v for v in sums[a][:(k-1)//2+1]]
            assert p[0] == 1 and min(p) >= 0
            if a == index[x]:
                return p,n
            mass[a] = p + [0]*(top+1-len(p))
        for edges in groups:
            check(t)
            for b,a,h in edges:
                src = mass[b]
                if src is None:
                    continue
                dest = mass[a]
                if dest is None:
                    dest = mass[a] = [0]*(top+1)
                for s in range(top-h+1):
                    dest[s+h] -= src[s]
                    if s+h < top:
                        dest[s+h+1] += src[s]
        for a,poly in enumerate(mass):
            if depth[a] > k and poly is not None:
                for s,v in enumerate(poly):
                    sums[a][s] += v
    raise AssertionError('lower endpoint missing')

# The singular rank-three test detects loss of the top term. The longest
# S4 interval also exercises non-cover reflections and cancellation.
sanity_time = time.monotonic()+8
assert kl((0,2,1,3),(2,3,0,1),64,sanity_time)[0] == [1,1]
assert kl((0,1,2,3),(3,2,1,0),64,sanity_time) == ([1,0,0],24)
assert set(up_edges((0,1,2,3))) == {(0,1),(1,2),(2,3)}
counts = Counter()
hist = Counter()
seen = set()
best = None
for trial in range(int(params.get('chains', 120000))):
    if time.monotonic() >= stop:
        break
    m = ranks[trial % len(ranks)]
    counts['chains_started'] += 1
    for x,w,c,chain in growing_chain(m):
        if (x,w) in seen:
            continue
        seen.add((x,w))
        counts['distinct_candidates'] += 1
        try:
            p,n = kl(x,w,node_cap,min(stop,time.monotonic()+per_pair))
        except TooLarge:
            counts['skipped_node_cap'] += 1
            continue
        except OutOfTime:
            counts['skipped_time_cap'] += 1
            continue
        counts['exact_polynomials'] += 1
        d = len(chain)
        a = p[(d-1)//2]
        hist[f'm={m},d={d},c={c},coefficient={a}'] += 1
        if best is None or a > best['coefficient']:
            best = {'x': [b+1 for b in x], 'w': [b+1 for b in w], 'd': d, 'c': c, 'chain_position_swaps_one_based': chain, 'interval_size': n, 'P_low_to_high': p, 'coefficient': a}
        if a > 1:
            break
    if best is not None and best['coefficient'] > 1:
        break
found = best is not None and best['coefficient'] > 1
result = {'summary': f"Evaluated {counts['exact_polynomials']} distinct candidates. Counterexample found: {found}.", 'seed': int(params.get('seed',7319)), 'sanity_passed': True, 'counts': dict(counts), 'histogram': dict(hist), 'strongest_example': best, 'search_support': {'author_support': 'heuristic', 'justification': 'Starting permutations, chain choices, endpoint filters, and resource caps restrict coverage.'}, 'chain_invariant': {'author_support': 'proved_here', 'justification': 'Initially d=0 and both component count k and cycle count c equal m. A cover joining components increases d by one and decreases both k and c by one, since distinct components contain distinct product cycles. A cover inside one product cycle increases both d and c by one and preserves k. Both moves preserve d-m-c+2k=0. The generator checks the endpoint equality again when k=1.'}, 'R_formula': {'author_support': 'recalled_literature', 'justification': 'The second KL implementation uses Dyer\'s reflection-order formula for R-polynomials, with lexicographic order on type-A transpositions. The formula has not been checked against a source here.'}}
with open('result.json','w') as out:
    json.dump(result,out)
