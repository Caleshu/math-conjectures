# MathResearchLab experiment 7ad39206-ad3b-4640-828f-cae6d8820eac
# Exact descent and coefficient test for the Table 20 rows
# sha256(code) = a782e86530ae76ee27360d038ccea838c161a9c0b1093351215281f30a501547
# parameters: {"x": null, "w": null}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from functools import lru_cache
from itertools import combinations

params = json.load(open(os.environ['MRL_PARAMS']))
deadline = time.monotonic() + 95

class Limit(Exception):
    pass

def check_time():
    if time.monotonic() >= deadline:
        raise Limit('95-second internal time limit')

def swap(p, i, j):
    row = list(p)
    row[i], row[j] = row[j], row[i]
    return tuple(row)

@lru_cache(maxsize=32768)
def length(p):
    return sum(a > b for a, b in combinations(p, 2))

@lru_cache(maxsize=32768)
def leq(a, b):
    # Each sorted prefix of a is componentwise at most the same prefix of b.
    return all(all(i <= j for i, j in zip(sorted(a[:k]), sorted(b[:k])))
               for k in range(1, len(a)))

def covers(p, direction):
    for i, j in combinations(range(len(p)), 2):
        a, b = p[i], p[j]
        if direction * (b - a) <= 0:
            continue
        low, high = sorted((a, b))
        if not any(low < t < high for t in p[i + 1:j]):
            yield i, j, swap(p, i, j)

def geometry(x, w):
    assert leq(x, w)
    n = len(x)
    rel = tuple(x.index(v) for v in w)
    unused = set(range(n))
    cycles = []
    while unused:
        i = min(unused)
        cycle = []
        while i in unused:
            unused.remove(i)
            cycle.append(i)
            i = rel[i]
        cycles.append(cycle)
    components = [{i} for i in range(n)]
    labels = []
    p = x
    while p != w:
        check_time()
        i, j, p = next(edge for edge in covers(p, 1) if leq(edge[2], w))
        labels.append([i, j])
        left = next(part for part in components if i in part)
        right = next(part for part in components if j in part)
        if left is not right:
            components.remove(right)
            left.update(right)
    d = length(w) - length(x)
    assert len(labels) == d
    return {'m': n, 'd': d, 'relative_cycles': cycles,
            'chain_position_swaps': labels, 'components': [sorted(s) for s in components],
            'connected': len(components) == 1, 'd_minus_m_minus_c_plus_2': d - n - len(cycles) + 2}

def flatten(x, w):
    deletions = []
    while True:
        for i, j in enumerate(x):
            if w[i] != j:
                continue
            left = sum(v >= j for v in x[:i])
            right = sum(v >= j for v in w[:i])
            if left == right:
                deletions.append({'current_position': i, 'current_value': j, 'equal_prefix_count': left})
                x = tuple(v - int(v > j) for v in x if v != j)
                w = tuple(v - int(v > j) for v in w if v != j)
                break
        else:
            return x, w, deletions

def below(top, bottom):
    # Enumerate [bottom,top) by downward covers, pruning below the lower bound.
    if not leq(bottom, top):
        return
    todo = [top]
    seen = {top}
    while todo:
        check_time()
        p = todo.pop()
        for _, _, z in covers(p, -1):
            if z not in seen and leq(bottom, z):
                if len(seen) >= 25000:
                    raise Limit('25000 vertices in one recurrence interval')
                seen.add(z)
                todo.append(z)
                yield z

def accumulate(out, poly, shift, factor):
    for i, v in enumerate(poly):
        out[i + shift] += factor * v

@lru_cache(maxsize=65536)
def kl(a, b):
    # Ordinary right-descent KL recurrence. Coefficients are in ascending degree.
    check_time()
    if not leq(a, b):
        return ()
    d = length(b) - length(a)
    if d <= 2:
        return (1,)
    i = next(i for i in range(len(b) - 1) if b[i] > b[i + 1])
    bs = swap(b, i, i + 1)
    asc = a[i] < a[i + 1]
    a_s = swap(a, i, i + 1)
    out = [0] * (d + 2)
    accumulate(out, kl(a_s, bs), int(asc), 1)
    accumulate(out, kl(a, bs), int(not asc), 1)
    for z in below(bs, a):
        gap = length(bs) - length(z)
        if gap % 2 == 0 or z[i] < z[i + 1]:
            continue
        poly = kl(z, bs)
        h = (gap - 1) // 2
        if h < len(poly) and poly[h]:
            accumulate(out, kl(a, z), h + 1, -poly[h])
    while out and out[-1] == 0:
        out.pop()
    assert out and out[0] == 1 and len(out) - 1 <= (d - 1) // 2
    return tuple(out)

