import sys
# Independent check from definitions; reads only edge list.
E=[l.split() for l in open(sys.argv[1]) if l.strip()]
n=len(E[0][0]); N=1<<n
assert all(len(a)==n==len(b) and set(a+b)<=set('01') for a,b in E)
edges=set()
for a,b in E:
    a,b=int(a,2),int(b,2); x=a^b
    assert x and x&(x-1)==0, "not a cube edge"
    edges.add((min(a,b),max(a,b)))
assert len(edges)==len(E)==N
adj={v:[] for v in range(N)}
for a,b in edges: adj[a].append(b); adj[b].append(a)
assert all(len(adj[v])==2 for v in range(N))
# walk the cycle
prev,cur,seen=None,0,{0}
for _ in range(N-1):
    nxt=adj[cur][0] if adj[cur][0]!=prev else adj[cur][1]
    assert nxt not in seen; seen.add(nxt); prev,cur=cur,nxt
assert 0 in adj[cur] and len(seen)==N
# squares: for every u, i != j, check edges {u,u^ei} and {u^ej, u^ej^ei}
sq=0
for u in range(N):
    for i in range(n):
        if u>>i&1: continue
        if (u,u|1<<i) not in edges: continue
        for j in range(n):
            if j==i: continue
            w=u^(1<<j)
            if (min(w,w|1<<i),max(w,w|1<<i)) in edges: sq+=1
print(f"n={n}: Hamiltonian cycle OK, inscribed squares found: {sq}")
