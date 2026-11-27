# MathResearchLab experiment 27d54a0a-472f-41b1-8cce-0f159ac5fcab
# Exact Table 20 polynomial and certificates for its odd descent candidates
# sha256(code) = 7810c0bffee55637d3f27b2f4545fd7bb9ac99a14a5b8056cce4f840aa67f5f8
# parameters: {"table20": {"x": null, "w": null}, "odd_candidate": null}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from collections import deque
from itertools import combinations

params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()

def check_time():
    if time.monotonic() - start > 105:
        raise TimeoutError('Internal 105-second limit reached')

def perm(values):
    p = tuple(values)
    if not p or sorted(p) != list(range(1, len(p) + 1)):
        raise ValueError('Expected a one-line permutation of 1 through m')
    return p

def length(p):
    return sum(a > b for a, b in combinations(p, 2))

def swap(p, i, j):
    v = list(p)
    v[i], v[j] = v[j], v[i]
    return tuple(v)

def trim(p):
    p = list(p)
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return p

def descent_moves(x, w):
    moves = {}
    for side in ('right', 'left'):
        for i in range(len(w) - 1):
            def act(p):
                if side == 'right':
                    return swap(p, i, i + 1)
                return swap(p, p.index(i + 1), p.index(i + 2))
            y = act(x)
            if length(act(w)) < length(w) and length(y) > length(x):
                moves.setdefault(y, []).append([side, i + 1])
    return moves

