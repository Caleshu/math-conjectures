# MathResearchLab experiment 52ac6990-6801-4a9e-8daf-abf639f600be
# Exact bridge-join comparison with a resumable search interval
# sha256(code) = 7cc4904cb3f0c2df0f393555fa6d88a3537891728780adb66398b748a8bbda87
# parameters: {"seconds": 90, "cursor": [0, 0]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
start = time.monotonic()
params = json.load(open(os.environ['MRL_PARAMS']))
import itertools
import networkx as nx
import numpy as np
import sympy as sp

N = 11
S = 16384
I = np.eye(N, dtype=np.int64)
left, right = np.triu_indices(N, 1)
stop = start + min(100, max(2, int(params.get('seconds', 90))))
resume = tuple(map(int, params.get('cursor', [0, 0])))
counts = dict(intervals=0, no_bridge=0, edge_or_resistance_bound=0, potential_bound=0, exact_leaves=0)

def exact_ht(g):
    # Each target gives a separate Dirichlet problem Lh = degree.
    nodes = list(range(len(g)))
    degree = [g.degree(u) for u in nodes]
    lap = sp.diag(*degree)
    for u, v in g.edges():
        lap[u, v] = lap[v, u] = -1
    h = sp.zeros(len(g))
    for target in nodes:
        keep = [i for i in nodes if i != target]
        col = lap.extract(keep, keep).inv(method='DM') * sp.Matrix([degree[i] for i in keep])
        for i, value in zip(keep, col):
            h[i, target] = value
    return sum(max(h[i,j], h[j,i]) for i,j in itertools.combinations(nodes, 2))

anchor = nx.lollipop_graph(6, 5)
anchor_score = exact_ht(anchor)
assert 3 * anchor_score == 11950 and exact_ht(nx.path_graph(6)) == 223

def tree_data(tree):
    n = len(tree)
    edges = sorted(tuple(sorted(e)) for e in tree.edges())
    dist = np.array([[nx.shortest_path_length(tree, i, j) for j in range(n)] for i in range(n)], dtype=np.int64)
    allowed, forbidden = [], []
    for a,b in itertools.combinations(range(n), 2):
        if dist[a,b] == 1:
            continue
        cover = 0
        for h,(u,v) in enumerate(edges):
            side = dist[:,u] < dist[:,v]
            if side[a] == side[b]:
                continue
            cover |= 1 << h
            if not side[a]:
                u,v = v,u
                side = ~side
            # Distance change summed over all separated pairs.
            change = ((dist[side,a]-dist[side,u]).sum() * (~side).sum()
                      + (dist[~side,b]-dist[~side,v]).sum() * side.sum())
            if change < 0:
                break
        else:
            allowed.append((a,b,cover))
            continue
        forbidden.append((a,b))
    allowed.sort(key=lambda e: (-e[2].bit_count(), e[0], e[1]))
    return edges, dist, allowed, forbidden

# Check the coverage mechanism against an independent complete small catalog.
# The test includes the exchange filter and the bridge-cut mask.
small = [g for g in nx.graph_atlas_g() if len(g) == 5 and nx.is_connected(g) and nx.has_bridges(g)]
found = set()
for tree in nx.nonisomorphic_trees(5):
    edges, _, chords, _ = tree_data(tree)
    for mask in range(1 << len(chords)):
        g = nx.Graph(edges)
        crossed = 0
        for j,(a,b,c) in enumerate(chords):
            if mask >> j & 1:
                g.add_edge(a,b)
                crossed |= c
        assert (crossed != 15) == nx.has_bridges(g)
        if crossed != 15:
            found.update(i for i,x in enumerate(small) if nx.is_isomorphic(x,g))
assert found == set(range(len(small)))

trees = sorted(tuple(sorted(tuple(sorted(e)) for e in t.edges())) for t in nx.nonisomorphic_trees(N))
assert len(trees) == 235
assert 0 <= resume[0] < len(trees) and resume[1] >= 0
class Verdict(Exception):
    pass

