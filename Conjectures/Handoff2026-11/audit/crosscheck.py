"""(a) alpha_eq(Q_n) via an ILP solved by CBC (independent of CP-SAT and of eqindep.c).
(b) Size of the paper's auxiliary graph Q'_n (Theorem 5.3 construction), to compare with their Table 1.
"""
import sys

def alpha_eq_ilp(n):
    """Decide by SAT (PySAT / CaDiCaL) whether a balanced independent set with k vertices per side
    exists; return the largest k found. Independent of CP-SAT and of eqindep.c."""
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    from pysat.solvers import Solver
    V = 1 << n
    best = 0
    for k in range(1, V // 4 + 2):
        pool = IDPool(); x = lambda v: pool.id(("x", v))
        cl = [[-x(v), -x(v ^ (1 << i))] for v in range(V) for i in range(n) if (v ^ (1 << i)) > v]
        ev = [x(v) for v in range(V) if bin(v).count("1") % 2 == 0]
        od = [x(v) for v in range(V) if bin(v).count("1") % 2 == 1]
        for side in (ev, od):
            cl += CardEnc.atleast(lits=side, bound=k, vpool=pool, encoding=EncType.seqcounter).clauses
        with Solver(name="cadical195", bootstrap_with=cl) as s:
            if s.solve(): best = k
            else: return ("UNSAT at k=%d per side" % k, 2 * best)
    return ("no UNSAT found", 2 * best)

def aux_graph_size(n):
    """Q'_n: vertices = non-adjacent pairs (v0, v1), v0 even, v1 odd. Pairs p, p' adjacent iff
    v0 = v0', or v1 = v1', or v0 ~ v1', or v1 ~ v0'  (~ = adjacent in Q_n)."""
    V = 1 << n
    ev = [v for v in range(V) if bin(v).count("1") % 2 == 0]
    od = [v for v in range(V) if bin(v).count("1") % 2 == 1]
    adj = lambda a, b: bin(a ^ b).count("1") == 1
    P = [(a, b) for a in ev for b in od if not adj(a, b)]
    m = len(P)
    # count NON-adjacent unordered pairs of P, then subtract from C(m,2)
    nonadj = 0
    for i in range(m):
        a, b = P[i]
        for j in range(i + 1, m):
            c, d = P[j]
            if a != c and b != d and not adj(a, d) and not adj(b, c):
                nonadj += 1
    return m, m * (m - 1) // 2 - nonadj

if __name__ == "__main__":
    for n in range(3, 7):
        print(f"n={n}: SAT alpha_eq(Q_n) =", alpha_eq_ilp(n), flush=True)
    for n in range(3, int(sys.argv[1]) + 1 if len(sys.argv) > 1 else 7):
        print(f"n={n}: |V(Q'_n)|, |E(Q'_n)| =", aux_graph_size(n), flush=True)
