"""Square-free 2-factors / Hamiltonian cycles of Q_n by SAT, with lazily added connectivity cuts.

Variables: x_e for each edge e of Q_n.
Clauses (all elementary, no auxiliary variables):
  degree exactly 2 at every vertex v (degree n):
      at most 2:  (-a v -b v -c) for every 3 edges a,b,c at v
      at least 2: for every edge a at v, OR of the other n-1 edges at v
  square-free: for every 4-cycle (a,b,c,d): (-ab v -cd) and (-bc v -da)
  [Hamiltonian mode] cut clauses: whenever a solution splits into several cycles, for one cycle with
      vertex set C add the clause OR_{e in delta(C)} x_e  (every Hamiltonian cycle crosses every cut).
All clauses are valid for every square-free Hamiltonian cycle, so UNSAT of the final CNF proves that none
exists. No symmetry breaking is used, so the CNF can be checked as is.

usage: python3 sqfree_sat.py n [ham|2factor] [cnf_out]
"""
import sys, itertools, time
from pysat.solvers import Solver

n = int(sys.argv[1]); mode = sys.argv[2] if len(sys.argv) > 2 else "ham"
out = sys.argv[3] if len(sys.argv) > 3 else None
V = 1 << n
eid = {}
for v in range(V):
    for i in range(n):
        u = v ^ (1 << i)
        if u > v: eid[(v, u)] = len(eid) + 1
E = lambda a, b: eid[(min(a, b), max(a, b))]
inc = {v: [E(v, v ^ (1 << i)) for i in range(n)] for v in range(V)}
clauses = []
for v in range(V):
    for a, b, c in itertools.combinations(inc[v], 3):
        clauses.append([-a, -b, -c])
    for a in inc[v]:
        clauses.append([e for e in inc[v] if e != a])
nsq = 0
for v in range(V):
    for i, j in itertools.combinations(range(n), 2):
        if v >> i & 1 or v >> j & 1: continue
        a, b, c, d = v, v ^ 1 << i, v ^ 1 << i ^ 1 << j, v ^ 1 << j
        clauses.append([-E(a, b), -E(d, c)]); clauses.append([-E(a, d), -E(b, c)]); nsq += 1
print(f"Q_{n}: {len(eid)} edge vars, {nsq} squares, {len(clauses)} base clauses, mode={mode}", flush=True)

def components(model):
    on = {e for e in model if e > 0}
    adj = {v: [] for v in range(V)}
    for (a, b), e in eid.items():
        if e in on: adj[a].append(b); adj[b].append(a)
    seen, comps = set(), []
    for s in range(V):
        if s in seen: continue
        comp, stack = [], [s]; seen.add(s)
        while stack:
            x = stack.pop(); comp.append(x)
            for y in adj[x]:
                if y not in seen: seen.add(y); stack.append(y)
        comps.append(comp)
    return comps, on

t0 = time.time(); cuts = 0
with Solver(name="cadical195", bootstrap_with=clauses) as s:
    while True:
        if not s.solve():
            print(f"UNSAT after {cuts} cuts, {time.time()-t0:.1f}s", flush=True); result = None; break
        comps, on = components(s.get_model())
        if mode == "2factor" or len(comps) == 1:
            result = (comps, on); print(f"SAT: {len(comps)} cycle(s), lengths {sorted(len(c) for c in comps)}, after {cuts} cuts, {time.time()-t0:.1f}s", flush=True); break
        for comp in comps:                         # add a cut for every cycle found
            C = set(comp)
            cut = [e for (a, b), e in eid.items() if (a in C) != (b in C)]
            s.add_clause(cut); clauses.append(cut); cuts += 1
        if cuts % 200 < len(comps): print(f"  {cuts} cuts, last solution had {len(comps)} cycles, {time.time()-t0:.0f}s", flush=True)

if out:
    with open(out, "w") as f:
        f.write(f"p cnf {len(eid)} {len(clauses)}\n")
        for c in clauses: f.write(" ".join(map(str, c)) + " 0\n")
    print("wrote", out)
if result:
    comps, on = result
    # independent re-check of the solution: degrees, squares, and the counting identity
    deg = {v: 0 for v in range(V)}
    for (a, b), e in eid.items():
        if e in on: deg[a] += 1; deg[b] += 1
    assert all(d == 2 for d in deg.values())
    cnt = {0: 0, 1: 0, 2: 0}
    for v in range(V):
        for i, j in itertools.combinations(range(n), 2):
            if v >> i & 1 or v >> j & 1: continue
            a, b, c, d = v, v ^ 1 << i, v ^ 1 << i ^ 1 << j, v ^ 1 << j
            es = [E(a, b) in on, E(b, c) in on, E(c, d) in on, E(d, a) in on]
            assert not (es[0] and es[2]) and not (es[1] and es[3])
            cnt[sum(es)] += 1
    print("re-check OK. squares by #H-edges:", cnt)
    with open(f"solution_Q{n}_{mode}.txt", "w") as f:
        f.write("\n".join(f"{a:0{n}b} {b:0{n}b}" for (a, b), e in sorted(eid.items()) if e in on) + "\n")
