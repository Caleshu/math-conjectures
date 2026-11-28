# MathResearchLab experiment 2828b1d4-bc9f-47be-b06e-960103da5a01
# Bridge-join decision with independently reconstructed shore resistances
# sha256(code) = fd77a48c5aa2766ee863d25f804291f4d6e01681379807a5ab0af6c9212df1c5
# parameters: {"seconds": 90, "start": 0}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from fractions import Fraction
from itertools import combinations
from time import monotonic
import numpy as np
import sympy as sp

params = json.load(open(os.environ['MRL_PARAMS']))
started = monotonic()
deadline = started + min(100.0, max(1.0, float(params.get('seconds', 90))))
n = 11
pairs = list(combinations(range(n), 2))
width = 1 << 45  # 55 possible edges minus 10 tree edges


def decode(code):
    adj, stack = [], []
    for ch in code:
        if ch == '(':
            v = len(adj)
            adj.append([])
            if stack:
                u = stack[-1]
                adj[u].append(v)
                adj[v].append(u)
            stack.append(v)
        else:
            stack.pop()
    return adj


def tree_code(adj):
    def rooted(v, parent):
        branches = sorted(rooted(w, v) for w in adj[v] if w != parent)
        return '(' + ''.join(branches) + ')'
    return min(rooted(v, -1) for v in range(len(adj)))


def tree_inventory():
    codes = {'()'}
    for size in range(1, n):
        new_codes = set()
        for code in codes:
            adj = decode(code)
            for v in range(size):
                adj[v].append(size)
                adj.append([v])
                new_codes.add(tree_code(adj))
                adj.pop()
                adj[v].pop()
        codes = new_codes
    return sorted(codes)


def prepare(code):
    adj = decode(code)
    A = tuple(sum(1 << w for w in row) for row in adj)
    dist = []
    for root in range(n):
        d = [-1] * n
        d[root] = 0
        queue = [root]
        for u in queue:
            for v in adj[u]:
                if d[v] == -1:
                    d[v] = d[u] + 1
                    queue.append(v)
        dist.append(d)
    edges = [(u, v) for u, v in pairs if v in adj[u]]
    cuts = []
    for p, q in edges:
        side = [x for x in range(n) if dist[x][p] < dist[x][q]]
        other = [x for x in range(n) if x not in side]
        cuts.append((p, q, side, other))
    chords = []
    for u, v in pairs:
        if dist[u][v] == 1:
            continue
        crossed = 0
        for i, (p, q, left, right) in enumerate(cuts):
            if (u in left) == (v in left):
                continue
            crossed |= 1 << i
            x, y = (u, v) if u in left else (v, u)
            change = len(right) * sum(dist[z][x] - dist[z][p] for z in left)
            change += len(left) * sum(dist[z][y] - dist[z][q] for z in right)
            if change < 0:
                break
        else:
            chords.append((u, v, crossed))
    chords.sort(key=lambda e: (-dist[e[0]][e[1]], e[0], e[1]))
    return A, np.array(dist, dtype=np.int64), edges, chords


def add_resistance(N, D, u, v):
    # N/D is the resistance matrix, D the tree count. The determinant
    # lemma gives Dnew. Sherman-Morrison gives the outer-product correction.
    Dnew = D + int(N[u, v])
    diff = N[:, u] - N[:, v]
    cross = diff[:, None] - diff[None, :]
    # With m <= 35, the ten positive Laplacian eigenvalues sum to <= 70.
    # Matrix-tree and AM-GM give D <= 7**10/11. Also N_ij <= 10D.
    # Thus both products below and the 121-entry matrix sum fit int64.
    numerator = 4 * Dnew * N - cross * cross
    updated, rem = np.divmod(numerator, 4 * D)
    if np.any(rem) or np.any(updated < 0):
        raise ArithmeticError('inexact resistance update')
    return updated, Dnew


def shore_matrix(A, vertices):
    s = len(vertices)
    R = [[Fraction(0) for _ in vertices] for _ in vertices]
    if s == 1:
        return R
    # Ground the last vertex. Use internal degrees, including edges to ground.
    M = sp.zeros(s - 1)
    for i, u in enumerate(vertices[:-1]):
        M[i, i] = sum((A[u] >> v) & 1 for v in vertices)
        for j, v in enumerate(vertices[:-1]):
            if i != j:
                M[i, j] = -((A[u] >> v) & 1)
    inv = M.inv()
    B = [[Fraction(0) for _ in vertices] for _ in vertices]
    for i in range(s - 1):
        for j in range(s - 1):
            a, b = inv[i, j].as_numer_denom()
            B[i][j] = Fraction(int(a), int(b))
    for i, j in combinations(range(s), 2):
        R[i][j] = R[j][i] = B[i][i] + B[j][j] - 2 * B[i][j]
    return R


def exact_join(A, p, q, prefix=None):
    left = [p]
    seen = {p}
    for u in left:
        for v in range(len(A)):
            if (u, v) == (p, q) or v in seen or not ((A[u] >> v) & 1):
                continue
            left.append(v)
            seen.add(v)
    if q in seen:
        raise ValueError('selected edge is not a bridge')
    right = [v for v in range(len(A)) if v not in seen]
    R = [[Fraction(0) for _ in A] for _ in A]
    for shore in (left, right):
        block = shore_matrix(A, shore)
        for i, u in enumerate(shore):
            for j, v in enumerate(shore):
                R[u][v] = block[i][j]
    for u in left:
        for v in right:
            R[u][v] = R[v][u] = R[u][p] + 1 + R[q][v]
    if prefix is not None:
        N, D = prefix
        if any(R[u][v] * D != int(N[u, v]) for u, v in pairs):
            raise ArithmeticError('shore and prefix resistances disagree')
    degrees = [row.bit_count() for row in A]
    m = sum(degrees) // 2
    S = [sum(r * d for r, d in zip(row, degrees)) for row in R]
    return sum(m * R[u][v] + abs(S[u] - S[v]) / 2
               for u, v in combinations(range(len(A)), 2))


