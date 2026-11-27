# MathResearchLab experiment 43c059a3-b187-4788-9f3b-5d810b476173
# A six-to-five Hall certificate and an exhaustive mixed-length extension
# sha256(code) = 88b601d8a15fe051ea29b427c47e121a415d1f8e6e00d450a2f96fc786b25a7f
# parameters: {"sizes": [7, 8], "seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import itertools as it
import math
import signal
import sys
from collections import Counter
from functools import cache
import networkx as nx


def partitions(n, cap=None):
    if n == 0:
        yield ()
        return
    for first in range(min(n, cap if cap is not None else n), 0, -1):
        for tail in partitions(n - first, first):
            yield (first,) + tail


def axis_labels(shape):
    d = len(shape)
    shifted = tuple(v + d - 1 - i for i, v in enumerate(shape))
    for order in it.permutations(range(d)):
        word = tuple(shifted[i] for i in order)
        margin = tuple(v - (d - 1 - i) for i, v in enumerate(word))
        if min(margin) >= 0:
            inversions = sum(a > b for a, b in it.combinations(order, 2))
            yield word, margin, inversions % 2


def tables(cells, margins):
    left = [list(m) for m in margins]
    data = [0] * len(cells)
    last = {(a, c[a]): j for j, c in enumerate(cells) for a in range(3)}

    def visit(j):
        if j == len(cells):
            yield tuple(data)
            return
        c = cells[j]
        amounts = [left[a][c[a]] for a in range(3)]
        upper = min(amounts)
        lower = max((amounts[a] for a in range(3) if last[a, c[a]] == j), default=0)
        for v in range(lower, upper + 1):
            data[j] = v
            for a in range(3):
                left[a][c[a]] -= v
            yield from visit(j + 1)
            for a in range(3):
                left[a][c[a]] += v
    yield from visit(0)


def transfer_targets(x, pairs, quantity, prescribed):
    # Each pair is a donor and its unique receiver, in donor cell order.
    active = [(s, t) for s, t in pairs if x[s]]
    suffix = [0] * (len(active) + 1)
    for i in reversed(range(len(active))):
        suffix[i] = suffix[i + 1] + x[active[i][0]]
    y = list(x)

    def visit(i, need):
        if need == 0:
            yield tuple(y)
            return
        if suffix[i] < need:
            return
        s, t = active[i]
        hi = min(need, x[s])
        lo = hi if prescribed else max(0, need - suffix[i + 1])
        for amount in range(hi, lo - 1, -1):
            y[s] -= amount
            y[t] += amount
            yield from visit(i + 1, need - amount)
            y[s] += amount
            y[t] -= amount
    yield from visit(0, quantity)


def build_graph(shapes, prescribed):
    dims = tuple(map(len, shapes))
    cells = list(it.product(*(range(d) for d in dims)))
    index = {c: i for i, c in enumerate(cells)}
    pairs = {}
    for a, d in enumerate(dims):
        for s in range(d):
            for t in (s - 1, s + 1):
                if 0 <= t < d:
                    pairs[a, s, t] = [(i, index[c[:a] + (t,) + c[a + 1:]]) for i, c in enumerate(cells) if c[a] == s]
    graph = nx.Graph()
    negative = set()
    positive = set()
    for labels in it.product(*(axis_labels(shape) for shape in shapes)):
        margins = [lab[1] for lab in labels]
        odd = sum(lab[2] for lab in labels) % 2
        moves = []
        if odd:
            for a, (word, margin, _) in enumerate(labels):
                for i in range(len(word) - 1):
                    diff = word[i + 1] - word[i]
                    s, t = (i + 1, i) if diff > 0 else (i, i + 1)
                    if margin[s] >= abs(diff):
                        moves.append((pairs[a, s, t], abs(diff)))
        for x in tables(cells, margins):
            graph.add_node(x)
            (negative if odd else positive).add(x)
            for cell_pairs, quantity in moves:
                for y in transfer_targets(x, cell_pairs, quantity, prescribed):
                    graph.add_edge(x, y)
    assert negative.isdisjoint(positive) and set(graph) == negative | positive
    assert all((u in negative) != (v in negative) for u, v in graph.edges)
    return graph, negative, positive


@cache
def character(beta, cycles):
    # Murnaghan–Nakayama in strictly decreasing beta numbers.
    if not cycles:
        return int(beta == tuple(reversed(range(len(beta)))))
    total = 0
    for i, v in enumerate(beta):
        target = v - cycles[0]
        if target < 0 or target in beta:
            continue
        crossed = sum(target < b < v for b in beta)
        smaller = tuple(sorted(beta[:i] + (target,) + beta[i + 1:], reverse=True))
        total += (-1) ** crossed * character(smaller, cycles[1:])
    return total


