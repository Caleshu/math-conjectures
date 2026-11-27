# MathResearchLab experiment c2afdb92-7da6-4cbc-b874-9cb8a9ff38dd
# Exact lollipop maximizers and finite-size deviations
# sha256(code) = 4bf2aa827d0fe61d41c538181ff5724ca907e1fb2888757fdcf8539255f7ffac
# parameters: {"orders": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 50, 100, 250, 500, 1000]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from fractions import Fraction
from math import sqrt
import networkx as nx
import sympy as sp
params = json.load(open(os.environ['MRL_PARAMS']))
deadline = time.monotonic() + 95

def index(n, k):
    # Work in units of 1/k. Vertex 0 is the clique attachment.
    tail = n - k
    ordinary = k - 1
    to_ordinary = k * (k - 1) + 4 * tail
    between_ordinary = k * (k - 1) + 2 * tail
    total = ordinary * to_ordinary + ordinary * (ordinary - 1) // 2 * between_ordinary
    for j in range(1, tail + 1):
        outward = k * j * (k * (k - 1) + j)
        inward = k * j * (2 * tail - j)
        total += max(outward, inward)
        total += ordinary * max(outward + k * (k - 1), inward + to_ordinary)
    # At fixed s=i+j, both directions are proportional to j-i.
    for s in range(3, 2 * tail):
        lo = max(1, s - tail)
        hi = (s - 1) // 2
        sum_distances = (hi - lo + 1) * (s - lo - hi)
        total += k * sum_distances * max(k * (k - 1) + s, 2 * tail - s)
    return Fraction(total, k)

def direct(n, k):
    g = nx.complete_graph(k)
    g.add_edges_from((v - 1, v) for v in range(k, n))
    lap = sp.diag(*[g.degree(v) for v in range(n)]) - sp.Matrix(nx.to_numpy_array(g, nodelist=range(n), dtype=int).tolist())
    h = sp.zeros(n)
    for target in range(n):
        keep = [v for v in range(n) if v != target]
        values = lap.extract(keep, keep).inv() * sp.Matrix([g.degree(v) for v in keep])
        for v, value in zip(keep, values):
            h[v, target] = value
    return sum(max(h[u, v], h[v, u]) for u in range(n) for v in range(u))

for n in range(2, 9):
    for k in range(2, n + 1):
        assert sp.Rational(str(index(n, k))) == direct(n, k)
assert index(6, 4) == 224 and index(6, 2) == 223
rows = []
partial = None
xstar = (1 + sqrt(21)) / 10
for n in params['orders']:
    assert isinstance(n, int) and n >= 2
    values = {}
    for k in range(2, n + 1):
        if time.monotonic() >= deadline:
            partial = {'n': n, 'last_completed_k': k - 1}
            break
        values[k] = index(n, k)
    if partial is not None:
        break
    levels = sorted(set(values.values()), reverse=True)
    winners = [k for k, value in values.items() if value == levels[0]]
    rows.append({'n': n, 'max_ht': str(levels[0]), 'maximizing_k': winners, 'k_minus_n_xstar': [k - n * xstar for k in winners], 'gap_to_next_distinct_ht': str(levels[0] - levels[1]) if len(levels) > 1 else None})
with open('result.json', 'w') as f:
    json.dump({'summary': 'Exact scan of every clique size for each completed order.', 'sanity': 'All lollipops through order 8 matched independent absorbing-chain equations.', 'completed': rows, 'interrupted_order': partial}, f)