def interval_kl(x, w, targets):
    # Enumerate the interval downward. Sorted prefixes implement the Bruhat criterion.
    n = len(x)
    if len(w) != n:
        raise ValueError('Endpoint sizes differ')
    prefixes = [sorted(x[:k]) for k in range(1, n)]
    def above_x(p):
        return all(all(a <= b for a, b in zip(row, sorted(p[:k])))
                   for k, row in enumerate(prefixes, 1))
    if not above_x(w):
        raise ValueError('Lower endpoint is not below upper endpoint')
    D = length(w) - length(x)
    levels = [[] for _ in range(D + 1)]
    rank = {w: D}
    parent = {w: None}
    queue = deque([w])
    labels = list(combinations(range(n), 2))
    while queue:
        check_time()
        v = queue.popleft()
        r = rank[v]
        levels[r].append(v)
        if r == 0:
            continue
        for i, j in labels:
            a, b = v[i], v[j]
            if a <= b or any(b < t < a for t in v[i+1:j]):
                continue
            p = swap(v, i, j)
            if p not in parent and above_x(p):
                parent[p] = v
                rank[p] = r - 1
                queue.append(p)
    assert levels[0] == [x] and all(p in rank for p in targets)

    # Dyer's increasing-path formula for ordinary R-polynomials. Use lexicographic
    # reflection order on position pairs (i,j). An upward edge of rank jump 2s+1
    # has weight q^s(q-1). Include every reflection edge, including long edges.
    edges = [[] for _ in labels]
    for p in rank:
        check_time()
        for t, (i, j) in enumerate(labels):
            if p[i] < p[j]:
                z = swap(p, i, j)
                if z in rank:
                    jump = rank[z] - rank[p]
                    assert jump > 0 and jump % 2 == 1
                    edges[t].append((p, z, jump // 2))

    # At p, total accumulates S_p = sum_{z>p} R_{p,z} P_{z,w}.
    # For delta = length(w)-length(p), bar invariance gives
    # q^delta P_{p,w}(1/q) - P_{p,w}(q) = S_p(q).
    # Hence P[i] = S_p[delta-i] for 0 <= i <= floor((delta-1)/2).
    total = {p: [0] * (D + 1) for p in rank}
    polys = {}
    trace = {p: [] for p in targets}
    for b in range(D, -1, -1):
        check_time()
        wave = {}
        for p in levels[b]:
            delta = D - b
            if delta == 0:
                poly = [1]
            else:
                poly = [total[p][delta-i] for i in range((delta-1)//2 + 1)]
                residual = [0] * (D + 1)
                for i, value in enumerate(poly):
                    residual[delta-i] += value
                    residual[i] -= value
                assert residual == total[p], 'Full bar identity failed'
            polys[p] = trim(poly)
            wave[p] = poly + [0] * (D + 1 - len(poly))
        if b == 0:
            break
        # Propagate from all z of rank b at once. Reverse processing gives
        # increasing labels from p up to z. Edges of one label are disjoint.
        for group in reversed(edges):
            check_time()
            for p, z, s in group:
                if z not in wave:
                    continue
                if p not in wave:
                    wave[p] = [0] * (D + 1)
                src, dst = wave[z], wave[p]
                for k in range(D - s):
                    dst[k+s] -= src[k]
                    dst[k+s+1] += src[k]
        for p, row in wave.items():
            if rank[p] == b:
                continue
            total[p] = [a + v for a, v in zip(total[p], row)]
            if p in trace:
                trace[p].append({'length_z_minus_length_p': b-rank[p], 'sum_R_pz_times_P_zw': trim(row)})
    return parent, polys, trace

def certificate(x, w, parent, polys, trace):
    n = len(x)
    d = length(w) - length(x)
    rel = [x.index(value) for value in w]
    cycles, seen = [], set()
    for i in range(n):
        if i in seen:
            continue
        cycle = []
        while i not in seen:
            seen.add(i)
            cycle.append(i + 1)
            i = rel[i]
        cycles.append(cycle)
    common, removable = [], []
    for i, value in enumerate(x):
        if w[i] == value:
            a = sum(t >= value for t in x[:i])
            b = sum(t >= value for t in w[:i])
            common.append([i + 1, value, a, b])
            if a == b:
                removable.append(i + 1)
    chain, swaps = [x], []
    neighbors = [set() for _ in x]
    while chain[-1] != w:
        p = chain[-1]
        z = parent[p]
        i, j = [k for k in range(n) if p[k] != z[k]]
        assert swap(p, i, j) == z and length(z) == length(p) + 1
        neighbors[i].add(j)
        neighbors[j].add(i)
        chain.append(z)
        swaps.append([i + 1, j + 1])
    assert len(swaps) == d
    unseen, components = set(range(n)), []
    while unseen:
        root = min(unseen)
        stack, comp = [root], {root}
        unseen.remove(root)
        while stack:
            for j in neighbors[stack.pop()] & unseen:
                unseen.remove(j)
                comp.add(j)
                stack.append(j)
        components.append(sorted(j + 1 for j in comp))
    connected = len(components) == 1
    numerator = d - n - len(cycles) + 2
    if connected:
        assert numerator >= 0 and numerator % 2 == 0
    h = (d-1)//2 if d else None
    poly = polys[x]
    top = None if h is None else (poly[h] if h < len(poly) else 0)
    qualifies = bool(d % 2 and connected and not removable and numerator == 0)
    return {'x': x, 'w': w, 'length_x': length(x), 'length_w': length(w), 'd': d,
            'cycles_of_x_inverse_w': cycles, 'c': len(cycles), 'components': components,
            'connected': connected, 'G': numerator//2 if connected else None,
            'common_position_value_and_two_prefix_counts': common,
            'compressible_positions': removable, 'uncompressible': not removable,
            'saturated_chain': chain, 'position_swaps': swaps, 'P_ascending': poly,
            'permitted_degree': h, 'coefficient': top, 'qualifies': qualifies,
            'counterexample': qualifies and top > 1,
            'bar_sum_grouped_by_rank': trace[x], 'bar_identity_verified': True}

def solve_one(x, w):
    parent, polys, trace = interval_kl(x, w, {x})
    return certificate(x, w, parent, polys, trace)

def after_deletion(record):
    omit = set(record['compressible_positions'])
    if not omit or len(omit) == len(record['x']):
        return None
    def flatten(p):
        vals = [v for i, v in enumerate(p, 1) if i not in omit]
        ranks = {v: i for i, v in enumerate(sorted(vals), 1)}
        return tuple(ranks[v] for v in vals)
    return solve_one(flatten(record['x']), flatten(record['w']))

out = {'summary': '', 'sanity': {}, 'descent_candidates': []}
try:
    e, y, v = (1,2,3,4), (1,3,2,4), (3,4,1,2)
    parent, polys, trace = interval_kl(e, v, {e, y})
    small = certificate(y, v, parent, polys, trace)
    assert polys[e] == polys[y] == [1,1]
    assert small['qualifies'] and small['coefficient'] == 1 and small['c'] == 1
    smooth = solve_one((1,2,3), (3,2,1))
    assert smooth['P_ascending'] == [1] and smooth['coefficient'] == 0
    out['sanity'] = {'passed': True, 'P_1234_3412': polys[e], 'P_1324_3412': polys[y], 'P_123_321': smooth['P_ascending']}
    table = params.get('table20')
    if table and table.get('x') is not None and table.get('w') is not None:
        x, w = perm(table['x']), perm(table['w'])
        moves = descent_moves(x, w)
        parent, polys, trace = interval_kl(x, w, {x} | set(moves))
        base = certificate(x, w, parent, polys, trace)
        out['table20'] = base
        out['benchmark_checks'] = {'m_is_10': len(w) == 10, 'd_is_10': base['d'] == 10, 'G_is_0': base['G'] == 0, 'q4_is_8': polys[x][4:5] == [8]}
        for y, labels in moves.items():
            rec = certificate(y, w, parent, polys, trace)
            item = {'moves_side_and_simple_index': labels, 'pair': rec}
            out['descent_candidates'].append(item)
            if rec['compressible_positions']:
                item['after_standardized_deletion'] = after_deletion(rec)
    else:
        out['table20_status'] = 'Missing Table 20 endpoint permutations'
    odd = params.get('odd_candidate')
    if odd is not None:
        rec = solve_one(perm(odd['x']), perm(odd['w']))
        out['supplied_candidate'] = rec
        if rec['compressible_positions']:
            out['supplied_candidate_after_deletion'] = after_deletion(rec)
    if 'table20' in out:
        out['summary'] = 'Computed the polynomial and chain certificate for the supplied Table 20 pair and all distinct descent candidates.'
    else:
        out['summary'] = 'Table 20 endpoints were absent. The sanity cases passed.' + (' The supplied odd candidate was evaluated.' if odd is not None else '')
except TimeoutError as exc:
    out['summary'] = 'Partial computation. ' + str(exc)
except (AssertionError, ValueError, KeyError, TypeError) as exc:
    out['summary'] = 'Validation failed. ' + type(exc).__name__ + ' ' + str(exc)
    out['validation_failed'] = True
with open('result.json', 'w') as f:
    json.dump(out, f)
