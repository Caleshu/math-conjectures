# MathResearchLab experiment 487532a4-d7d2-4b84-ad57-374f7b709ca3
# Exact counterexample feasibility at orders nine and ten
# sha256(code) = 26838668ae7fcc952ebeed9819941eec9e3ed7b59ec4645c8ba2b8d1e4625412
# parameters: {"orders": [9, 10], "seconds_per_order": 30}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from itertools import combinations
import networkx as nx
from ortools.sat.python import cp_model

params = json.load(open(os.environ["MRL_PARAMS"]))
orders = params['orders']
assert orders and len(set(orders)) == len(orders) and set(orders) <= {9, 10}
seconds = float(params['seconds_per_order'])
assert 0 < seconds <= 35
started = time.monotonic()


def solve(n, k, limit, fixed=None):
    model = cp_model.CpModel()
    vertices = range(n)
    pairs = list(combinations(vertices, 2))
    edge = {p: model.new_bool_var(f'e{p}') for p in pairs}
    tri = {}
    incident = {p: [] for p in pairs}
    for triple in combinations(vertices, 3):
        t = model.new_bool_var(f't{triple}')
        tri[triple] = t
        tri_edges = list(combinations(triple, 2))
        for p in tri_edges:
            model.add(t <= edge[p])
            incident[p].append(t)
        model.add(t >= sum(edge[p] for p in tri_edges) - 2)
    for four in combinations(vertices, 4):
        model.add(sum(edge[p] for p in combinations(four, 2)) <= 5)
    maximal_edge = {}
    for p in pairs:
        m = model.new_bool_var(f'm{p}')
        maximal_edge[p] = m
        model.add(m <= edge[p])
        for t in incident[p]:
            model.add(m + t <= 1)
        model.add(m >= edge[p] - sum(incident[p]))
    for subset in combinations(vertices, k):
        model.add_bool_or([maximal_edge[p] for p in combinations(subset, 2)] +
                          [tri[t] for t in combinations(subset, 3)])

    model.add(tri[0, 1, 2] == 1)
    # Permute within the chosen triangle and within its complement independently.
    degrees = [sum(edge[tuple(sorted((u, v)))] for u in vertices if u != v) for v in vertices]
    for group in (range(3), range(3, n)):
        for u, v in zip(group, group[1:]):
            model.add(degrees[u] >= degrees[v])
    if fixed is not None:
        for p in pairs:
            model.add(edge[p] == int(p in fixed))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = limit
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 151
    status = solver.solve(model)
    name = solver.status_name(status)
    row = {'n': n, 'subset_size': k, 'status': name, 'solver_seconds': solver.wall_time}
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        g = nx.Graph()
        g.add_nodes_from(vertices)
        g.add_edges_from(p for p in pairs if solver.value(edge[p]))
        blocks = [set(c) for c in nx.find_cliques(g) if len(c) >= 2]
        assert max(map(len, blocks)) == 3
        for size in range(n, -1, -1):
            witness = next((s for s in combinations(vertices, size)
                            if all(not block.issubset(s) for block in blocks)), None)
            if witness is not None:
                break
        assert witness is not None and len(witness) < k
        row.update(edges=sorted(g.edges()), b=len(witness), largest_admissible_set=witness,
                   minimum_transversal=sorted(set(vertices).difference(witness)))
    return row


# K3 plus three disjoint edges has b = 2 + 3 = 5. Both fixed tests use
# the full encoding, including the triangle anchor and degree ordering.
fixed = {(0, 1), (0, 2), (1, 2), (3, 4), (5, 6), (7, 8)}
yes = solve(9, 6, 3, fixed)
no = solve(9, 5, 3, fixed)
sanity_ok = yes['status'] in ('OPTIMAL', 'FEASIBLE') and yes.get('b') == 5 and no['status'] == 'INFEASIBLE'
rows = []
if sanity_ok:
    for n in orders:
        remaining = 95 - (time.monotonic() - started)
        if remaining < 1:
            break
        rows.append(solve(n, 4, min(seconds, remaining)))
verified = [r['n'] for r in rows if r['status'] == 'INFEASIBLE']
violations = [r['n'] for r in rows if r['status'] in ('OPTIMAL', 'FEASIBLE')]
unresolved = sorted(set(orders) - set(verified) - set(violations))
result = {'summary': f'Sanity passed: {sanity_ok}. Orders verified by infeasibility: {verified}. Orders with checked counterexamples: {violations}. Unresolved orders: {unresolved}.',
          'sanity': [yes, no], 'sanity_ok': sanity_ok, 'searches': rows, 'unresolved': unresolved}
with open('result.json', 'w') as output:
    json.dump(result, output)
