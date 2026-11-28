# MathResearchLab experiment 126f8d17-ca2d-425a-9c06-a4c83ac5f213
# Exact KL recurrence for the specified pair
# sha256(code) = e80fcbcd191917fe83e207228a291bc0e27cff002abf710045a29b8902afce4a
# parameters: {"a": [4, 3, 2, 1, 6, 5, 10, 9, 8, 7], "v": [10, 4, 3, 2, 6, 5, 9, 8, 7, 1]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from functools import cache
from itertools import combinations
from time import monotonic

params = json.load(open(os.environ["MRL_PARAMS"]))
deadline = monotonic() + 90

def check_time():
    if monotonic() >= deadline:
        raise TimeoutError

@cache
def length(p):
    return sum(b < a for k, a in enumerate(p) for b in p[k + 1:])

@cache
def prefix_signature(p):
    return tuple(x for k in range(1, len(p)) for x in sorted(p[:k]))

def below(p, q):
    return all(i <= j for i, j in zip(prefix_signature(p), prefix_signature(q)))

def left_swap(p, i):
    q = list(p)
    j, k = p.index(i), p.index(i + 1)
    q[j], q[k] = q[k], q[j]
    return tuple(q)

def evaluate(bottom, top, sizes):
    ends = [0]
    for size in sizes:
        ends.append(ends[-1] + size)
    blocks = list(zip(ends, ends[1:]))
    block_at = [b for b, size in enumerate(sizes) for _ in range(size)]

    def normalize(p):
        return tuple(x for j, k in blocks for x in sorted(p[j:k], reverse=True))

    def representatives(rest, b=0):
        if b == len(sizes) - 1:
            yield tuple(reversed(rest))
            return
        for chosen in combinations(rest, sizes[b]):
            remaining = tuple(x for x in rest if x not in chosen)
            for tail in representatives(remaining, b + 1):
                yield chosen[::-1] + tail

    assert normalize(top) == top and normalize(bottom) == bottom and below(bottom, top)
    pool = []
    for z in representatives(tuple(range(1, len(top) + 1))):
        check_time()
        if below(z, top):
            pool.append(z)

    @cache
    def corrections(y, i, u):
        terms = []
        for z in pool:
            check_time()
            g = length(u) - length(z)
            if g <= 0 or g % 2 == 0 or z.index(i) < z.index(i + 1) or not below(z, u):
                continue
            mu = polynomial(z, u)[(g - 1) // 2]
            if mu:
                terms.append((z, (length(y) - length(z)) // 2, mu))
        return terms

    @cache
    def polynomial(x, y):
        check_time()
        if x == y:
            return (1,)
        if not below(x, y):
            return ()
        i = next(i for i in range(1, len(y)) if block_at[y.index(i)] > block_at[y.index(i + 1)])
        u = left_swap(y, i)
        assert normalize(u) == u and length(u) == length(y) - 1
        c = int(x.index(i) > x.index(i + 1))
        gap = length(y) - length(x)
        coeff = [0] * (gap + 2)

        def add(poly, shift, factor):
            for k, value in enumerate(poly):
                coeff[k + shift] += factor * value

        add(polynomial(normalize(left_swap(x, i)), u), 1 - c, 1)
        add(polynomial(x, u), c, 1)
        for z, shift, mu in corrections(y, i, u):
            if below(x, z):
                add(polynomial(x, z), shift, -mu)
        degree_bound = (gap - 1) // 2
        assert coeff[0] == 1 and not any(coeff[degree_bound + 1:])
        return tuple(coeff[:degree_bound + 1])

    return polynomial(bottom, top), len(pool)

result = {'summary': 'Time budget reached before an exact target decision.', 'status': 'incomplete'}
try:
    # Singleton blocks give the ordinary recurrence with no parabolic reduction.
    # The second evaluation exercises the block reduction on the same singular interval.
    small = ((2, 1, 4, 3), (4, 2, 3, 1))
    ordinary, _ = evaluate(*small, (1, 1, 1, 1))
    reduced, _ = evaluate(*small, (2, 2))
    assert ordinary == reduced == (1, 1)
    result['sanity'] = {'ordinary_S4': ordinary, 'block_reduced_S4': reduced}
    a, v = tuple(params['a']), tuple(params['v'])
    assert len(a) == len(v) == 10 and sorted(a) == sorted(v) == list(range(1, 11))
    assert length(v) - length(a) == 11
    poly, count = evaluate(a, v, (4, 2, 4))
    mu = poly[5]
    result.update(status='exact', summary=f'The specified pair has coefficient {mu} at q^5. Threshold met: {mu >= 5}.', a=a, v=v, lengths=[length(a), length(v)], coefficients_low_to_high=poly, coefficient_q5=mu, threshold_met=(mu >= 5), block_representatives_below_v=count)
except TimeoutError:
    pass
with open('result.json', 'w') as f:
    json.dump(result, f)