def simple(p, side, i):
    if side == 'right':
        return swap(p, i, i + 1)
    return swap(p, p.index(i), p.index(i + 1))

def children(x, w):
    checks = []
    candidates = {}
    for side in ('right', 'left'):
        for i in range(len(x) - 1):
            y = simple(x, side, i)
            ws = simple(w, side, i)
            raises = length(y) == length(x) + 1
            lowers = length(ws) == length(w) - 1
            checks.append({'side': side, 'i': i, 'raises_lower': raises, 'lowers_upper': lowers})
            if raises and lowers:
                assert leq(y, w)
                candidates.setdefault(y, []).append([side, i])
    return checks, candidates

def normalize(row):
    if not isinstance(row, list) or len(row) != 10 or any(type(i) is not int for i in row):
        raise ValueError('Each endpoint must be an array of ten integers.')
    base = min(row)
    if base not in (0, 1) or sorted(row) != list(range(base, base + 10)):
        raise ValueError('Each row must permute 0 through 9 or 1 through 10.')
    return tuple(i - base for i in row), base

def investigate(out):
    # The S4 singular interval checks a positive top coefficient and left/right conventions.
    e = (0, 1, 2, 3)
    b = (2, 3, 0, 1)
    a = (0, 2, 1, 3)
    assert children(e, b)[1] == {a: [['right', 1], ['left', 1]]}
    assert kl(a, b) == (1, 1)
    assert geometry(a, b)['connected'] and geometry(a, b)['d_minus_m_minus_c_plus_2'] == 0
    assert kl((0, 1, 2), (2, 1, 0)) == (1,)
    insert_min = lambda p: (0,) + tuple(v + 1 for v in p)
    assert flatten(insert_min(a), insert_min(b))[:2] == (a, b)
    out['sanity_checks'] = 'passed'
    if params.get('x') is None or params.get('w') is None:
        out.update(status='missing_source_rows', summary='Both Table 20 endpoint rows are needed to decide the requested case.')
        return
    x, bx = normalize(params['x'])
    w, bw = normalize(params['w'])
    if bx != bw or not leq(x, w):
        raise ValueError('Rows must use the same base and satisfy Bruhat comparability.')
    out.update(input_rows={'x': params['x'], 'w': params['w']}, index_convention='All certificate positions and standardized values are zero-based.')
    parent = geometry(x, w)
    out['parent'] = parent
    if parent['d'] != 10 or not parent['connected'] or parent['d_minus_m_minus_c_plus_2'] != 0:
        out.update(status='parent_signature_mismatch', summary='The supplied rows fail the recorded length, connectivity, or genus condition. Check the transcription.')
        return
    checks, candidates = children(x, w)
    out.update(simple_moves=checks, children=[])
    for y, moves in candidates.items():
        lo, hi, deletions = flatten(y, w)
        g = geometry(lo, hi)
        record = {'moves': moves, 'child_lower': y, 'deletions': deletions, 'flat_x': lo, 'flat_w': hi, 'geometry': g}
        out['children'].append(record)
        assert g['d'] == 9
        accepted = g['connected'] and g['d_minus_m_minus_c_plus_2'] == 0
        record['geometrically_accepted'] = accepted
        if accepted:
            p = kl(lo, hi)
            record.update(KL_low_to_high=p, q4=p[4] if len(p) > 4 else 0)
            if record['q4'] >= 2:
                out.update(status='witness', summary='The recorded move, deletion trace, saturated chain, and directly computed child polynomial certify a witness for the supplied rows.')
                return
    out.update(status='exhausted_for_supplied_rows', summary='Every simple move for the supplied rows was classified. None yields the requested witness.')

result = {}
try:
    investigate(result)
except Limit as err:
    result.update(status='partial', summary=str(err) + '. The decision is incomplete.')
except ValueError as err:
    result.update(status='invalid_input', summary=str(err))
with open('result.json', 'w') as f:
    json.dump(result, f)
