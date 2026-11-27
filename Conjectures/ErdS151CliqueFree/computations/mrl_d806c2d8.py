# MathResearchLab experiment d806c2d8-680a-45ea-b37b-5f87699fc38c
# Exact extremal values through seven vertices
# sha256(code) = 6bae42a14137aa9e73b2ba0d7b99c0b99d52b85ea9e23b3d29afeae349dd963c
# parameters: {"n_max": 7}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from collections import Counter
from itertools import combinations
import networkx as nx

params = json.load(open(os.environ["MRL_PARAMS"]))
n_max = params['n_max']
assert 0 <= n_max <= 7


def describe(g):
    return {'n': len(g), 'edges': sorted([min(u, v), max(u, v)] for u, v in g.edges())}


def largest_avoiding(n, forbidden):
    # A zero mask is never supplied as a forbidden set.
    for k in range(n, -1, -1):
        for vertices in combinations(range(n), k):
            mask = sum(1 << v for v in vertices)
            if all(mask & block != block for block in forbidden):
                return list(vertices)
    raise AssertionError('The empty set should be admissible')


def clique_blocks(g):
    return [sum(1 << v for v in c) for c in nx.find_cliques(g) if len(c) >= 2]


def check_local_description(g, blocks):
    # Independent construction for K4-free inputs. A triangle is maximal,
    # and an edge is maximal exactly when it has no common neighbor.
    local = set()
    for u, v in g.edges():
        common = set(g[u]).intersection(g[v])
        edge = (1 << u) | (1 << v)
        if common:
            local.update(edge | (1 << w) for w in common)
        else:
            local.add(edge)
    assert local == set(blocks)


def retain_min(row, field, g, vertices):
    entry = row[field]
    if entry is None or len(vertices) < entry['value']:
        row[field] = {'value': len(vertices), 'graph': describe(g),
                      'largest_admissible_set': vertices, 'number_of_minimizers_up_to_isomorphism': 1}
    elif len(vertices) == entry['value']:
        entry['number_of_minimizers_up_to_isomorphism'] += 1


sanity_graph = nx.disjoint_union(nx.complete_graph(3), nx.empty_graph(1))
assert len(largest_avoiding(4, clique_blocks(sanity_graph))) == 3
assert len(largest_avoiding(5, clique_blocks(nx.cycle_graph(5)))) == 2
assert largest_avoiding(0, []) == []

rows = [{'n': n, 'H': None, 'min_b': None, 'min_b_with_triangle': None,
         'b_histogram': Counter(), 'b_histogram_with_triangle': Counter()} for n in range(n_max + 1)]
atlas_counts = [0] * (n_max + 1)
for g in nx.graph_atlas_g():
    n = len(g)
    if n > n_max:
        continue
    atlas_counts[n] += 1
    assert set(g) == set(range(n))
    blocks = clique_blocks(g)
    if any(block.bit_count() >= 4 for block in blocks):
        continue
    check_local_description(g, blocks)
    vertices = largest_avoiding(n, blocks)
    row = rows[n]
    row['b_histogram'][len(vertices)] += 1
    retain_min(row, 'min_b', g, vertices)
    if any(block.bit_count() == 3 for block in blocks):
        row['b_histogram_with_triangle'][len(vertices)] += 1
        retain_min(row, 'min_b_with_triangle', g, vertices)
    else:
        # Complement cliques provide a separate computation of alpha.
        independent = max(nx.find_cliques(nx.complement(g)), key=len, default=[])
        assert len(independent) == len(vertices)
        retain_min(row, 'H', g, sorted(independent))

assert atlas_counts == [1, 1, 2, 4, 11, 34, 156, 1044][:n_max + 1]
for row in rows:
    row['gap'] = row['min_b']['value'] - row['H']['value']
violations = [row['n'] for row in rows if row['gap'] < 0]
result = {'summary': f'Exhausted graph-atlas isomorphism classes through order {n_max}. Orders with a violation: {violations}.',
          'atlas_counts_before_filtering': atlas_counts, 'rows': rows,
          'sanity_checks': 'Passed null graph, triangle plus isolate, five-cycle, atlas counts, and independent clique-block checks.'}
with open('result.json', 'w') as output:
    json.dump(result, output)
