# MathResearchLab experiment d410c963-1bda-4249-9460-a8056465e7f2
# Exact descent-move certificates for Table 20 and a bounded search for its endpoints
# sha256(code) = f55d37f5975dbef6cfc9b83ba93667abc34b00b92764b629f069089ab85fe7c2
# parameters: {"seed_x": "4321098765", "seed_w": "9467182350", "table_x": null, "table_w": null, "fixed_upper_search": true, "seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from functools import lru_cache

params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()
deadline = start + min(100.0, float(params.get('seconds', 90)))

def tick():
    if time.monotonic() >= deadline:
        raise TimeoutError

def permutation(data):
    p = tuple(map(int, data))
    if sorted(p) != list(range(len(p))):
        raise ValueError('Use zero-based one-line permutations.')
    return p

def swap(p, i, j):
    a = list(p)
    a[i], a[j] = a[j], a[i]
    return tuple(a)

@lru_cache(maxsize=16000)
def inv(p):
    a = [0] * len(p)
    for i, v in enumerate(p):
        a[v] = i
    return tuple(a)

@lru_cache(maxsize=30000)
def length(p):
    return sum(p[i] > p[j] for j in range(len(p)) for i in range(j))

@lru_cache(maxsize=60000)
def leq(a, b):
    if len(a) != len(b) or length(a) > length(b):
        return False
    # At each prefix count entries >= t. Only thresholds strictly between
    # the two new entries (including the larger entry) change discrepancy.
    delta = [0] * len(a)
    for x, y in zip(a, b):
        if x < y:
            for t in range(x + 1, y + 1):
                delta[t] += 1
        elif x > y:
            for t in range(y + 1, x + 1):
                delta[t] -= 1
                if delta[t] < 0:
                    return False
    return True

def covers(p, up):
    for i, v in enumerate(p):
        record = len(p) if up else -1
        for j in range(i + 1, len(p)):
            u = p[j]
            if (v < u < record) if up else (record < u < v):
                yield swap(p, i, j), (i, j)
                record = u

def cycles(a, b):
    ai = inv(a)
    rel = tuple(ai[v] for v in b)
    seen = set()
    answer = []
    for i in range(len(a)):
        if i in seen:
            continue
        orbit = []
        while i not in seen:
            seen.add(i)
            orbit.append(i)
            i = rel[i]
        answer.append(orbit)
    return answer

def flatten(a, b):
    deleted = []
    original = list(range(len(a)))
    while True:
        for i, v in enumerate(a):
            if b[i] == v and sum(t >= v for t in a[:i]) == sum(t >= v for t in b[:i]):
                break
        else:
            return a, b, deleted
        deleted.append(original.pop(i))
        a = tuple(t - int(t > v) for j, t in enumerate(a) if j != i)
        b = tuple(t - int(t > v) for j, t in enumerate(b) if j != i)

def geometry(a, b):
    d = length(b) - length(a)
    out = {'x': a, 'w': b, 'd': d, 'comparable': leq(a, b)}
    if not out['comparable']:
        return out
    blocks = [{i} for i in range(len(a))]
    chain = []
    p = a
    while p != b:
        tick()
        p, (i, j) = next((q, edge) for q, edge in covers(p, True) if leq(q, b) for i, j in [edge])
        chain.append((i, j))
        s = next(s for s in blocks if i in s)
        t = next(s for s in blocks if j in s)
        if s is not t:
            blocks.remove(t)
            s.update(t)
    assert len(chain) == d
    cyc = cycles(a, b)
    out.update(cycles=cyc, components=sorted(sorted(s) for s in blocks), chain_position_swaps=chain,
               connected=len(blocks) == 1, genus_numerator_if_connected=d - len(a) - len(cyc) + 2,
               uncompressible=not flatten(a, b)[2])
    return out

def genus_zero(g):
    return g.get('connected', False) and g['genus_numerator_if_connected'] == 0

