# MathResearchLab experiment 6d12fc68-801d-4768-8039-147935e63868
# Exact adjacent-swap matching test in rank five
# sha256(code) = fe0cc9e4409935402218765ec9ef5bf878c3397a3d29c239fe81654699693092
# parameters: {"seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from collections import Counter, deque
from itertools import combinations_with_replacement, permutations, product
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
start = monotonic()
budget = min(95.0, float(params['seconds']))

def require(condition, message):
    if not condition:
        raise AssertionError(message)

P = list(permutations(range(1, 6)))
length = [sum(x > y for i, x in enumerate(p) for y in p[i+1:]) for p in P]
# A bit selects the pair (compatible label, simple-generator index).
cells = [(r, a) for r in range(1, 5) for a in range(4, r-1, -1)]

def encode(weight):
    return sum(x << (4*i) for i, x in enumerate(weight))

bags = {p: {} for p in P}
for mask in range(1 << len(cells)):
    p = list(P[0])
    weight = [0]*4
    for k, (r, a) in enumerate(cells):
        if mask & (1 << k):
            if p[a-1] > p[a]:
                break
            p[a-1], p[a] = p[a], p[a-1]
            weight[r-1] += 1
    else:
        bags[tuple(p)].setdefault(encode(weight), []).append(mask)
counts = [{w: len(masks) for w, masks in bags[p].items()} for p in P]

def polynomial(p):
    return {w: len(ms) for w, ms in bags[tuple(p)].items()}

require(polynomial(P[0]) == {0: 1}, 'empty word')
require(polynomial((1,3,2,4,5)) == {1: 1, 16: 1}, 's2 labels')
require(polynomial((2,3,1,4,5)) == {17: 1}, 'strict rise or right multiplication')
require(polynomial((3,1,2,4,5)) == {2: 1}, 'reversed word')
require(polynomial(P[-1]) == {encode((4,3,2,1)): 1}, 'longest permutation')

# The fifth coordinate is always zero. Indices refer to lexicographic order below.
weights = list(permutations(range(1, 5)))
index = {encode(w): i for i, w in enumerate(weights)}
odd = [i for i, w in enumerate(weights) if sum(x < y for j, x in enumerate(w) for y in w[j+1:]) % 2]
even = sorted(set(range(24)) - set(odd))
adj = {}
for i in odd:
    w = weights[i]
    neighbors = []
    for k in range(3):
        v = list(w)
        v[k], v[k+1] = v[k+1], v[k]
        neighbors.append(index[encode(v)])
    adj[i] = sorted(neighbors)
require(index[encode((4,3,2,1))] in even and all(j in even for ns in adj.values() for j in ns), 'parity')

def profile(triple):
    a, b, c = (counts[k] for k in triple)
    h = [0]*24
    for x, nx in a.items():
        for y, ny in b.items():
            for z, nz in c.items():
                j = index.get(x+y+z)
                if j is not None:
                    h[j] += nx*ny*nz
    return tuple(h)

def match(h):
    # Integral flow. Each allowed odd-to-even edge has unlimited capacity.
    left = list(h)
    right = list(h)
    flow = Counter()
    while True:
        roots = [i for i in odd if left[i] > 0]
        if not roots:
            edges = [[i,j,f] for (i,j),f in sorted(flow.items()) if f]
            require(all(f > 0 and j in adj[i] for i,j,f in edges), 'invalid flow edge')
            require(all(sum(f for i,j,f in edges if i == k) == h[k] for k in odd), 'uncovered source')
            require(all(sum(f for i,j,f in edges if j == k) <= h[k] for k in even), 'overfilled target')
            return edges, None
        parent = dict.fromkeys(roots)
        queue = deque(roots)
        sink = None
        while queue and sink is None:
            k = queue.popleft()
            if k in adj:
                for j in adj[k]:
                    if j in parent:
                        continue
                    parent[j] = k
                    if right[j] > 0:
                        sink = j
                        break
                    queue.append(j)
            else:
                for i in odd:
                    if i not in parent and flow[i,k] > 0:
                        parent[i] = k
                        queue.append(i)
        if sink is None:
            s = sorted(i for i in odd if i in parent)
            t = sorted({j for i in s for j in adj[i] if h[j]})
            require(sum(h[i] for i in s) > sum(h[j] for j in t), 'invalid Hall witness')
            return None, (s,t)
        k = sink
        amount = right[sink]
        while parent[k] is not None:
            prev = parent[k]
            if k in adj:
                amount = min(amount, flow[k,prev])
            k = prev
        amount = min(amount, left[k])
        left[k] -= amount
        right[sink] -= amount
        k = sink
        while parent[k] is not None:
            prev = parent[k]
            if k in adj:
                flow[k,prev] -= amount
            else:
                flow[prev,k] += amount
            k = prev