def masks(size, edges):
    A = [0] * size
    for u, v in edges:
        A[u] |= 1 << v
        A[v] |= 1 << u
    return tuple(A)


def run():
    # On P3 the two adjacent-pair maxima are 3 and the end-pair maximum is 4.
    assert exact_join(masks(3, [(0, 1), (1, 2)]), 0, 1) == 10
    # A cyclic shore exercises inversion and a nonintegral resistance.
    clique = list(combinations(range(6), 2))
    tail = [(i, i + 1) for i in range(5, 10)]
    lollipop = masks(n, clique + tail)
    tree = [(0, i) for i in range(1, 6)] + tail
    A0 = masks(n, tree)
    N = np.zeros((n, n), dtype=np.int64)
    for r in range(n):
        queue, seen = [r], {r}
        for u in queue:
            for v in range(n):
                if (A0[u] >> v) & 1 and v not in seen:
                    seen.add(v)
                    N[r, v] = N[r, u] + 1
                    queue.append(v)
    D = 1
    for u, v in clique:
        if (u, v) not in tree:
            N, D = add_resistance(N, D, u, v)
    assert 3 * exact_join(lollipop, 5, 6, (N, D)) == 11950
    codes = tree_inventory()
    assert len(codes) == 235
    total = len(codes) * width
    start = int(params.get('start', 0))
    stop = int(params.get('stop', total))
    if not 0 <= start < stop <= total:
        raise ValueError('invalid half-open rank range')
    cursor = start
    stats = {'scope_closures': 0, 'bound_closures': 0, 'exact_scores': 0}
    witness = None

    class Budget(Exception):
        pass

    class Found(Exception):
        pass

    def close(lo, hi):
        nonlocal cursor
        assert cursor == max(start, lo)
        cursor = min(stop, hi)

    def visit(lo, hi, depth, A, N, D, m, bridges):
        nonlocal witness
        if hi <= start or lo >= stop:
            return
        if monotonic() >= deadline:
            raise Budget
        remaining = len(chords) - depth
        if (not bridges or m + remaining < 14 or
                not any(not ((A[u] >> v) & 1) and not (A[u] & A[v]) for u, v in pairs)):
            stats['scope_closures'] += 1
            close(lo, hi)
            return
        # Sorted undecided resistances minimize the amount we may subtract.
        costs = sorted(int(N[u, v]) for u, v, _ in chords[depth:])
        upper_K_num = int(N.sum()) // 2
        for t in range(min(remaining, 35 - m) + 1):
            if t:
                upper_K_num -= costs[t - 1]
            final_m = m + t
            if final_m >= 14 and 6 * final_m * upper_K_num - 3 * (110 - final_m) * D > 11950 * D:
                break
        else:
            stats['bound_closures'] += 1
            close(lo, hi)
            return
        if not remaining or m == 35:
            # At m=35 every strict supergraph is out of scope.
            i = (bridges & -bridges).bit_length() - 1
            p, q = tree_edges[i]
            score3 = 3 * exact_join(A, p, q, (N, D))
            stats['exact_scores'] += 1
            if score3 > 11950:
                witness = {'edges': [[u, v] for u, v in pairs if (A[u] >> v) & 1],
                           'bridge': [p, q], 'three_HT_numerator': score3.numerator,
                           'three_HT_denominator': score3.denominator}
                raise Found
            close(lo, hi)
            return
        mid = (lo + hi) // 2
        u, v, cut_mask = chords[depth]
        visit(lo, mid, depth + 1, A, N, D, m, bridges)
        if mid < stop and start < hi:
            if not (bridges & ~cut_mask):
                stats['scope_closures'] += 1
                close(mid, hi)
                return
            B = list(A)
            B[u] |= 1 << v
            B[v] |= 1 << u
            M, E = add_resistance(N, D, u, v)
            visit(mid, hi, depth + 1, B, M, E, m + 1, bridges & ~cut_mask)

    try:
        for index in range(start // width, (stop - 1) // width + 1):
            A, N, tree_edges, chords = prepare(codes[index])
            visit(index * width, (index + 1) * width, 0, A, N, 1, 10, (1 << 10) - 1)
        assert cursor == stop
        status = 'PASS' if start == 0 and stop == total else 'RANGE_PASS'
    except Budget:
        status = 'PARTIAL'
    except Found:
        status = 'COUNTEREXAMPLE'
    return {'summary': status, 'checked_half_open': [str(start), str(cursor)],
            'requested_stop': str(stop), 'full_stop': str(total), 'witness': witness,
            'sanity': {'P3_HT': '10', 'lollipop_three_HT': '11950', 'tree_shapes': len(codes)},
            'counts': stats}

try:
    result = run()
except Exception as exc:
    result = {'summary': 'CHECK_ERROR', 'error': repr(exc)}
with open('result.json', 'w') as out:
    json.dump(result, out)