def moves(p, w, raising):
    for side in ('right', 'left'):
        u, v = (p, w) if side == 'right' else (inv(p), inv(w))
        for i in range(len(v) - 1):
            if v[i] > v[i + 1] and (u[i] < u[i + 1]) == raising:
                z = swap(u, i, i + 1)
                yield side, i, z if side == 'right' else inv(z)

# Ordinary right-descent KL recursion. Tuples give coefficients in ascending
# degree. Empty tuples represent incomparable pairs. All arithmetic is integral.
@lru_cache(maxsize=80000)
def kl(a, b):
    tick()
    if not leq(a, b):
        return ()
    d = length(b) - length(a)
    if d <= 2:
        return (1,)
    desc = [i for i in range(len(b) - 1) if b[i] > b[i + 1]]
    for i in desc:
        if a[i] < a[i + 1]:
            return kl(swap(a, i, i + 1), b)
    i = desc[0]
    v = swap(b, i, i + 1)
    h = (d - 1) // 2
    # Keep an extra degree for the intermediate q*P term and cancellations.
    out = [0] * (h + 2)
    def add(poly, shift, scale):
        for j, t in enumerate(poly, shift):
            out[j] += scale * t
    add(kl(swap(a, i, i + 1), v), 0, 1)
    add(kl(a, v), 1, 1)
    if leq(a, v):
        stack = [v]
        visited = {v}
        while stack:
            tick()
            u = stack.pop()
            gap = length(v) - length(u)
            if gap % 2 and u[i] > u[i + 1]:
                mu = coeff(kl(u, v), (gap - 1) // 2)
                if mu:
                    add(kl(a, u), (gap + 1) // 2, -mu)
            if u != a:
                for z, _ in covers(u, False):
                    if z not in visited and leq(a, z):
                        visited.add(z)
                        stack.append(z)
    assert out[0] == 1 and out[-1] == 0 and min(out) >= 0
    while out[-1] == 0:
        out.pop()
    return tuple(out)

def coeff(p, i):
    return p[i] if i < len(p) else 0

report = {'indexing': 'Values, positions and simple-reflection indices start at zero. Index i exchanges i and i+1.',
          'sanity': {}, 'phases': {}, 'supplied_or_nearby_parents': [], 'witnesses': [],
          'fixed_upper_children_after_descent_and_order_filters': 0, 'fixed_upper_qualifying_flattenings_with_parent_candidate': 0}
seen = set()

def inspect(a, b, label, save):
    tick()
    if (a, b) in seen:
        return
    parent = geometry(a, b)
    row = {'origin': label, 'parent': parent, 'moves': []}
    if save:
        report['supplied_or_nearby_parents'].append(row)
    if len(a) != 10 or parent['d'] != 10 or not genus_zero(parent):
        row['status'] = 'fails reported parent size, rank, comparability or genus'
        seen.add((a, b))
        return
    row['status'] = 'computing parent polynomial'
    pp = kl(a, b)
    row.update(parent_KL=pp, parent_q4=coeff(pp, 4))
    row['status'] = 'checking moves'
    for side, i, y in moves(a, b, True):
        assert leq(y, b) and length(y) == length(a) + 1
        u, v, removed = flatten(y, b)
        child = geometry(u, v)
        entry = {'side': side, 'simple_index': i, 'raw_child_x': y, 'deleted_original_positions': removed, 'flattened_child': child}
        row['moves'].append(entry)
        if child['d'] != 9 or not child['uncompressible'] or not genus_zero(child):
            continue
        cp = kl(u, v)
        entry.update(child_KL=cp, child_q4=coeff(cp, 4))
        if coeff(pp, 4) == 8 and coeff(cp, 4) >= 2:
            # Inverse endpoints replay the calculation with left descents.
            assert kl(inv(u), inv(v)) == cp and kl(inv(a), inv(b)) == pp
            report['witnesses'].append({'origin': label, 'parent': parent, 'parent_KL': pp, 'move': entry,
                                        'inverse_recurrence_agrees': True})
    row['status'] = 'complete'
    seen.add((a, b))

def candidate_children(w):
    n = len(w)
    target = length(w) - 9
    wi = inv(w)
    upper_prefix = [sorted(w[:k]) for k in range(n + 1)]
    def visit(p, unused, count):
        tick()
        k = len(p)
        if not unused:
            if count == target:
                yield p
            return
        for j, v in enumerate(unused):
            # j unused smaller values will follow v in the completed word.
            total = count + j
            left = len(unused) - 1
            if total > target or total + left * (left - 1) // 2 < target:
                continue
            if k and w[k - 1] > w[k] and p[-1] < v:
                continue
            if v + 1 < n and wi[v] > wi[v + 1] and v + 1 in unused:
                continue
            q = p + (v,)
            if any(s > t for s, t in zip(sorted(q), upper_prefix[k + 1])):
                continue
            yield from visit(q, unused[:j] + unused[j + 1:], total)
    yield from visit((), tuple(range(n)), 0)

phase = 'sanity'
try:
    e = (0, 1, 2, 3)
    singular = (2, 3, 0, 1)
    assert kl(e, singular) == (1, 1)
    assert kl(e, (3, 2, 1, 0)) == (1,)
    assert kl(singular, e) == ()
    tiny = geometry((0, 1), (1, 0))
    assert genus_zero(tiny) and tiny['uncompressible']
    assert flatten((0, 1, 2), (1, 0, 2)) == ((0, 1), (1, 0), [2])
    report['sanity'] = {'P_1234_3412_in_one_based_notation': [1, 1], 'P_identity_longest_S4': [1], 'geometry_and_flatten_checks': 'passed'}
    if params.get('table_x') is not None or params.get('table_w') is not None:
        phase = 'source_transcribed_pair'
        inspect(permutation(params['table_x']), permutation(params['table_w']), phase, True)
        report['phases'][phase] = 'complete'
    else:
        a, b = permutation(params['seed_x']), permutation(params['seed_w'])
        phase = 'all_rank_ten_subintervals_of_seed'
        report['seed'] = geometry(a, b)
        if not leq(a, b) or length(b) - length(a) != 11 or len(a) != 10:
            raise ValueError('The fallback seed must be a comparable rank-eleven pair in S10.')
        parents = [(z, b) for z, _ in covers(a, True) if leq(z, b)]
        parents += [(a, z) for z, _ in covers(b, False) if leq(a, z)]
        report['number_of_nearby_parents'] = len(parents)
        for u, v in parents:
            inspect(u, v, phase, True)
        report['phases'][phase] = 'complete'
        if params.get('fixed_upper_search', True) and not report['witnesses']:
            phase = 'all_potential_witness_children_with_seed_upper_endpoint'
            for y in candidate_children(b):
                report['fixed_upper_children_after_descent_and_order_filters'] += 1
                possible = {z for _, _, z in moves(y, b, False) if (z, b) not in seen and len(cycles(z, b)) == 2}
                if not possible:
                    continue
                u, v, _ = flatten(y, b)
                g = geometry(u, v)
                if g['d'] != 9 or not g['uncompressible'] or not genus_zero(g):
                    continue
                report['fixed_upper_qualifying_flattenings_with_parent_candidate'] += 1
                if coeff(kl(y, b), 4) != 8:
                    continue
                for z in sorted(possible):
                    inspect(z, b, phase, False)
                if report['witnesses']:
                    break
            report['phases'][phase] = 'stopped after witness' if report['witnesses'] else 'complete'
except TimeoutError:
    report['phases'][phase] = 'partial: time budget reached'
report['completed_parent_inspections'] = len(seen)
report['elapsed_seconds'] = round(time.monotonic() - start, 3)
if report['witnesses']:
    report['summary'] = 'Exact parent and child certificates found. The origin field distinguishes input transcription from a bounded numerical match.'
elif any(v.startswith('partial') for v in report['phases'].values()):
    report['summary'] = 'No certified witness in the completed work. The named partial phase was interrupted.'
else:
    report['summary'] = 'No matching descent witness in the completed domains listed under phases.'
with open('result.json', 'w') as f:
    json.dump(report, f)