# Exercise both outcomes, including a Hall failure with equal total populations.
i0 = odd[0]
h = [0]*24
h[i0] = 2
h[adj[i0][0]] = h[adj[i0][1]] = 1
require(match(h)[0] is not None, 'capacity splitting')
h[adj[i0][1]] = 0
h[next(j for j in even if j not in adj[i0])] = 1
require(match(h)[1] == ([i0], [adj[i0][0]]), 'local Hall obstruction')

# The sorted factors are (u,v,w0*w), so all six factor orders are equivalent.
levels = Counter(length)
ordered_total = sum(na*nb*levels[10-a-b] for a,na in levels.items() for b,nb in levels.items())
certificates = {}
checked = ordered_checked = 0
status = 'all_covered'
failure = None
next_triple = None
for triple in combinations_with_replacement(range(len(P)), 3):
    if sum(length[k] for k in triple) != 10:
        continue
    if monotonic() - start >= budget:
        status = 'partial'
        next_triple = [P[k] for k in triple]
        break
    h = profile(triple)
    checked += 1
    ordered_checked += (1,3,6)[len(set(triple))-1]
    if not any(h[i] for i in odd) or h in certificates:
        continue
    edges, obstruction = match(h)
    if obstruction is None:
        certificates[h] = edges
        continue
    status = 'hall_obstruction'
    s,t = obstruction
    factors = [P[k] for k in triple]
    # Independently expand the deficient blocks and their entire neighborhood.
    objects = [[] for _ in weights]
    for blocks in product(*(bags[p].items() for p in factors)):
        j = index.get(sum(w for w,ms in blocks))
        if j is not None:
            objects[j].extend(product(*(ms for w,ms in blocks)))
    require(tuple(map(len,objects)) == h, 'expanded histogram')
    negative = sorted(m for i in s for m in objects[i])
    positive = sorted(m for j in t for m in objects[j])
    require(len(negative) > len(positive), 'expanded deficiency')
    failure = {'u': factors[0], 'v': factors[1], 'w': [6-x for x in factors[2]], 'factors': factors, 'profile': h, 'negative_weight_indices': s, 'neighbor_weight_indices': t, 'negative_mask_triples': negative, 'all_positive_neighbor_mask_triples': positive, 'deficiency': len(negative)-len(positive)}
    break
if status == 'all_covered':
    require(ordered_checked == ordered_total, 'ordered scope mismatch')

result = {
    'summary': {'all_covered': 'Every eligible ordered triple in S5 has a covering matching.', 'hall_obstruction': 'A deficient set rules out a covering matching for the displayed triple.', 'partial': 'The time guard stopped enumeration. The universal rank-five test remains open.'}[status],
    'author_support': 'proved_here',
    'justification': 'Within each factor, compatible labels increase weakly. In a run of equal labels the generators decrease weakly by compatibility, and adjacent equal generators would contradict reducedness. Thus the run decreases strictly. Each compatible pair selects a unique subset of the listed cells, and each accepted subset gives a compatible pair because every selected swap increases length. Total degree is ten, so packed weight addition never carries in base sixteen. A staircase weight has zero last coordinate, and swapping that coordinate cannot yield an object. All objects of a given odd weight have the same complete neighboring even blocks. The supplied integral edge counts therefore lift to the matching specified by the decoding rule. A Hall witness lists whole odd blocks and every object of each adjacent nonempty even block. Permuting the three factors preserves weights and adjacency, which transports either certificate to any factor order.',
    'status': status, 'solver': 'custom exact integral augmenting paths, no external solver', 'sanity_checks_passed': True,
    'eligible_ordered_total': ordered_total, 'canonical_triples_examined': checked, 'ordered_triples_represented': ordered_checked, 'first_unexamined_factors_if_partial': next_triple,
    'cells_in_low_to_high_bit_order': cells, 'weights_in_index_order_fifth_coordinate_omitted': weights, 'odd_weight_indices': odd,
    'certificate_decoding': 'For an ordered triple sort the three factors (u,v,w0*w) lexicographically, breaking ties by original position. Form its 24-entry profile by counting mask triples by weight. Zero odd population uses the empty matching. Otherwise look up that profile below. Each edge [i,j,f] uses f objects. Within odd block i sort mask triples lexicographically and split into consecutive segments by increasing destination j. Within even block j do the same by increasing source i, leaving any unused suffix free. Pair corresponding segment entries in order and undo the factor sort. Only successful profiles encountered before stopping are included.',
    'matching_certificates': [{'profile': h, 'edges': edges} for h,edges in certificates.items()], 'failure': failure
}
with open('result.json','w') as out:
    json.dump(result, out, separators=(',',':'))
