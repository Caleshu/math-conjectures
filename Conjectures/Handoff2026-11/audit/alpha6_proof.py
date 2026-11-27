"""DRUP-certified upper bound alpha_eq(Q_6) <= 20: no independent set in Q_6 with >= 11 even and
>= 11 odd vertices. Cardinality via sequential counter (auxiliary variables; checker handles any CNF)."""
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver
n = 6; V = 1 << n; k = 11
pool = IDPool(); x = lambda v: pool.id(("x", v))
for v in range(V): x(v)
cl = [[-x(v), -x(v ^ (1 << i))] for v in range(V) for i in range(n) if (v ^ (1 << i)) > v]
for par in (0, 1):
    cl += CardEnc.atleast(lits=[x(v) for v in range(V) if bin(v).count("1") % 2 == par], bound=k,
                          vpool=pool, encoding=EncType.seqcounter).clauses
nv = max(abs(l) for c in cl for l in c)
open("alpha6_k11.cnf", "w").write(f"p cnf {nv} {len(cl)}\n" + "".join(" ".join(map(str, c)) + " 0\n" for c in cl))
with Solver(name="glucose4", bootstrap_with=cl, with_proof=True) as s:
    r = s.solve(); print("SAT" if r else "UNSAT")
    if not r: open("alpha6_k11.drup", "w").write("\n".join(s.get_proof()) + "\n"); print("proof lines", len(s.get_proof()))