def coefficient(shapes):
    n = sum(shapes[0])
    fact = math.factorial(n)
    betas = [tuple(v + len(s) - 1 - i for i, v in enumerate(s)) for s in shapes]
    total = 0
    for cycles in partitions(n):
        z = math.prod(k ** m * math.factorial(m) for k, m in Counter(cycles).items())
        total += (fact // z) * math.prod(character(b, cycles) for b in betas)
    assert total >= 0 and total % fact == 0
    return total // fact


def analyze(shapes, prescribed=False, fixed_witness=None):
    graph, neg, pos = build_graph(shapes, prescribed)
    g = coefficient(shapes)
    assert len(pos) - len(neg) == g
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 100))
    mate = nx.algorithms.bipartite.hopcroft_karp_matching(graph, top_nodes=sorted(neg))
    matched = sorted(x for x in neg if x in mate)
    assert len({mate[x] for x in matched}) == len(matched)
    assert all(mate[x] in graph[x] and mate[mate[x]] == x for x in matched)
    row = dict(shapes=shapes, negative=len(neg), positive=len(pos), edges=graph.number_of_edges(), matching_size=len(matched), character_coefficient=g)
    if len(matched) < len(neg):
        # Alternating reachability from every uncovered negative vertex.
        reached = neg.difference(matched)
        stack = list(reached)
        right = set()
        while stack:
            x = stack.pop()
            for y in graph[x]:
                if y in right:
                    continue
                right.add(y)
                assert y in mate
                if mate[y] not in reached:
                    reached.add(mate[y])
                    stack.append(mate[y])
        assert len(reached) - len(right) == len(neg) - len(matched)
        witness = reached if fixed_witness is None else fixed_witness
        assert witness <= neg
        neighborhood = {y for x in witness for y in graph[x]}
        assert len(witness) > len(neighborhood)
        row.update(deficient_subset=sorted(witness), full_neighborhood=sorted(neighborhood))
    if fixed_witness is not None:
        row['matching_edges'] = [(x, mate[x]) for x in matched]
    return row


def small_certificate():
    shapes = ((1, 1),) * 3
    def array(*indices):
        return tuple(indices.count(i) for i in range(8))
    # Flat index is 4*a+2*b+c. T has two units in cell 7.
    witness = {array(7, 7), array(4, 7), array(5, 6), array(2, 7), array(3, 6), array(1, 7)}
    expected = {array(6, 7), array(5, 7), array(3, 7), array(0, 7), array(1, 6)}
    rule = analyze(shapes, True, witness)
    assert set(map(tuple, rule['full_neighborhood'])) == expected
    assert (rule['negative'], rule['positive'], rule['edges'], rule['matching_size']) == (7, 7, 21, 6)
    full = analyze(shapes)
    assert (full['edges'], full['matching_size']) == (27, 7)
    return {'prescribed': rule, 'all_transfer': full}


class TimeBudget(Exception):
    pass


def stop(signum, frame):
    raise TimeBudget()


sizes = sorted(set(params['sizes']))
assert all(isinstance(n, int) and n >= 3 for n in sizes)
certificate = small_certificate()
assert coefficient(((3,), (2, 1), (2, 1))) == 1
cases = {}
for n in sizes:
    parts = sorted(partitions(n))
    short = [p for p in parts if len(p) <= 2]
    third = [p for p in parts if len(p) == 3]
    cases[n] = [(a, b, c) for a, b in it.combinations_with_replacement(short, 2) for c in third]
coverage = {n: {'requested': len(cases[n]), 'completed': 0, 'failures': 0} for n in sizes}
records = []
interrupted_case = None
signal.signal(signal.SIGALRM, stop)
signal.setitimer(signal.ITIMER_REAL, min(95, max(1, params['seconds'])))
try:
    for n in sizes:
        for shapes in cases[n]:
            interrupted_case = shapes
            row = analyze(shapes)
            records.append(row)
            coverage[n]['completed'] += 1
            coverage[n]['failures'] += int(row['matching_size'] < row['negative'])
            interrupted_case = None
except TimeBudget:
    pass
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
# Derive coverage from fully appended records, including at a timer boundary.
for n in sizes:
    done = [r for r in records if sum(r['shapes'][0]) == n]
    coverage[n]['completed'] = len(done)
    coverage[n]['failures'] = sum(r['matching_size'] < r['negative'] for r in done)
completed = {r['shapes'] for r in records}
first_pending = next((s for n in sizes for s in cases[n] if s not in completed), None)
target = sum(map(len, cases.values()))
failures = sum(v['failures'] for v in coverage.values())
result = {'summary': f'n=2 prescribed matching 6/7, all-transfer matching 7/7. Mixed-length all-transfer cases completed {len(records)}/{target}, with {failures} failures.', 'array_format': 'Flatten in lexicographic cell order, last axis fastest. Dimensions are the three partition lengths. The margins uniquely determine the permutation labels.', 'n2_certificate': certificate, 'coverage_by_n': coverage, 'range_complete': first_pending is None, 'first_pending_triple': first_pending, 'cases': records}
with open('result.json', 'w') as out:
    json.dump(result, out, separators=(',', ':'))