# MathResearchLab experiment 2a1c8f0c-e04b-43e7-83fa-3fcadb9a878a
# Can adjacent-slice moves cancel the negative contingency tables?
# sha256(code) = 845191da063f37fdbdaa78221488e7f4eebe0e7852828b7267413d419bb6c885
# parameters: {"n_max": 6}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from collections import Counter, defaultdict, deque
from functools import lru_cache
from itertools import combinations_with_replacement, permutations, product
from math import factorial, prod
from time import monotonic
import networkx as nx

params = json.load(open(os.environ['MRL_PARAMS']))
n_max = int(params['n_max'])
assert 1 <= n_max <= 6
start = monotonic()

@lru_cache(None)
def parts(n, limit):
    if n == 0:
        return ((),)
    return tuple((k,) + tail for k in range(min(n, limit), 0, -1) for tail in parts(n-k, k))

@lru_cache(None)
def margins(shape):
    r = len(shape)
    shifted = tuple(v+r-1-i for i, v in enumerate(shape))
    out = {}
    for perm in permutations(range(r)):
        a = tuple(shifted[j]-(r-1-i) for i, j in enumerate(perm))
        if min(a) >= 0:
            inversions = sum(x > y for i, x in enumerate(perm) for y in perm[i+1:])
            out[a] = (-1)**inversions
    return out

@lru_cache(None)
def character(shape, cycle):
    # Coefficient of x^(shape+delta) in the alternant times the power sums.
    r = len(shape)
    target = tuple(v+r-1-i for i, v in enumerate(shape))
    dp = {(0,)*r: 1}
    for k in cycle:
        nxt = defaultdict(int)
        for exps, ways in dp.items():
            for i in range(r):
                if exps[i]+k <= target[i]:
                    new = list(exps)
                    new[i] += k
                    nxt[tuple(new)] += ways
        dp = nxt
    total = 0
    for delta_term in permutations(range(r-1, -1, -1)):
        flips = sum(x < y for i, x in enumerate(delta_term) for y in delta_term[i+1:])
        needed = tuple(x-y for x, y in zip(target, delta_term))
        total += (-1)**flips * dp.get(needed, 0)
    return total

