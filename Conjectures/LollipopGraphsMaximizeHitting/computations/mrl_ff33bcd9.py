# MathResearchLab experiment ff33bcd9-9dba-459d-ba16-fe1d0023ca2b
# Exact bridge-join comparison with edge-count-sensitive pruning
# sha256(code) = a55ec3ac52334dac2d805d241f830b5d69a8d675d191f9dcdb54f7de294bb3d4
# parameters: {"seconds": 100}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from fractions import Fraction
from itertools import combinations
import networkx as nx
import numpy as np

params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()
deadline = start + min(105.0, float(params.get('seconds', 100)))
n = 11
pairs = list(combinations(range(n), 2))
I, J = np.array(pairs, dtype=np.int64).T
bit = {p: 1 << k for k, p in enumerate(pairs)}
scale = 4096
stats = dict(jobs_closed=0, intervals=0, score_bounds=0, terminal=0, symmetry=0)

def mask_edges(mask):
    return [p for p in pairs if mask & bit[p]]

def rooted(T, x, parent):
    return '(' + ''.join(sorted(rooted(T, y, x) for y in T[x] if y != parent)) + ')'

def inventory():
    jobs = []
    for T in nx.nonisomorphic_trees(n):
        dist = dict(nx.all_pairs_shortest_path_length(T))
        if max(max(row.values()) for row in dist.values()) < 3:
            continue
        tree = sum(bit[tuple(sorted(p))] for p in T.edges)
        cuts = []
        for p, q in T.edges:
            A = {x for x in T if dist[p][x] < dist[q][x]}
            B = set(T) - A
            changes = {}
            for side, end in [(A, p), (B, q)]:
                for u in side:
                    changes[u] = (n-len(side))*sum(dist[x][u]-dist[x][end] for x in side)
            cuts.append((p, q, A, changes))
        allowed = []
        for u, v in mask_edges(((1 << len(pairs))-1) ^ tree):
            if all((u in A) == (v in A) or ch[u]+ch[v] >= 0 for p,q,A,ch in cuts):
                allowed.append((u,v))
        pools = {}
        seen = set()
        for p,q,A,ch in cuts:
            key = tuple(sorted((rooted(T,p,q), rooted(T,q,p))))
            if key in seen:
                continue
            seen.add(key)
            pool = sum(bit[u,v] for u,v in allowed if (u in A) == (v in A))
            if pool.bit_count() >= 4:
                pools[pool] = tuple(sorted((p,q)))
        for pool, bridge in pools.items():
            if not any(pool != other and pool & other == pool for other in pools):
                jobs.append((pool.bit_count(),tree,pool,bridge))
    return sorted(jobs)

# K is the grounded inverse times its determinant, padded with a zero row
# and column for vertex 10. Each array has a leading batch dimension.
def tree_state(T):
    paths = [set(nx.shortest_path(T,n-1,i)[1:]) for i in range(n)]
    K = np.array([[len(a & b) for b in paths] for a in paths], dtype=np.int64)
    return K[None,:,:], np.ones(1,dtype=np.int64)

def change(K, tau, edge, sign):
    u,v = edge
    x = K[:,:,u]-K[:,:,v]
    t = tau + sign*(x[:,u]-x[:,v])
    assert np.all(t > 0)
    return (K*t[:,None,None]-sign*x[:,:,None]*x[:,None,:])//tau[:,None,None], t

def resistance(K):
    diag = np.diagonal(K,axis1=1,axis2=2)
    return diag[:,:,None]+diag[:,None,:]-2*K

def exact_scores(K,tau,deg):
    R = resistance(K)
    q = (R @ deg[:,:,None])[:,:,0]
    twice = deg.sum(axis=1)*R[:,I,J].sum(axis=1)+np.abs(q[:,I]-q[:,J]).sum(axis=1)
    return twice, 2*tau

def direct(G):
    # Independent rational solution, one absorbing target at a time.
    import sympy as sp
    verts = sorted(G)
    H = {}
    for j in verts:
        V = [i for i in verts if i != j]
        L = sp.Matrix([[G.degree(i) if i == k else -int(G.has_edge(i,k)) for k in V] for i in V])
        h = L.inv()*sp.Matrix([G.degree(i) for i in V])
        for i,val in zip(V,h):
            H[i,j] = Fraction(int(val.p),int(val.q))
    return sum(max(H[i,j],H[j,i]) for i,j in combinations(verts,2))

