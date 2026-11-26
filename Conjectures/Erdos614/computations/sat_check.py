"""
Independent SAT cross-check of g(n,m) = C(m-1,2) + n-m+1 (equivalently f(n,k) = (n-k-1)(n+k-2)/2,
m = k+2) for cases outside exhaustive enumeration.

Variables: one per possible edge of the complement H. Constraints: for every m-set S some vertex
v in S has at most one H-neighbour in S; e(H) >= target. Expect SAT at target = g and UNSAT at
target = g + 1.

Usage: python sat_check.py n k        (needs `python-sat`)
"""
import sys, itertools, time
from math import comb
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153


def solve(n, m, target):
    pool = IDPool()
    x = {}
    for u, v in itertools.combinations(range(n), 2):
        x[(u, v)] = x[(v, u)] = pool.id(("x", u, v))
    edges = [x[(u, v)] for u, v in itertools.combinations(range(n), 2)]
    cnf = CNF()
    for S in itertools.combinations(range(n), m):
        ys = []
        for v in S:
            y = pool.id(("y", S, v))
            ys.append(y)
            nb = [x[(v, w)] for w in S if w != v]
            for a, b in itertools.combinations(nb, 2):      # y -> at most one of nb
                cnf.append([-y, -a, -b])
        cnf.append(ys)
    card = CardEnc.atleast(lits=edges, bound=target, vpool=pool, encoding=EncType.seqcounter)
    cnf.extend(card.clauses)
    with Cadical153(bootstrap_with=cnf.clauses) as s:
        # symmetry breaking (sound): vertex 0 has maximum degree is NOT used; keep plain.
        return s.solve()


if __name__ == "__main__":
    n, k = int(sys.argv[1]), int(sys.argv[2])
    m = k + 2
    g = comb(m - 1, 2) + n - m + 1
    f = (n - k - 1) * (n + k - 2) // 2
    print(f"n={n} k={k} m={m}: formula g={g} (f={f})")
    for t in (g, g + 1):
        t0 = time.time()
        r = solve(n, m, t)
        print(f"  e(H) >= {t}: {'SAT' if r else 'UNSAT'}  ({time.time() - t0:.1f}s)")