def kronecker(shapes):
    n = sum(shapes[0])
    order = factorial(n)
    numerator = 0
    for cycle in parts(n, n):
        centralizer = prod(k**v * factorial(v) for k, v in Counter(cycle).items())
        numerator += (order//centralizer) * prod(character(s, cycle) for s in shapes)
    value, remainder = divmod(numerator, order)
    assert remainder == 0 and value >= 0
    return value

def tables(a, b, c):
    # Place units in sorted cell order within each first-axis slice.
    rows = [i for i, count in enumerate(a) for _ in range(count)]
    width = len(b)*len(c)
    data = [0]*(len(a)*width)
    left_b, left_c = list(b), list(c)
    def visit(t, first):
        if t == len(rows):
            yield tuple(data)
            return
        i = rows[t]
        for pos in range(first, width):
            j, k = divmod(pos, len(c))
            if left_b[j] and left_c[k]:
                cell = i*width+pos
                data[cell] += 1
                left_b[j] -= 1
                left_c[k] -= 1
                same_row = t+1 < len(rows) and rows[t+1] == i
                yield from visit(t+1, pos if same_row else 0)
                left_b[j] += 1
                left_c[k] += 1
                data[cell] -= 1
    yield from visit(0, 0)

def signature(table, fibers):
    down, up = [], []
    for i, j in fibers:
        for _ in range(table[j]):
            if up:
                up.pop()
            else:
                down.append((i, j))
        up.extend([(i, j)]*table[i])
    if not down:
        return None
    out = list(table)
    target_down = len(up)+1
    for t, (i, j) in enumerate(down+up):
        change = int(t < target_down)-int(t < len(down))
        out[i] -= change
        out[j] += change
    return tuple(out)

def transfers(table, fibers):
    # Shifted margin difference equals the amount the swap must transfer.
    amount = 1+sum(table[i]-table[j] for i, j in fibers)
    assert amount != 0
    if amount < 0:
        fibers = [(j, i) for i, j in fibers]
        amount = -amount
    active = [(i, j) for i, j in fibers if table[i]]
    out = list(table)
    def visit(t, left):
        if left == 0:
            yield tuple(out)
        elif t < len(active):
            i, j = active[t]
            for moved in range(min(left, table[i])+1):
                out[i] -= moved
                out[j] += moved
                yield from visit(t+1, left-moved)
                out[i] += moved
                out[j] -= moved
    yield from visit(0, amount)

def solve_graph(negative, positive, neighbors):
    graph = nx.Graph()
    graph.add_nodes_from(negative)
    graph.add_nodes_from(positive)
    for t in negative:
        for u in neighbors(t):
            assert u in positive
            graph.add_edge(t, u)
    match = nx.algorithms.bipartite.maximum_matching(graph, top_nodes=negative) if negative else {}
    free = negative-match.keys()
    report = {'matched_negative': len(negative)-len(free)}
    if free:
        # Alternating reachability gives S and its entire neighborhood.
        seen = set(free)
        queue = deque(free)
        adjacent = set()
        while queue:
            t = queue.popleft()
            for u in graph[t]:
                adjacent.add(u)
                assert u in match
                if match[u] not in seen:
                    seen.add(match[u])
                    queue.append(match[u])
        assert len(adjacent) < len(seen)
        report['hall_witness'] = {'negative_tables': sorted(seen), 'positive_neighbors': sorted(adjacent)}
    return report

def investigate(shapes):
    dims = tuple(map(len, shapes))
    cells = list(product(*(range(d) for d in dims)))
    index = {c: i for i, c in enumerate(cells)}
    moves = []
    for axis, d in enumerate(dims):
        for level in range(d-1):
            fibers = []
            for c in cells:
                if c[axis] == level:
                    other = list(c)
                    other[axis] += 1
                    fibers.append((index[c], index[tuple(other)]))
            moves.append(fibers)
    negative, positive = set(), set()
    for (a, sa), (b, sb), (c, sc) in product(*(margins(s).items() for s in shapes)):
        side = positive if sa*sb*sc == 1 else negative
        for t in tables(a, b, c):
            assert t not in side
            side.add(t)
    g = kronecker(shapes)
    assert not (positive & negative) and len(positive)-len(negative) == g
    def prescribed(t):
        for fibers in moves:
            u = signature(t, fibers)
            if u is not None:
                assert signature(u, fibers) == t
                assert u in set(transfers(t, fibers))
                yield u
    narrow = solve_graph(negative, positive, prescribed)
    if 'hall_witness' in narrow:
        wide = solve_graph(negative, positive, lambda t: (u for f in moves for u in transfers(t, f)))
    else:
        wide = {'matched_negative': len(negative), 'certificate': 'covering matching in prescribed subgraph'}
    return {'shapes': shapes, 'g': g, 'positive': len(positive), 'negative': len(negative), 'prescribed': narrow, 'all_transfers': wide}

assert character((2, 1), (3,)) == -1
assert kronecker(((2, 1),)*3) == 1
assert kronecker(((1, 1),)*3) == 0
assert signature((1, 1), [(0, 1)]) == (0, 2)
assert signature((0, 2), [(0, 1)]) == (1, 1)
rows = []
complete = True
for n in range(1, n_max+1):
    shapes = sorted(p for p in parts(n, n) if len(p) <= 3)
    for triple in combinations_with_replacement(shapes, 3):
        if monotonic()-start > 80:
            complete = False
            break
        rows.append(investigate(triple))
    if not complete:
        break
failures = {key: sum('hall_witness' in row[key] for row in rows) for key in ('prescribed', 'all_transfers')}
result = {'summary': f'Checked {len(rows)} triples. Prescribed failures: {failures["prescribed"]}. All-transfer failures: {failures["all_transfers"]}. Requested range complete: {complete}.', 'complete': complete, 'n_max': n_max, 'failure_counts': failures, 'table_encoding': 'Flatten in lexicographic coordinate order, using partition lengths as axis sizes.', 'rows': rows}
with open('result.json', 'w') as f:
    json.dump(result, f)
