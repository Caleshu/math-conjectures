# MathResearchLab experiment a4403c4a-7573-4bf7-82e9-4b3cf12ebdb3
# From-scratch CP-SAT search for a square-free Hamiltonian cycle in Q_8
# sha256(code) = 104e95fc2f80680503aff3ebaaf00b560cc1f607fc83d6f4ae4b5d0704d2ab71
# parameters: {"n_main": 8, "tl_main": 80.0}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from ortools.sat.python import cp_model
params = json.load(open(os.environ['MRL_PARAMS']))
n_main = params.get('n_main', 8)
tl_main = params.get('tl_main', 80.0)
T0 = time.time()

def build(n, squares=True):
    N = 1 << n
    mdl = cp_model.CpModel()
    arc = {}
    arcs = []
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i)
            lit = mdl.NewBoolVar(f'a{v}_{u}')
            arc[(v, u)] = lit
            arcs.append((v, u, lit))
    mdl.AddCircuit(arcs)
    for v in range(N):
        for i in range(n):
            u = v ^ (1 << i)
            if u > v: mdl.Add(arc[(v, u)] + arc[(u, v)] <= 1)
    # symmetry breaking: WLOG H uses edge {0,1} oriented 0->1 (vertex-transitivity + coordinate permutations + reversal)
    mdl.Add(arc[(0, 1)] == 1)
    nsq = 0
    if squares:
        for i in range(n):
            for j in range(i + 1, n):
                for v in range(N):
                    if v >> i & 1 or v >> j & 1: continue
                    a, b, c, d = v, v ^ (1 << i), v ^ (1 << i) ^ (1 << j), v ^ (1 << j)
                    # opposite pairs: (a,b)&(d,c) [dim i], (a,d)&(b,c) [dim j]
                    for (p, q), (r, s) in [((a, b), (d, c)), ((a, d), (b, c))]:
                        mdl.Add(arc[(p, q)] + arc[(q, p)] + arc[(r, s)] + arc[(s, r)] <= 1)
                        nsq += 1
    return mdl, arc, nsq

def extract(n, solver, arc):
    N = 1 << n
    succ = {}
    for (v, u), lit in arc.items():
        if solver.Value(lit): succ[v] = u
    cyc = [0]
    while len(cyc) <= N:
        nx = succ.get(cyc[-1])
        if nx is None or nx == 0: break
        cyc.append(nx)
    return cyc

def check(n, cyc):
    N = 1 << n
    ham = len(cyc) == N and len(set(cyc)) == N and all(0 <= v < N for v in cyc)
    E = set()
    for k in range(len(cyc)):
        a, b = cyc[k], cyc[(k + 1) % len(cyc)]
        if bin(a ^ b).count('1') != 1: ham = False
        E.add(frozenset((a, b)))
    # brute-force inscribed squares: pairs of H-edges in the same dimension whose endpoints are adjacent pairwise
    El = [tuple(e) for e in E]
    cnt = 0
    for x in range(len(El)):
        a, b = El[x]
        da = a ^ b
        for y in range(x + 1, len(El)):
            c, d = El[y]
            if c ^ d != da: continue
            # rims of a 4-cycle: a~c and b~d, or a~d and b~c, with matching translations
            for (p, q) in [(c, d), (d, c)]:
                t = a ^ p
                if bin(t).count('1') == 1 and (b ^ q) == t:
                    cnt += 1; break
    dims = [0] * n
    for (a, b) in El: dims[(a ^ b).bit_length() - 1] += 1
    return ham, cnt, dims

def run(n, squares, tl, seed=0):
    mdl, arc, nsq = build(n, squares)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_workers = 8
    s.parameters.random_seed = seed
    st = s.Solve(mdl)
    r = {'n': n, 'squares': squares, 'n_square_constraints': nsq, 'status': s.StatusName(st), 'wall': round(s.WallTime(), 2)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        cyc = extract(n, s, arc)
        ham, cnt, dims = check(n, cyc)
        r.update(hamiltonian=ham, inscribed_squares=cnt, edges_per_dim=dims)
        if n >= 6: r['cycle'] = cyc
    return r

out = {}
out['sanity_Q4_no_squares'] = run(4, False, 10.0)
# checker sanity: reflected Gray code of Q_4 must have many inscribed squares
g = [k ^ (k >> 1) for k in range(16)]
h, c, d = check(4, g)
out['sanity_gray_Q4'] = {'hamiltonian': h, 'inscribed_squares': c}
out['sanity_Q5_squarefree'] = run(5, True, 15.0)
rem = 115 - (time.time() - T0)
tl = max(5.0, min(tl_main, rem - 8))
out['main'] = run(n_main, True, tl)
m = out['main']
sanity_ok = (out['sanity_Q4_no_squares']['status'] in ('OPTIMAL', 'FEASIBLE') and out['sanity_Q4_no_squares'].get('hamiltonian') is True
             and out['sanity_gray_Q4']['hamiltonian'] and out['sanity_gray_Q4']['inscribed_squares'] > 0
             and out['sanity_Q5_squarefree']['status'] == 'INFEASIBLE')
out['sanity_passed'] = sanity_ok
found = m['status'] in ('OPTIMAL', 'FEASIBLE') and m.get('hamiltonian') and m.get('inscribed_squares') == 0
out['squarefree_found_from_scratch'] = bool(found)
out['summary'] = (f"sanity_passed={sanity_ok} (Q4 unconstrained: {out['sanity_Q4_no_squares']['status']}; Gray Q4 squares={out['sanity_gray_Q4']['inscribed_squares']}; Q5 square-free: {out['sanity_Q5_squarefree']['status']}). "
                  f"Q_{n_main} square-free search: {m['status']} in {m['wall']}s" + (f", verified hamiltonian={m.get('hamiltonian')}, inscribed_squares={m.get('inscribed_squares')}, edges_per_dim={m.get('edges_per_dim')}" if 'hamiltonian' in m else ' (no cycle found; UNKNOWN is not evidence of nonexistence)'))
out['total_time'] = round(time.time() - T0, 1)
json.dump(out, open('result.json', 'w'), indent=1)
