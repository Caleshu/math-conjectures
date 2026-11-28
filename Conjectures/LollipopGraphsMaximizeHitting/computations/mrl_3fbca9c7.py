# MathResearchLab experiment 3fbca9c7-c8d2-49c2-9ff4-e3a5e9b86fac
# Exact interval search over rooted bridge joins on eleven vertices
# sha256(code) = 59248912a6f2cbc1df576477c40f419d287ab7390c284fcabc5b981800da1de7
# parameters: {"seconds": 92}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from functools import lru_cache
from itertools import combinations
from fractions import Fraction

started = time.monotonic()
params = json.load(open(os.environ['MRL_PARAMS']))
import networkx as nx
import numpy as np
import sympy as sp

deadline = started + min(100.0, float(params.get('seconds', 92)))
N = 11
pairs = list(combinations(range(N), 2))
index = {p: i for i, p in enumerate(pairs)}
U, V = np.array(pairs).T
ALL = (1 << len(pairs)) - 1

def bit(u, v):
    return 1 << index[tuple(sorted((u, v)))]

def indices(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low

def edges(mask):
    return [pairs[i] for i in indices(mask)]

def shape(g, u, parent):
    return tuple(sorted(shape(g, v, u) for v in g[u] if v != parent))

# A rooted tree is encoded by the sorted tuple of its child encodings.
rooted = {1: [()]}
for size in range(2, 11):
    rooted[size] = sorted({shape(g, u, -1) for g in nx.nonisomorphic_trees(size) for u in g})
assert [len(rooted[i]) for i in range(1, 11)] == [1, 1, 2, 4, 9, 20, 48, 115, 286, 719]
cases = [(a, x, y) for a in range(1, 6) for x in rooted[a] for y in rooted[N-a]]

def grow(g, sh):
    u = len(g)
    g.add_node(u)
    for child in sh:
        v = grow(g, child)
        g.add_edge(u, v)
    return u

@lru_cache(maxsize=32)
def setup(case):
    a, left, right = cases[case]
    tree = nx.Graph()
    s = grow(tree, left)
    t = grow(tree, right)
    assert (s, t) == (0, a)
    tree.add_edge(s, t)
    tm = sum(bit(u, v) for u, v in tree.edges())
    dist = [nx.single_source_shortest_path_length(tree, i) for i in range(N)]
    optional = {p for p in pairs if (p[0] < a) == (p[1] < a) and not tm & bit(*p)}
    for s, t in tree.edges():
        A = [u for u in range(N) if dist[u][s] < dist[u][t]]
        B = [u for u in range(N) if dist[u][t] < dist[u][s]]
        ca = {x: len(B)*sum(dist[z][x] for z in A) for x in A}
        cb = {y: len(A)*sum(dist[z][y] for z in B) for y in B}
        old = ca[s] + cb[t]
        for x in A:
            for y in B:
                if ca[x] + cb[y] < old:
                    optional.discard(tuple(sorted((x, y))))
    chords = [index[p] for p in sorted(optional, key=lambda p: (-dist[p[0]][p[1]], p))]
    suffix = [0]*(len(chords)+1)
    for j in reversed(range(len(chords))):
        suffix[j] = suffix[j+1] | (1 << chords[j])
    # Ground vertex zero. On a tree the Green entry counts common root-path edges.
    green = np.array([[(dist[0][u]+dist[0][v]-dist[u][v])//2 for v in range(N)] for u in range(N)], dtype=np.int64)
    return tm, green, chords, suffix

def include(B, tau, e):
    u, v = pairs[e]
    w = B[:, u] - B[:, v]
    new_tau = tau + int(w[u]-w[v])
    # B is tau times the padded grounded inverse. Matrix determinant lemma
    # and Sherman-Morrison give an exact division. For m <= 35, AM-GM on
    # the ten positive Laplacian eigenvalues gives tau <= 7**10/11.
    # All entries of either scaled inverse are <= 10*tau in magnitude.
    num = new_tau*B - np.outer(w, w)
    return num//tau, new_tau

def score(mask, B, tau, details=False):
    deg = np.zeros(N, dtype=np.int64)
    for i in indices(mask):
        u, v = pairs[i]
        deg[u] += 1
        deg[v] += 1
    m2 = int(deg.sum())
    g = B @ deg
    delta = g[U]-g[V]
    forward = delta + m2*(B[V,V]-B[U,V])
    backward = -delta + m2*(B[U,U]-B[U,V])
    vals = np.maximum(forward, backward)
    return (int(vals.sum()), [int(v) for v in vals] if details else None)

def bound_closes(mask, optional, B, tau, threshold=11950):
    m0 = mask.bit_count()
    lo, hi = max(14, m0), min(35, m0+optional.bit_count())
    if lo > hi:
        return True
    r = (B[U,U]+B[V,V]-2*B[U,V]).tolist()
    fixed = [r[i] for i in indices(ALL ^ (mask | optional))]
    undecided = sorted(r[i] for i in indices(optional))
    # The same order maximizes the upper bound at every possible final size.
    cap = fixed + undecided
    t2 = tau*tau
    sum_r = sum(cap)
    loss = sum(max(2*t2, x*x) for x in cap)
    for j in range(hi-m0+1):
        m = m0+j
        if m >= lo:
            upper = 19*m*t2 + 2*m*tau*sum_r - loss
            if 3*upper > threshold*t2:
                return False
        if m < hi:
            x = undecided[j]
            sum_r -= x
            loss -= max(2*t2, x*x)
    return True

def direct(mask):
    adj = sp.zeros(N)
    for u, v in edges(mask):
        adj[u,v] = adj[v,u] = 1
    d = adj*sp.ones(N, 1)
    L = sp.diag(*list(d))-adj
    H = sp.zeros(N)
    for j in range(N):
        keep = [i for i in range(N) if i != j]
        h = L.extract(keep, keep).inv()*d.extract(keep, [0])
        for i, val in zip(keep, h):
            H[i,j] = val
    return sum(max(H[i,j], H[j,i]) for i,j in pairs)

# Independent sanity check at the proposed threshold, plus a pruning check
# on a full eight-completion interval containing that equality case.
base = [(0,i) for i in range(1,6)] + [(0,6)] + [(i,i+1) for i in range(6,10)]
g = nx.Graph(base)
d = dict(nx.all_pairs_shortest_path_length(g))
B0 = np.array([[(d[0][i]+d[0][j]-d[i][j])//2 for j in range(N)] for i in range(N)], dtype=np.int64)
mask0 = sum(bit(*p) for p in base)
tau0 = 1
extra = [index[p] for p in combinations(range(1,6),2)]
for e in extra[:-3]:
    B0, tau0 = include(B0, tau0, e)
    mask0 |= 1 << e
opt0 = sum(1 << e for e in extra[-3:])
local = []
for subset in range(8):
    mask, B, tau = mask0, B0, tau0
    for j, e in enumerate(extra[-3:]):
        if subset & (1 << j):
            B, tau = include(B, tau, e)
            mask |= 1 << e
    val = Fraction(score(mask,B,tau)[0], tau)
    assert val == Fraction(direct(mask))
    local.append(val)
assert local[-1] == Fraction(11950,3)
assert not bound_closes(mask0,opt0,B0,tau0,(3*max(local)).__ceil__()-1)

stats = dict(prefixes_tested=0, intervals_closed_by_bound=0, singleton_comparisons=0)
witness = None

def inspect(case, mask, B, tau):
    global witness
    stats['singleton_comparisons'] += 1
    val, _ = score(mask, B, tau)
    if 3*val <= 11950*tau:
        return
    g = nx.Graph()
    g.add_nodes_from(range(N))
    g.add_edges_from(edges(mask))
    diameter = nx.diameter(g)
    if diameter < 3:
        return
    a = cases[case][0]
    assert 14 <= g.number_of_edges() <= 35 and list(nx.edge_boundary(g, range(a))) == [(0,a)]
    exact = Fraction(direct(mask))
    assert exact == Fraction(val,tau)
    witness = dict(edges=edges(mask), bridge=[0,a], diameter=diameter, HT=str(exact), pair_order=pairs, common_denominator=tau, pair_max_numerators=score(mask,B,tau,True)[1])

# A job is [case index, bit string]. Bits follow the canonical chord order
# from setup(). A frontier produced on one run is valid with a new deadline.
full = 'frontier' not in params
jobs = [[i,''] for i in range(len(cases))] if full else list(params['frontier'])
# Use the least expensive pass across all supplied roots first.
remaining = []

def restore(case, prefix):
    if not 0 <= case < len(cases):
        raise ValueError('invalid case index')
    mask, B, chords, suffix = setup(case)
    if len(prefix) > len(chords) or set(prefix)-set('01'):
        raise ValueError('invalid decision prefix')
    tau = 1
    for flag,e in zip(prefix,chords):
        if flag == '1':
            if mask.bit_count() >= 35:
                raise ValueError('prefix exceeds maximum size')
            B, tau = include(B,tau,e)
            mask |= 1 << e
    return mask, B, tau, chords, suffix

def closed(case, mask, B, tau, optional):
    stats['prefixes_tested'] += 1
    m = mask.bit_count()
    if m >= 14 and (m == 35 or optional == 0):
        inspect(case, mask, B, tau)
        return True
    if bound_closes(mask, optional, B, tau):
        stats['intervals_closed_by_bound'] += 1
        return True
    return False

for pos, (case,prefix) in enumerate(jobs):
    if time.monotonic() >= deadline:
        remaining.extend(jobs[pos:])
        break
    mask,B,tau,chords,suffix = restore(case,prefix)
    if not closed(case,mask,B,tau,suffix[len(prefix)]):
        remaining.append([case,prefix])
    if witness:
        break

# Store matrices only for the active DFS. Unvisited siblings are serializable.
while remaining and witness is None and time.monotonic() < deadline:
    case,prefix = remaining.pop()
    mask,B,tau,chords,suffix = restore(case,prefix)
    stack = [(prefix,mask,B,tau)]
    while stack and witness is None and time.monotonic() < deadline:
        s,mask,B,tau = stack.pop()
        j = len(s)
        if closed(case,mask,B,tau,suffix[j]):
            continue
        e = chords[j]
        C,t = include(B,tau,e)
        stack.append((s+'0',mask,B,tau))
        stack.append((s+'1',mask | (1 << e),C,t))
    remaining.extend([case,item[0]] for item in stack)

status = 'VIOLATION' if witness else ('PARTIAL' if remaining else 'EXHAUSTED')
if witness:
    summary = 'An exact counterexample to the bridge-join inequality is attached.'
elif remaining:
    summary = 'Comparison unfinished. The frontier encodes the exact unclosed portion of the supplied scope.'
elif full:
    summary = 'Every rooted bridge join in the specified range satisfies the inequality.'
else:
    summary = 'Every supplied frontier prefix satisfies the inequality or contains no eligible join.'
result = dict(summary=summary, status=status, initial_scope='all cases' if full else 'supplied prefixes', rooted_tree_pair_cases=len(cases), stats=stats, sanity_scores=[str(x) for x in local], witness=witness, frontier=None if witness else remaining)
with open('result.json','w') as f:
    json.dump(result,f)
