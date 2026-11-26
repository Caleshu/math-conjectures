# Emits graph6 for the two constructions (complement form H), to be checked by ./sizes.
import sys
def g6(n, E):
    bits = []
    S = set(map(lambda e: (min(e), max(e)), E))
    for j in range(1, n):
        for i in range(j): bits.append(1 if (i, j) in S else 0)
    while len(bits) % 6: bits.append(0)
    return chr(n + 63) + "".join(chr(63 + int("".join(map(str, bits[i:i+6])), 2)) for i in range(0, len(bits), 6))
def clique_pendants(n, m):        # K_{m-1} on 0..m-2, every other vertex pendant to vertex 0
    E = [(i, j) for j in range(m - 1) for i in range(j)] + [(0, v) for v in range(m - 1, n)]
    return E
def clique_cycle(m):              # K_{m-1} plus a cycle of length m-1 through clique vertex 0; n = 2m-3
    E = [(i, j) for j in range(m - 1) for i in range(j)]
    cyc = [0] + list(range(m - 1, 2 * m - 3))
    E += [(cyc[i], cyc[(i + 1) % len(cyc)]) for i in range(len(cyc))]
    return E
kind, n, m = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
E = clique_pendants(n, m) if kind == "pend" else clique_cycle(m)
print(g6(n, E), len(E), file=sys.stderr); print(g6(n, E))
