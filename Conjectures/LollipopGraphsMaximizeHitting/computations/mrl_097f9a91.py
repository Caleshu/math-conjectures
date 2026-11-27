# MathResearchLab experiment 097f9a91-b48c-4e5a-a2b9-9e0ef9d0aa8a
# Counterexample search over every small connected core with an attached rooted tree
# sha256(code) = 8c35f6516b134f9a9aee8edc100506c44e351f828f8b605089c6dc37bb20f57e
# parameters: {"orders": [11, 12, 13], "core_max": 7}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from fractions import Fraction
from math import lcm
import networkx as nx
import sympy as sp
params = json.load(open(os.environ['MRL_PARAMS']))
deadline = time.monotonic() + 95

def core_data(g):
    # Ground the last vertex. All callers label vertices 0,...,c-1.
    c = len(g)
    deg = [g.degree(i) for i in range(c)]
    lap = sp.diag(*deg) - sp.Matrix(nx.to_numpy_array(g, nodelist=range(c), dtype=int).tolist())
    green = sp.zeros(c)
    green[:c-1, :c-1] = lap[:c-1, :c-1].inv()
    raw = [[green[i,i] + green[j,j] - 2 * green[i,j] for j in range(c)] for i in range(c)]
    den = lcm(*(int(x.q) for row in raw for x in row))
    resistance = [[int(x * den) for x in row] for row in raw]
    score = [sum(d * x for d, x in zip(deg, row)) for row in resistance]
    w = sum(sum(row) for row in resistance) // 2
    return den, resistance, score, w

def dispersion(scores):
    n = len(scores)
    return sum((2*i + 1 - n) * x for i, x in enumerate(sorted(scores)))

def full_index(g):
    den, _, scores, w = core_data(g)
    return Fraction(2 * g.number_of_edges() * w + dispersion(scores), 2 * den)

def root_code(t, r, parent):
    return tuple(sorted(root_code(t, v, r) for v in t[r] if v != parent))

def tree_cases(size):
    trees = [nx.empty_graph(1)] if size == 1 else nx.nonisomorphic_trees(size)
    cases = []
    for t in trees:
        dist = dict(nx.all_pairs_shortest_path_length(t))
        tw = sum(sum(row.values()) for row in dist.values()) // 2
        ts = {i: sum(t.degree(j) * d for j, d in row.items()) for i, row in dist.items()}
        seen = set()
        for r in t:
            key = root_code(t, r, None)
            if key in seen:
                continue
            seen.add(key)
            others = [(d, ts[j]) for j, d in dist[r].items() if j != r]
            cases.append((tw, ts[r], sum(dist[r].values()), others, r, list(t.edges())))
    return cases

def joined_numerator(c, m, den, row, score, w, r, tree):
    # HT = m_total * sum_{i<j} R_ij + (1/2) sum_{i<j} |S_i-S_j|,
    # with S_i = sum_z degree(z)*R_iz. At a cut vertex resistances add.
    tw, root_score, depth_sum, others, _, _ = tree
    e = len(others)
    whole_w = w + e * sum(row) + den * (tw + (c - 1) * depth_sum)
    whole_s = [s + 2 * e * d + den * root_score for s, d in zip(score, row)]
    whole_s.extend(score[r] + den * (2 * m * depth + ts) for depth, ts in others)
    return 2 * (m + e) * whole_w + dispersion(whole_s)

def direct(g):
    n = len(g)
    h = sp.zeros(n)
    for j in range(n):
        keep = [v for v in range(n) if v != j]
        mat = sp.Matrix([[g.degree(u) if u == v else -int(g.has_edge(u,v)) for v in keep] for u in keep])
        vals = mat.inv() * sp.Matrix([g.degree(v) for v in keep])
        for u, val in zip(keep, vals):
            h[u,j] = val
    return sum(max(h[i,j], h[j,i]) for i in range(n) for j in range(i))

# Check the composition formula against direct first-step equations at every
# root of an asymmetric core, using every rooted four-vertex tree shape.
g = nx.complete_graph(4)
g.remove_edge(0, 1)
den, resist, score, w = core_data(g)
for r in g:
    for tc in tree_cases(4):
        tr, edges = tc[-2:]
        remap = {tr: r}
        remap.update({v: i for i, v in enumerate((v for v in range(4) if v != tr), start=4)})
        whole = g.copy()
        whole.add_edges_from((remap[u], remap[v]) for u, v in edges)
        num = joined_numerator(4, g.number_of_edges(), den, resist[r], score, w, r, tc)
        assert sp.Rational(num, 2 * den) == direct(whole)

def lollipop(n, k):
    g = nx.complete_graph(k)
    g.add_edges_from((i - 1, i) for i in range(k, n))
    return g

assert full_index(lollipop(6, 4)) == 224 and full_index(lollipop(6, 2)) == 223
cap = params['core_max']
assert 2 <= cap <= 7
atlas = [g for g in nx.graph_atlas_g() if 2 <= len(g) <= cap and nx.is_connected(g)]
cache = {}
tree_cache = {}
rows = []
for n in params['orders']:
    assert 2 <= n <= 14
    bench = [full_index(lollipop(n, k)) for k in range(2, n + 1)]
    target = max(bench)
    record = None
    witness = None
    checked = 0
    complete = True
    for idx, g in enumerate(atlas):
        if len(g) > n:
            continue
        if time.monotonic() >= deadline:
            complete = False
            break
        c = len(g)
        m = g.number_of_edges()
        size = n - c + 1
        if size not in tree_cache:
            tree_cache[size] = tree_cases(size)
        if idx not in cache:
            cache[idx] = core_data(g)
        den, resist, score, w = cache[idx]
        for r in g:
            if time.monotonic() >= deadline:
                complete = False
                break
            for tree in tree_cache[size]:
                num = joined_numerator(c, m, den, resist[r], score, w, r, tree)
                checked += 1
                if record is None or num * record.denominator > record.numerator * 2 * den:
                    record = Fraction(num, 2 * den)
                    witness = {'core_edges': list(g.edges()), 'core_root': r, 'tree_edges': tree[-1], 'tree_root': tree[-2]}
        if not complete:
            break
    rows.append({'n': n, 'class_exhausted': complete, 'rooted_combinations_checked': checked, 'best_seen': str(record) if record is not None else None, 'best_witness_identify_the_two_roots': witness, 'lollipop_max': str(target), 'lollipop_winning_k': [k for k, v in enumerate(bench, start=2) if v == target], 'strict_counterexample_found': record is not None and record > target})
    if not complete:
        break
with open('result.json', 'w') as f:
    json.dump({'summary': 'Exact comparisons over the indicated core and tree combinations. Only rows with class_exhausted=true certify a class maximum. Counts include duplicate unrooted graphs.', 'sanity': 'Composition checked against first-step equations on branched and unbranched attachments. Both order-six benchmarks checked.', 'rows': rows}, f)
