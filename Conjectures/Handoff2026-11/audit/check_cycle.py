"""Standalone check of a claimed square-free Hamiltonian cycle of Q_n (no shared code with the search).
Input: a text file with one edge per line, two n-bit binary strings.
Checks: (1) every edge is a hypercube edge; (2) every vertex of {0,1}^n has degree exactly 2;
(3) the edges form ONE cycle through all 2^n vertices; (4) no two edges are opposite edges of a 4-cycle,
tested by brute force over ALL pairs of edges: edges {a, a+e_i} and {b, b+e_i} (same direction i) are
opposite in a 4-cycle iff their lower endpoints a, b (bit i = 0) differ in exactly one coordinate.
Also writes the cycle as a vertex sequence and its transition sequence."""
import sys
from itertools import combinations
path = sys.argv[1]
E = [tuple(l.split()) for l in open(path) if l.strip()]
n = len(E[0][0]); N = 1 << n
E = [(int(a, 2), int(b, 2)) for a, b in E]
assert all(bin(a ^ b).count("1") == 1 for a, b in E), "non-edge present"
assert len(set(frozenset(e) for e in E)) == len(E) == N, "need 2^n distinct edges"
deg = [0] * N; adj = [[] for _ in range(N)]
for a, b in E: deg[a] += 1; deg[b] += 1; adj[a].append(b); adj[b].append(a)
assert all(d == 2 for d in deg), "degree != 2 somewhere"
seq = [0, adj[0][0]]
while len(seq) < N:
    x, y = seq[-1], seq[-2]
    seq.append(adj[x][0] if adj[x][0] != y else adj[x][1])
assert len(set(seq)) == N and seq[0] in adj[seq[-1]], "not a single Hamiltonian cycle"
bad = 0
for (a, b), (c, d) in combinations(E, 2):
    if a ^ b != c ^ d: continue
    i = a ^ b
    lo1, lo2 = (a if not a & i else b), (c if not c & i else d)
    if bin(lo1 ^ lo2).count("1") == 1: bad += 1
print(f"Q_{n}: single Hamiltonian cycle through all {N} vertices: OK; opposite-edge pairs (inscribed squares): {bad}")
trans = [(seq[(k + 1) % N] ^ seq[k]).bit_length() - 1 for k in range(N)]
with open(path.replace(".txt", "_sequence.txt"), "w") as f:
    f.write("vertex sequence (binary, cyclic):\n" + " ".join(format(v, f"0{n}b") for v in seq) + "\n")
    f.write("transition sequence (coordinate flipped at each step, 0 = least significant bit):\n" + " ".join(map(str, trans)) + "\n")
print("direction counts:", [trans.count(i) for i in range(n)])