def sanity():
    assert direct(nx.lollipop_graph(4,2)) == 224
    G = nx.lollipop_graph(6,5)
    T = nx.bfs_tree(G,10).to_undirected()
    K,t = tree_state(T)
    initial = K.copy()
    added = [p for p in pairs if G.has_edge(*p) and not T.has_edge(*p)]
    for p in added:
        K,t = change(K,t,p,1)
    deg = np.array([[G.degree(i) for i in range(n)]])
    a,b = exact_scores(K,t,deg)
    val = Fraction(int(a[0]),int(b[0]))
    assert val == direct(G) == Fraction(11950,3)
    for p in reversed(added):
        K,t = change(K,t,p,-1)
    assert t.tolist() == [1] and np.array_equal(K,initial)
    return {'L(6,4)':'224','L(11,6)':str(val),'inverse_round_trip':True}

# For each batch row r, return True only when an upper bound certifies it.
def bounded(K,t,U,h,deg,extra,edges,level,tree,prefix):
    R = resistance(K)
    D = (scale*R+t[:,None,None]-1)//t[:,None,None]
    m = deg.sum(axis=1)//2
    opt = edges[level:]
    count = len(opt)
    M = np.minimum(35,m+count)
    # Outside the mandatory graph are permanently absent pairs and the
    # undecided edges. Prefix-selected edges are removed from this sum.
    outside = D[:,I,J].sum(axis=1) + 10*scale
    for u,v in mask_edges(tree):
        outside -= D[:,u,v]
    for j,(u,v) in enumerate(edges[:level]):
        outside -= D[:,u,v]*((prefix >> (level-1-j)) & 1)
    oi,oj = np.array(opt,dtype=np.int64).T
    costs = np.sort(D[:,oi,oj],axis=1)
    loss = np.pad(costs.cumsum(axis=1),((0,0),(1,0)))
    final = m[:,None]+np.arange(count+1)
    product = final*(outside[:,None]-loss)
    F = np.where((final>=14)&(final<=35),product,-1).max(axis=1)
    closed = 3*4*F <= 23900*scale
    r = np.flatnonzero(~closed)
    if not len(r):
        return closed
    D = D[r]
    E = scale*resistance(U[r])//h[r,None,None]
    d = deg[r,None,:]
    dij,eij = D[:,I,J],E[:,I,J]
    s = D[:,I,:]-E[:,J,:]
    z = D[:,J,:]-E[:,I,:]
    def delta(X):
        return (X*d+np.maximum(X,0)*extra).sum(axis=2)
    Q = np.maximum(delta(s),delta(z))
    b = 2*np.minimum(deg[r][:,I],deg[r][:,J])-1
    cap = np.minimum(Q,2*(M[r,None]-b)*dij)
    first = 2*F[r]+cap.sum(axis=1)
    def lower(X):
        return (np.maximum(eij[:,:,None]-X,0)*d).sum(axis=2)
    floor = np.maximum(2*b*eij,np.minimum(lower(s),lower(z)))
    second = 4*F[r]-floor.sum(axis=1)
    closed[r] = 3*np.minimum(first,second) <= 23900*scale
    return closed

