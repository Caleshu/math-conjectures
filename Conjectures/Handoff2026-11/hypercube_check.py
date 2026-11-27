"""Independent checks for the inscribed-squares conjecture (Sagols & Morales-Luna, arXiv:1009.3304).

1. eq_indep(n): equi-independence number of Q_n (largest independent set with equally many
   even- and odd-weight vertices).
2. square_free_ham(n): search for a Hamiltonian cycle of Q_n containing no two opposite
   edges of a 4-cycle. INFEASIBLE => conjecture verified for that n by exhaustive solver search.
"""
import sys, itertools
from ortools.sat.python import cp_model

def eq_indep(n, tlimit=120):
    N = 1 << n
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{v}") for v in range(N)]
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i)
            if u > v:
                m.AddBoolOr([x[u].Not(), x[v].Not()])
    even = [x[v] for v in range(N) if bin(v).count("1") % 2 == 0]
    odd = [x[v] for v in range(N) if bin(v).count("1") % 2 == 1]
    m.Add(sum(even) == sum(odd))
    # symmetry: vertex 0 in the set (Q_n is vertex-transitive)
    m.Add(x[0] == 1)
    m.Maximize(sum(x))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tlimit; s.parameters.num_workers = 2
    r = s.Solve(m)
    return s.StatusName(r), int(s.ObjectiveValue()), int(s.BestObjectiveBound())

def square_free_ham(n, tlimit=300):
    N = 1 << n
    m = cp_model.CpModel()
    arcs, edge = [], {}
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i)
            a = m.NewBoolVar(f"a{v}_{u}")
            arcs.append((v, u, a))
    arcvar = {(v, u): a for v, u, a in arcs}
    m.AddCircuit(arcs)
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i)
            if u > v:
                e = m.NewBoolVar(f"e{v}_{u}")
                m.Add(e == arcvar[(v, u)] + arcvar[(u, v)])
                edge[(v, u)] = e
    E = lambda a, b: edge[(min(a, b), max(a, b))]
    # every 4-cycle v, v^i, v^i^j, v^j : forbid both pairs of opposite edges
    cnt = 0
    for v in range(N):
        for i, j in itertools.combinations(range(n), 2):
            if v & (1 << i) or v & (1 << j):
                continue  # canonical corner: bits i,j zero
            a, b, c, d = v, v ^ (1 << i), v ^ (1 << i) ^ (1 << j), v ^ (1 << j)
            m.AddBoolOr([E(a, b).Not(), E(d, c).Not()])  # the two direction-i edges
            m.AddBoolOr([E(a, d).Not(), E(b, c).Not()])  # the two direction-j edges
            cnt += 1
    # symmetry breaking: edge 0--1 (direction 0) is used (cycle uses some edge at vertex 0; by symmetry of
    # coordinates we may assume the direction-0 edge at vertex 0 is used)
    m.Add(E(0, 1) == 1)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tlimit; s.parameters.num_workers = 2
    r = s.Solve(m)
    return s.StatusName(r), cnt

if __name__ == "__main__":
    mode, n = sys.argv[1], int(sys.argv[2])
    t = float(sys.argv[3]) if len(sys.argv) > 3 else 120
    if mode == "eq":
        print("alpha_eq(Q_%d)" % n, eq_indep(n, t), flush=True)
    else:
        print("square-free Ham cycle in Q_%d" % n, square_free_ham(n, t), flush=True)
