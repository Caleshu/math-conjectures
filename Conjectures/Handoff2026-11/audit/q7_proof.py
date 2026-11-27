"""Q_7 square-free 2-factor CNF with sound symmetry breaking, solved with proof logging.
Symmetry breaking (justified in the write-up): edges {0,1}, {0,2}, {1,5} are in H
(vertex 0's two H-directions are mapped to coordinates 0 and 1 by a coordinate permutation; the other
H-direction at vertex 1 = e_0 cannot be 1 (that would create a square) and is mapped to coordinate 2)."""
import itertools, sys, time
from pysat.solvers import Solver
n = 7; V = 1 << n
eid = {}
for v in range(V):
    for i in range(n):
        u = v ^ (1 << i)
        if u > v: eid[(v, u)] = len(eid) + 1
E = lambda a, b: eid[(min(a, b), max(a, b))]
inc = {v: [E(v, v ^ (1 << i)) for i in range(n)] for v in range(V)}
cl = []
for v in range(V):
    cl += [[-a, -b, -c] for a, b, c in itertools.combinations(inc[v], 3)]
    cl += [[e for e in inc[v] if e != a] for a in inc[v]]
for v in range(V):
    for i, j in itertools.combinations(range(n), 2):
        if v >> i & 1 or v >> j & 1: continue
        a, b, c, d = v, v ^ 1 << i, v ^ 1 << i ^ 1 << j, v ^ 1 << j
        cl += [[-E(a, b), -E(d, c)], [-E(a, d), -E(b, c)]]
sym = [[E(0, 1)], [E(0, 2)], [E(1, 5)]]
name = sys.argv[1] if len(sys.argv) > 1 else "glucose4"
use_sym = "nosym" not in sys.argv
F = cl + (sym if use_sym else [])
with open("q7_2factor%s.cnf" % ("_sym" if use_sym else ""), "w") as f:
    f.write(f"p cnf {len(eid)} {len(F)}\n" + "".join(" ".join(map(str, c)) + " 0\n" for c in F))
t = time.time()
with Solver(name=name, bootstrap_with=F, with_proof=True) as s:
    r = s.solve(); dt = time.time() - t
    print(name, "sym" if use_sym else "nosym", "SAT" if r else "UNSAT", f"{dt:.1f}s", flush=True)
    if not r:
        p = s.get_proof()
        with open(f"q7_{name}.drup", "w") as f: f.write("\n".join(p) + "\n")
        print("proof lines:", len(p))
