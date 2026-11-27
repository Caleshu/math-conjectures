# Independent re-check of every egg constraint (written separately from the search code).
# Egg: connected C such that no W ⊇ C with |W|<=10 and boundary(W)<=30 exists, except W a closed neighborhood.
import sys, itertools
N=64
adj=[{v^(1<<k) for k in range(6)} for v in range(N)]
closed={frozenset(adj[v]|{v}) for v in range(N)}
def boundary(W): return sum(len(adj[u]-W) for u in W)
def is_conn(S):
    S=set(S); start=next(iter(S)); seen={start}; todo=[start]
    while todo:
        u=todo.pop()
        for w in adj[u]&S:
            if w not in seen: seen.add(w); todo.append(w)
    return seen==S
def dist_to(C):
    d={v:0 for v in C}; frontier=list(C)
    while frontier:
        nf=[]
        for u in frontier:
            for w in adj[u]:
                if w not in d: d[w]=d[u]+1; nf.append(w)
        frontier=nf
    return d
def egg(C):
    C=frozenset(C)
    if not is_conn(C): return False
    if len(C)>10: return True
    d=dist_to(C); room=10-len(C)
    cand=[v for v in range(N) if 0<d[v]<=room]   # a connected superset only uses vertices within distance `room`
    for r in range(room+1):
        for extra in itertools.combinations(cand,r):
            W=C|frozenset(extra)
            if boundary(W)<=30 and W not in closed: return False
    return True
eggs=[frozenset(map(int,l.split())) for l in open(sys.argv[1]) if l.strip()]
bad=[e for e in eggs if not egg(e)]
print(f"{len(eggs)} egg constraints checked; failures: {len(bad)}")
from collections import Counter; print("sizes:", sorted(Counter(len(e) for e in eggs).items()))