def search(job):
    _,tree,pool,bridge = job
    T = nx.Graph(mask_edges(tree))
    dist = dict(nx.all_pairs_shortest_path_length(T))
    edges = sorted(mask_edges(pool),key=lambda p:(-dist[p[0]][p[1]],p))
    size = len(edges)
    K,t = tree_state(T)
    U,h = K,t
    for p in edges:
        U,h = change(U,h,p,1)
    deg0 = np.array([[T.degree(i) for i in range(n)]],dtype=np.int64)
    row0 = np.array([[sum(1 << (10-v) for v in T[i]) for i in range(n)]],dtype=np.int64)
    extra = np.zeros((size+1,n),dtype=np.int64)
    rowextra = np.zeros_like(extra)
    for j in reversed(range(size)):
        u,v = edges[j]
        extra[j] = extra[j+1]
        extra[j,[u,v]] += 1
        rowextra[j] = rowextra[j+1]
        rowextra[j,u] |= 1 << (10-v)
        rowextra[j,v] |= 1 << (10-u)
    twins = []
    for x,y in pairs:
        keep = 2047 ^ ((1 << (10-x)) | (1 << (10-y)))
        if deg0[0,x] == deg0[0,y] == 1 and ((row0[0,x]^row0[0,y]) & keep) == 0 and ((rowextra[0,x]^rowextra[0,y]) & keep) == 0:
            twins.append((x,y,keep))
    stack = [(0,np.array([0],dtype=np.int64),K,t,U,h,deg0,row0)]
    while stack:
        if time.monotonic() >= deadline:
            return {'status':'PARTIAL','ordered_chords':edges,'pending_prefixes':[[j,code.tolist()] for j,code,*_ in stack]}
        j,code,K,t,U,h,deg,rows = stack.pop()
        stats['intervals'] += len(code)
        m = deg.sum(axis=1)//2
        ok = (m<=35)&(m+size-j>=14)&(deg.max(axis=1)<10)
        # A bridge graph of diameter <=2 has a universal vertex: if both
        # shores are nontrivial the diameter is >=3, and for a singleton
        # shore its neighbor must touch every other vertex.
        for x,y,keep in twins:
            ok &= (((rows[:,x] | rowextra[j,x]) & keep) >= (rows[:,y] & keep))
        stats['symmetry'] += int(np.count_nonzero((~ok)&(m<=35)&(m+size-j>=14)&(deg.max(axis=1)<10)))
        terminal = np.flatnonzero(ok & ((j==size)|(m==35)))
        if len(terminal):
            assert np.all(m[terminal]>=14)
            a,b = exact_scores(K[terminal],t[terminal],deg[terminal])
            stats['terminal'] += len(terminal)
            bad = np.flatnonzero(3*a > 11950*b)
            if len(bad):
                k = int(bad[0]); word = int(code[terminal[k]])
                es = mask_edges(tree)+[p for v,p in enumerate(edges[:j]) if word & (1 << (j-1-v))]
                G = nx.Graph(es)
                val = Fraction(int(a[k]),int(b[k]))
                assert direct(G) == val and nx.diameter(G)>=3 and 14<=len(es)<=35
                G.remove_edge(*bridge)
                shores = [sorted(c) for c in nx.connected_components(G)]
                assert len(shores)==2
                return {'status':'VIOLATION','edges':es,'bridge':bridge,'shores':shores,'HT':[val.numerator,val.denominator]}
        run = np.flatnonzero(ok & (j<size) & (m<35))
        if not len(run):
            continue
        code,K,t,U,h,deg,rows = [a[run] for a in (code,K,t,U,h,deg,rows)]
        closed = bounded(K,t,U,h,deg,extra[j],edges,j,tree,code)
        stats['score_bounds'] += int(closed.sum())
        live = np.flatnonzero(~closed)
        if not len(live):
            continue
        code,K,t,U,h,deg,rows = [a[live] for a in (code,K,t,U,h,deg,rows)]
        u,v = edges[j]
        K1,t1 = change(K,t,(u,v),1)
        U0,h0 = change(U,h,(u,v),-1)
        deg1,rows1 = deg.copy(),rows.copy()
        deg1[:,[u,v]] += 1
        rows1[:,u] |= 1 << (10-v)
        rows1[:,v] |= 1 << (10-u)
        children = [np.concatenate(p) for p in [(2*code,2*code+1),(K,K1),(t,t1),(U0,U),(h0,h),(deg,deg1),(rows,rows1)]]
        for pos in range(0,len(children[0]),96):
            stack.append((j+1,*(a[pos:pos+96] for a in children)))
    return {'status':'CLOSED'}

# Integer safety: every top graph is a bridge join bounded by complete
# shores. Its tree count is at most 10^8 by the labeled-tree formula
# (also directly from the complete-shore grounded determinants). Every
# grounded entry is between zero and 10*tau by voltage and a tree path.
# Thus each rank-one numerator has magnitude at most 2*10^18, in int64.
check = sanity()
jobs = inventory()
answer = {'status':'PASS','summary':'All bridge-join intervals closed.','sanity':check,'total_jobs':len(jobs),'stats':stats}
for index,job in enumerate(jobs):
    result = search(job)
    if result['status'] == 'CLOSED':
        stats['jobs_closed'] += 1
        continue
    answer.update(result)
    answer['current_job'] = job
    if result['status']=='PARTIAL':
        answer['summary'] = 'Time guard reached. Pending prefixes of the current job and all listed later jobs remain to be closed.'
        answer['unstarted_jobs'] = jobs[index+1:]
        answer['encoding'] = 'Job = [chord count, tree mask, chord pool mask, bridge]. Mask bit k denotes the zero-based kth lexicographic pair. A pending item [j,words] fixes the first j ordered chords according to each j-bit word, most significant bit first.'
    else:
        answer['summary'] = 'Exact violating bridge join, cross-checked by absorbing-target linear solves.'
    break
answer['elapsed_seconds'] = round(time.monotonic()-start,3)
with open('result.json','w') as out:
    json.dump(answer,out)
