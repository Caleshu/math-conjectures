# MathResearchLab experiment c6c41e8a-cac7-422d-8291-49649029d9ee
# Exhaustive census through $S_6$
# sha256(code) = 963de9bb3a0f41cd0a2c7e9ea87c2a97d61893fcd557cd54d67725f584b7ddc3
# parameters: {"m_max": 6, "seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from itertools import permutations
from math import factorial

params = json.load(open(os.environ['MRL_PARAMS']))
limit = int(params.get('m_max', 6))
assert 4 <= limit <= 6
deadline = time.monotonic() + min(105, float(params.get('seconds', 95)))

def inversions(p):
    return sum(a > b for i, a in enumerate(p) for b in p[i+1:])

def swap(p, i, j):
    a = list(p)
    a[i], a[j] = a[j], a[i]
    return tuple(a)

def cycle_count(x, w):
    inverse = {a: i for i, a in enumerate(x)}
    rel = [inverse[b] for b in w]
    seen = set()
    c = 0
    for i in range(len(x)):
        if i not in seen:
            c += 1
            while i not in seen:
                seen.add(i)
                i = rel[i]
    return c

def uncompressible(x, w):
    for i, j in enumerate(x):
        if w[i] == j and sum(b >= j for b in x[:i]) == sum(b >= j for b in w[:i]):
            return False
    return True

def indices(bits):
    while bits:
        low = bits & -bits
        yield low.bit_length() - 1
        bits ^= low

def add_shifted(total, poly, shift, scale=1):
    if poly:
        need = len(poly) + shift - len(total)
        if need > 0:
            total.extend([0] * need)
        for k, coefficient in enumerate(poly):
            total[k + shift] += scale * coefficient

def coefficient(poly, k):
    return poly[k] if k < len(poly) else 0

def census(m, report):
    perms = sorted(permutations(range(m)), key=inversions)
    index = {p: i for i, p in enumerate(perms)}
    length = [inversions(p) for p in perms]
    down = []
    covers = []
    columns = []
    simple = [[index[swap(p, s, s+1)] for s in range(m-1)] for p in perms]

    def connected(a, b):
        components = list(range(m))
        while b != a:
            for v, i, j in covers[b]:
                if (down[v] >> a) & 1:
                    old, new = components[j], components[i]
                    if old != new:
                        components = [new if t == old else t for t in components]
                    b = v
                    break
            else:
                raise AssertionError('missing chain step')
        return len(set(components)) == 1

    for b, w in enumerate(perms):
        if time.monotonic() >= deadline:
            return False
        pred = []
        bits = 1 << b
        for i in range(m):
            for j in range(i+1, m):
                if w[i] > w[j]:
                    v = index[swap(w, i, j)]
                    if length[v] == length[b] - 1:
                        pred.append((v, i, j))
                        bits |= down[v]
        covers.append(pred)
        down.append(bits)
        col = {b: (1,)}
        if b:
            s = next(i for i in range(m-1) if w[i] > w[i+1])
            v = simple[b][s]
            corrections = []
            for z, poly in columns[v].items():
                gap = length[v] - length[z]
                if gap % 2 and perms[z][s] > perms[z][s+1]:
                    mu = coefficient(poly, (gap-1)//2)
                    if mu:
                        corrections.append((z, (gap+1)//2, mu))
            for a in indices(bits ^ (1 << b)):
                asc = int(perms[a][s] < perms[a][s+1])
                total = []
                add_shifted(total, columns[v].get(simple[a][s], ()), asc)
                add_shifted(total, columns[v].get(a, ()), 1-asc)
                for z, shift, mu in corrections:
                    add_shifted(total, columns[z].get(a, ()), shift, -mu)
                while total and total[-1] == 0:
                    total.pop()
                d = length[b] - length[a]
                assert total and total[0] == 1 and min(total) >= 0
                assert 2*(len(total)-1) < d
                col[a] = tuple(total)
        columns.append(col)
        for a, poly in col.items():
            x = perms[a]
            d = length[b] - length[a]
            if d % 2 == 0 or not uncompressible(x, w):
                continue
            c = cycle_count(x, w)
            if d != m+c-2 or not connected(a, b):
                continue
            value = coefficient(poly, (d-1)//2)
            bucket = report['histogram'].setdefault(f'd={d},c={c}', {})
            key = str(value)
            bucket[key] = bucket.get(key, 0) + 1
            if value > 1 and len(report['counterexamples']) < 5:
                report['counterexamples'].append({'x': [t+1 for t in x], 'w': [t+1 for t in w], 'd': d, 'c': c, 'P_low_to_high': poly})
        report['upper_endpoints_finished'] += 1
    assert all(poly == (1,) for poly in columns[-1].values())
    assert len(columns[-1]) == factorial(m)
    if m == 4:
        x, w = (0,2,1,3), (2,3,0,1)
        a, b = index[x], index[w]
        assert columns[b][a] == (1,1) and length[b]-length[a] == 3
        assert cycle_count(x,w) == 1 and uncompressible(x,w) and connected(a,b)
        assert columns[b][0] == (1,1)
        assert not connected(0, index[(1,0,3,2)])
        assert not uncompressible(perms[0], (1,0,2,3))
    return True

reports = []
for m in range(1, limit+1):
    report = {'m': m, 'upper_endpoints_total': factorial(m), 'upper_endpoints_finished': 0, 'histogram': {}, 'counterexamples': []}
    reports.append(report)
    report['complete'] = census(m, report)
    if not report['complete']:
        break
finished = [r['m'] for r in reports if r['complete']]
found = any(r['counterexamples'] for r in reports)
result = {'summary': f'Complete ranks {finished}. Counterexample among processed intervals: {found}.', 'ranks': reports, 'sanity_S4_passed': 4 in finished, 'author_support': 'proved_here', 'justification': 'Within each finished upper endpoint, downward closure under all inversion-difference-one transpositions enumerates every lower endpoint. Induction on upper length computes each column by the ordinary right-descent KL recurrence, starting with diagonal entries 1 and incomparable entries 0. The filters use the endpoint definitions and the edge components of one saturated chain. The supplied chain-independence property makes this connectivity test sufficient. Each qualifying pair contributes once.'}
with open('result.json', 'w') as out:
    json.dump(result, out)
