"""Enumerate all square-free subgraphs of Q_3 with max degree <= 2 and record
m = #edges, c = #vertices of degree 2 (corners). Report max(m - c) and the feasible (c, m) pairs."""
import itertools
n = 3; V = 8
edges = [(v, v ^ 1 << i) for v in range(V) for i in range(n) if v ^ 1 << i > v]
idx = {e: k for k, e in enumerate(edges)}
E = lambda a, b: idx[(min(a, b), max(a, b))]
squares = []
for v in range(V):
    for i, j in itertools.combinations(range(n), 2):
        if v >> i & 1 or v >> j & 1: continue
        a, b, c, d = v, v ^ 1 << i, v ^ 1 << i ^ 1 << j, v ^ 1 << j
        squares.append(((E(a, b), E(d, c)), (E(a, d), E(b, c))))
feas = {}
for mask in range(1 << 12):
    deg = [0] * V
    for k, (a, b) in enumerate(edges):
        if mask >> k & 1: deg[a] += 1; deg[b] += 1
    if max(deg) > 2: continue
    if any((mask >> p & 1) and (mask >> q & 1) for pair in squares for p, q in pair): continue
    m = bin(mask).count("1"); c = deg.count(2)
    feas[(c, m)] = feas.get((c, m), 0) + 1
print("feasible (c, m): count", sorted(feas.items()))
print("max m - c =", max(m - c for c, m in feas))