def search_tree(ti):
    tree = nx.Graph(trees[ti])
    edges, dist, chords, forbidden = tree_data(tree)
    q = len(chords)
    first = resume[1] if ti == resume[0] else 0
    assert 0 <= first < (1 << q)
    pairlist = forbidden + [(a,b) for a,b,_ in chords]
    aa,bb = np.array(pairlist, dtype=np.int64).T
    f = len(forbidden)
    grams = (dist[:,0,None] + dist[None,0,:] - dist) * (S//2)
    base_adj = nx.to_numpy_array(tree, nodelist=range(N), dtype=np.int64)

    def visit(h, word, crossed, m0, Q):
        p = q-h
        keep = (((word+1) << p)-1 >= first)
        if not keep.any():
            return
        word,crossed,m0,Q = (v[keep] for v in (word,crossed,m0,Q))
        cursor = [ti, max(first, int(word[0]) << p)]
        if time.monotonic() >= stop:
            raise Verdict({'status':'PARTIAL', 'next_cursor':cursor})
        # Split in increasing full-word order so a single cursor covers all pending work.
        if len(word) > 192:
            mid = len(word)//2
            for s in (slice(None,mid), slice(mid,None)):
                visit(h,word[s],crossed[s],m0[s],Q[s])
            return
        counts['intervals'] += len(word)
        keep = crossed != 1023
        counts['no_bridge'] += int((~keep).sum())
        word,crossed,m0,Q = (v[keep] for v in (word,crossed,m0,Q))
        if not len(word):
            return
        diag = Q.diagonal(axis1=1, axis2=2)
        upper = diag[:,aa] + diag[:,bb] - 2*Q[:,aa,bb]
        chosen = (word[:,None] >> np.arange(h-1,-1,-1,dtype=np.int64)) & 1
        fixed = 10*S + upper[:,:f].sum(axis=1) + (upper[:,f:f+h]*(1-chosen)).sum(axis=1)
        largest = np.sort(upper[:,f+h:], axis=1)[:,::-1]
        K = fixed[:,None] + np.pad(largest.cumsum(axis=1), ((0,0),(1,0)))
        m = m0[:,None] + p - np.arange(p+1)
        possible = (m>=14) & (m<=35) & (3*(2*m*K-(110-m)*S) > 11950*S)
        keep = possible.any(axis=1)
        counts['edge_or_resistance_bound'] += int((~keep).sum())
        if not keep.any():
            return
        word,crossed,m0,Q,chosen,K,m,possible = (v[keep] for v in (word,crossed,m0,Q,chosen,K,m,possible))
        if p <= 6:
            hi_adj = np.repeat(base_adj[None,:,:], len(word), axis=0)
            lo_degree = np.broadcast_to(base_adj.sum(axis=1), (len(word),N)).copy()
            for j,(a,b,_) in enumerate(chords):
                bit = chosen[:,j] if j<h else 1
                hi_adj[:,a,b] = hi_adj[:,b,a] = bit
                if j<h:
                    lo_degree[:,a] += bit
                    lo_degree[:,b] += bit
            hi_degree = hi_adj.sum(axis=2)
            lap = hi_degree[:,:,None]*I - hi_adj
            dual = 2*S*Q - (Q @ lap @ Q)
            d = dual.diagonal(axis1=1,axis2=2)
            rlo = np.maximum(0,(d[:,:,None]+d[:,None,:]-2*dual)//S)
            d = Q.diagonal(axis1=1,axis2=2)
            rhi = d[:,:,None]+d[:,None,:]-2*Q
            dlo = (rlo*lo_degree[:,None,:]).sum(axis=2)
            dhi = (rhi*hi_degree[:,None,:]).sum(axis=2)
            asym = np.maximum(dhi[:,left]-dlo[:,right],dhi[:,right]-dlo[:,left]).sum(axis=1)
            keep = (possible & (3*(2*m*K+asym[:,None]) > 2*11950*S)).any(axis=1)
            counts['potential_bound'] += int((~keep).sum())
            word,crossed,m0,Q = (v[keep] for v in (word,crossed,m0,Q))
        if not len(word):
            return
        if p == 0:
            for w in word.tolist():
                if time.monotonic() >= stop:
                    raise Verdict({'status':'PARTIAL','next_cursor':[ti,w]})
                g = tree.copy()
                g.add_edges_from((a,b) for j,(a,b,_) in enumerate(chords) if (w >> (q-1-j)) & 1)
                if nx.diameter(g) < 3:
                    continue
                score = exact_ht(g)
                counts['exact_leaves'] += 1
                if 3*score > 11950:
                    bridge = next(nx.bridges(g))
                    cut = g.copy()
                    cut.remove_edge(*bridge)
                    shores = sorted(sorted(c) for c in nx.connected_components(cut))
                    raise Verdict({'status':'VIOLATION','cursor':[ti,w],'edges':sorted(tuple(sorted(e)) for e in g.edges()),'bridge':bridge,'shores':shores,'internal_edges':[cut.subgraph(c).number_of_edges() for c in shores],'diameter':nx.diameter(g),'HT':[int(sp.numer(score)),int(sp.denom(score))]})
            return
        a,b,c = chords[h]
        v = Q[:,:,a]-Q[:,:,b]
        den = S + v[:,a]-v[:,b]
        assert (den>0).all()
        updated = Q - (v[:,:,None]*v[:,None,:])//den[:,None,None] + N*I
        children = np.stack((Q,updated),axis=1).reshape(-1,N,N)
        bits = np.tile(np.array([0,1],dtype=np.int64),len(word))
        visit(h+1, 2*np.repeat(word,2)+bits, np.repeat(crossed,2)|(bits*c), np.repeat(m0,2)+bits, children)

    visit(0,np.array([0],dtype=np.int64),np.array([0],dtype=np.int64),np.array([10],dtype=np.int64),grams[None,:,:])

try:
    for ti in range(resume[0],len(trees)):
        search_tree(ti)
    result = {'status':'PASS' if resume==(0,0) else 'CLEAR_SUFFIX','next_cursor':None}
except Verdict as e:
    result = e.args[0]
result.update(start_cursor=list(resume), counts=counts, tree_count=len(trees), anchor_HT=str(anchor_score), small_bridge_classes=len(found), numpy_version=np.__version__, networkx_version=nx.__version__)
result['summary'] = {'PASS':'Full finite scope cleared.','CLEAR_SUFFIX':'Suffix cleared. A full certificate requires contiguous recorded intervals starting at [0,0] with the same program and library versions.','PARTIAL':'Only the interval from start_cursor up to, but excluding, next_cursor was cleared. Resume with cursor equal to next_cursor.','VIOLATION':'Exact violating bridge join found.'}[result['status']]
with open('result.json','w') as out:
    json.dump(result,out,sort_keys=True)
