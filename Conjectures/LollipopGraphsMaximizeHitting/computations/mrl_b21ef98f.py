# MathResearchLab experiment b21ef98f-ebdb-4685-8083-b6e488f2035e
# Exact order-11 search rooted at a pair of maximum effective resistance
# sha256(code) = f1af5b03625d73585e96cc3f2d751c11882c6048993015eb3d977303b0c146e3
# parameters: {"seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
import numpy as np

params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()
deadline = start + min(100.0, max(1.0, float(params.get('seconds', 90))))

# Store the grounded inverse as A/t, with row and column zero at vertex 0.
def tree_state(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    paths = [None] * n
    paths[0] = 0
    queue = [0]
    for u in queue:
        for v in adj[u]:
            if paths[v] is None:
                paths[v] = paths[u] | (1 << v)
                queue.append(v)
    assert len(queue) == n and len(edges) == n - 1
    A = np.array([[(x & y).bit_count() for y in paths] for x in paths], dtype=np.int64)
    return A, 1, tuple(map(len, adj))

def add(state, edge):
    A, t, degree = state
    u, v = edge
    s = t + int(A[u,u] + A[v,v] - 2*A[u,v])
    # Sherman-Morrison and the determinant lemma. Guard both products.
    raw = A if max(s, int(A.max())) <= 2000000000 else A.astype(object)
    z = raw[:,u] - raw[:,v]
    new_A = ((s*raw - np.outer(z,z)) // t).astype(np.int64)
    new_degree = list(degree)
    new_degree[u] += 1
    new_degree[v] += 1
    return new_A, s, tuple(new_degree)

def score(state, edges=None):
    A, t, degree = state
    n = len(degree)
    volume = sum(degree)
    p = A @ np.array(degree, dtype=np.int64)
    hits = p[:,None] - p[None,:] + volume*(A.diagonal()[None,:] - A)
    value = Fraction(sum(int(max(hits[i,j], hits[j,i])) for i,j in combinations(range(n),2)), t)
    if edges is not None:
        L = np.diag(degree)
        for i,j in edges:
            L[i,j] = L[j,i] = -1
        rhs = np.array(degree)[:,None] - volume*np.eye(n, dtype=np.int64)
        assert np.all(hits.diagonal() == 0) and np.array_equal(L @ hits, t*rhs)
    return value, hits

def lollipop(n,k):
    tree = [(0,v) for v in range(1,k)]
    if k < n:
        tree += [(0,k)] + [(v-1,v) for v in range(k+1,n)]
    extra = list(combinations(range(1,k),2))
    state = tree_state(n,tree)
    for e in extra:
        state = add(state,e)
    return score(state,tree+extra)[0]

assert lollipop(6,2) == 223 and lollipop(6,4) == 224
n = 11
pairs = list(combinations(range(n),2))
pi, pj = np.array(pairs).T
bench = {k:lollipop(n,k) for k in range(2,n+1)}
B = max(bench.values())
assert bench[6] == Fraction(11950,3) and B > 3600

# A rooted tree is the sorted tuple of its child subtrees.
@lru_cache(None)
def trees(size):
    if size == 1:
        return ((),)
    choices = sorted((s,tr) for s in range(1,size) for tr in trees(s))
    out = []
    def forest(left, first, children):
        if left == 0:
            out.append(tuple(children))
            return
        for i in range(first,len(choices)):
            s,tr = choices[i]
            if s > left:
                break
            forest(left-s,i,children+[tr])
    forest(size-1,0,[])
    return tuple(out)

def family(tr):
    queue = [tr]
    parent = [-1]
    depth = [0]
    edges = []
    for u,children in enumerate(queue):
        for child in children:
            edges.append((u,len(queue)))
            queue.append(child)
            parent.append(u)
            depth.append(depth[u]+1)
    if max(depth) < 3:
        return None
    opt = []
    for u,v in pairs:
        if depth[v] == depth[u]:
            opt.append((u,v))
        elif depth[v] == depth[u]+1 and u != parent[v] and len(queue[u]) < len(queue[parent[v]]):
            opt.append((u,v))
    state = tree_state(n,edges)
    A = state[0]
    opt.sort(key=lambda e: (-(int(A[e[0],e[0]]+A[e[1],e[1]]-2*A[e])),e))
    partners = tuple(v for v in range(n) if depth[v] >= 3 and state[2][v] <= state[2][0])
    if partners:
        return (max(depth), tuple(edges), tuple(opt), partners, state)
    return None

all_trees = trees(n)
assert len(all_trees) == 1842
families = [f for tr in all_trees if (f := family(tr)) is not None]
families.sort(key=lambda f:(-f[0],len(f[2]),f[1]))

# A job [i,p] uses family i. Drop the leading 1 from binary p to get
# the prefix of edge decisions. 0 excludes an edge and 1 includes it.
# next_family covers the untouched suffix. The frontier covers earlier IDs.
resume = params.get('resume', {})
next_family = int(resume.get('next_family',0))
jobs = [(int(i),int(p)) for i,p in resume.get('frontier',[])]
assert 0 <= next_family <= len(families)
assert all(0 <= i < next_family and p >= 1 and p.bit_length()-1 <= len(families[i][2]) for i,p in jobs)
visited = pruned = evaluated = 0
witness = None

# Sums in score fit int64: t is a spanning-tree count at most 11^9,
# and each grounded inverse entry lies between 0 and 10 before scaling.
def visit(i, prefix, pos, state):
    global visited, pruned, evaluated, witness
    if witness is not None:
        return
    if time.monotonic() >= deadline:
        pending.append((i,prefix))
        return
    visited += 1
    _, base, opt, partners, _ = families[i]
    A,t,deg = state
    cap = max((int(A[v,v]) for v in partners if deg[v] <= deg[0]),default=0)
    if cap <= 2*t:
        pruned += 1
        return
    diagonal = A.diagonal()
    weights = np.minimum(cap, diagonal[:,None] + diagonal[None,:] - 2*A)
    remaining_sum = int(weights[pi,pj].sum())
    m = sum(deg)//2
    costs = sorted(int(weights[e]) for e in opt[pos:])
    for q in range(len(costs)+1):
        final_m = m+q
        upper = 2*final_m*remaining_sum - (2*len(pairs)-final_m)*t
        if upper*B.denominator > B.numerator*t:
            break
        if q < len(costs):
            remaining_sum -= costs[q]
    else:
        pruned += 1
        return
    if pos == len(opt):
        evaluated += 1
        value,_ = score(state)
        if value > B:
            bits = bin(prefix)[3:]
            edges = list(base)+[e for e,b in zip(opt,bits) if b == '1']
            value,hits = score(state,edges)
            witness = {'edges':edges,'HT':str(value),'excess':str(value-B),'hitting_time_numerators':hits.tolist(),'common_denominator':t}
        return
    visit(i,2*prefix+1,pos+1,add(state,opt[pos]))
    visit(i,2*prefix,pos+1,state)

pending = []
while (jobs or next_family < len(families)) and witness is None and time.monotonic() < deadline:
    if jobs:
        i,prefix = jobs.pop()
    else:
        i,prefix = next_family,1
        next_family += 1
    opt = families[i][2]
    state = families[i][4]
    bits = bin(prefix)[3:]
    for bit,e in zip(bits,opt):
        if bit == '1':
            state = add(state,e)
    visit(i,prefix,len(bits),state)
pending.extend(jobs)
complete = witness is None and not pending and next_family == len(families)
status = 'COUNTEREXAMPLE' if witness else ('EXHAUSTED' if complete else 'PARTIAL')
remaining = sum(1 << (len(families[i][2])-(p.bit_length()-1)) for i,p in pending)
remaining += sum(1 << len(f[2]) for f in families[next_family:])
summary = {'COUNTEREXAMPLE':'A connected 11-vertex graph strictly exceeds the best lollipop.', 'EXHAUSTED':'Every candidate family was settled. A lollipop attains the global order-11 maximum.', 'PARTIAL':'The listed prefixes and untouched family suffix remain to be settled.'}[status]
result = {'summary':summary,'status':status,'n':n,'author_support':'proved_here' if status != 'PARTIAL' else 'proved_here','justification':'The benchmark and any witness satisfy the integer first-step equations. Family coverage and the pruning inequalities are given in the experiment justification. A partial run certifies only its completed branches.','lollipop_scores':{str(k):str(v) for k,v in bench.items()},'B':str(B),'maximizing_lollipop_k':[k for k,v in bench.items() if v==B],'rooted_families':len(families),'nodes_this_run':visited,'pruned_nodes_this_run':pruned,'exact_leaves_this_run':evaluated,'witness':witness,'resume':{'next_family':next_family,'frontier':pending} if status=='PARTIAL' else None,'remaining_edge_patterns_counted_with_family_multiplicity':remaining if status=='PARTIAL' else (0 if complete else None)}
with open('result.json','w') as out:
    json.dump(result,out)
