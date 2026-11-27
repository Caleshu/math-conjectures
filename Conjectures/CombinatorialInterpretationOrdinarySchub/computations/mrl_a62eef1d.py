# MathResearchLab experiment a62eef1d-4b68-49d6-a94a-0156c352887a
# Weighted Hall test for adjacent coordinate swaps in $S_4$
# sha256(code) = d2b609be34a8e5c283ae4cda834a96cb8397a65e461969b239d251a4c4a6b830
# parameters: {"n": 4, "seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from collections import Counter
from functools import cache
from itertools import combinations_with_replacement, permutations
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
n = params['n']
assert n == 4
start = monotonic()
limit = min(90, params.get('seconds', 90))
perms = list(permutations(range(1, n + 1)))
identity = perms[0]
longest = perms[-1]
delta = tuple(range(n - 1, -1, -1))
zero = (0,) * n

def length(p):
    return sum(x > y for i, x in enumerate(p) for y in p[i + 1:])

def swap(p, i):
    return p[:i] + (p[i + 1], p[i]) + p[i + 2:]

@cache
def words(p):
    if p == identity:
        return ((),)
    return tuple(a + (i + 1,) for i in range(n - 1) if p[i] > p[i + 1]
                 for a in words(swap(p, i)))

def compatible_polynomial(p):
    poly = Counter()
    for a in words(p):
        for b in combinations_with_replacement(range(1, n), len(a)):
            if any(j > k for j, k in zip(b, a)):
                continue
            if any(a[i] < a[i + 1] and b[i] == b[i + 1] for i in range(len(a) - 1)):
                continue
            poly[tuple(b.count(j) for j in range(1, n + 1))] += 1
    return poly

def divided_difference(poly, i):
    out = Counter()
    for exponent, coeff in poly.items():
        a, b = exponent[i:i + 2]
        for k in range(min(a, b), max(a, b)):
            term = exponent[:i] + (k, a + b - 1 - k) + exponent[i + 2:]
            out[term] += coeff if a > b else -coeff
    return {e: c for e, c in out.items() if c}

@cache
def from_longest(p):
    if p == longest:
        return {delta: 1}
    i = next(i for i in range(n - 1) if p[i] < p[i + 1])
    return divided_difference(from_longest(swap(p, i)), i)

polys = {p: compatible_polynomial(p) for p in perms}
assert all(dict(polys[p]) == from_longest(p) for p in perms)

def multiply(f, g):
    result = Counter()
    for a, c in f.items():
        for b, d in g.items():
            result[tuple(x + y for x, y in zip(a, b))] += c * d
    return result

weights = list(permutations(delta))
def odd(t):
    return sum(x < y for i, x in enumerate(t) for y in t[i + 1:]) % 2

negative = [t for t in weights if odd(t)]
positive = [t for t in weights if not odd(t)]
assert delta in positive and len(positive) == len(negative) == 12
neighbors = [sum(1 << positive.index(swap(t, i)) for i in range(n - 1)) for t in negative]

def members(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit

def hall_witness(neg, pos):
    active = [i for i, c in enumerate(neg) if c]
    best = None
    # Visit each nonempty subset of occupied odd weights exactly once.
    def visit(first, chosen, neighborhood, demand):
        nonlocal best
        for k in range(first, len(active)):
            i = active[k]
            new_demand = demand + neg[i]
            if best is not None and new_demand > best[0]:
                continue
            left = chosen | (1 << i)
            right = neighborhood | neighbors[i]
            supply = sum(pos[j] for j in members(right))
            if supply < new_demand:
                candidate = (new_demand, left.bit_count(), supply, left, right)
                if best is None or candidate < best:
                    best = candidate
            else:
                visit(k + 1, left, right, new_demand)
    visit(0, 0, 0, 0)
    return best

# The first synthetic graph needs two positive copies at one neighbor. Moving
# one copy to a nonneighbor preserves the signed total but violates Hall.
probe_neg = [2] + [0] * 11
probe_pos = [0] * 12
j = next(members(neighbors[0]))
probe_pos[j] = 2
assert hall_witness(probe_neg, probe_pos) is None
probe_pos[j] = 1
probe_pos[next(k for k in range(12) if not (neighbors[0] >> k) & 1)] = 1
assert hall_witness(probe_neg, probe_pos)[:3] == (2, 1, 1)

def factor_terms(p):
    return [{'exponent': e, 'multiplicity': c} for e, c in sorted(polys[p].items())]

lengths = {p: length(p) for p in perms}
triples = [(u, v, w) for u in perms for v in perms for w in perms
           if lengths[u] + lengths[v] == lengths[w]]
assert len(triples) == 1115
best_key = None
witness = None
tested = failures = 0
for u, v, w in triples:
    if monotonic() - start >= limit:
        break
    dual = tuple(n + 1 - x for x in w)
    uv = multiply(polys[u], polys[v])
    product = multiply(uv, polys[dual])
    neg = [product[t] for t in negative]
    pos = [product[t] for t in positive]
    # Independent coefficient extraction by stripping right descents of w.
    extracted = uv
    for letter in reversed(words(w)[0]):
        extracted = divided_difference(extracted, letter - 1)
    assert set(extracted) <= {zero}
    assert sum(pos) - sum(neg) == extracted.get(zero, 0)
    tested += 1
    violation = hall_witness(neg, pos)
    if violation is None:
        continue
    failures += 1
    demand, types, supply, left, right = violation
    key = (demand, types, sum(len(polys[p]) for p in (u, v, dual)), supply, u, v, w)
    if best_key is not None and key >= best_key:
        continue
    best_key = key
    left_weights = [negative[i] for i in members(left)]
    right_weights = sorted({swap(t, i) for t in left_weights for i in range(n - 1)})
    assert set(right_weights) == {positive[j] for j in members(right)}
    assert sum(product[t] for t in right_weights) == supply < demand == sum(product[t] for t in left_weights)
    def counts(ts):
        return [{'weight': t, 'multiplicity': product[t]} for t in ts]
    witness = {'u': u, 'v': v, 'w': w, 'w0w': dual,
               'negative_set': counts(left_weights), 'all_adjacent_even_weights': counts(right_weights),
               'negative_vertices': demand, 'positive_neighbors': supply, 'deficiency': demand - supply,
               'all_odd_weights': counts(negative), 'all_even_weights': counts(positive),
               'signed_total': sum(pos) - sum(neg),
               'factor_terms_in_order_u_v_w0w': [factor_terms(p) for p in (u, v, dual)]}

complete = tested == len(triples)
result = {'summary': f'Checked {tested} of {len(triples)} degree-compatible ordered triples in S_4. Hall failed on {failures} tested triples.',
          'complete': complete, 'tested': tested, 'eligible': len(triples), 'failures': failures,
          'matching_method': 'Exact integer enumeration of weighted Hall subsets with pruning.',
          'author_support': 'proved_here',
          'justification': 'All copies of one odd weight have the same neighbors. Enlarging any deficient vertex set to include every copy of its represented weights preserves its neighbors and increases or preserves its size. Thus a failure has a witness among the enumerated weight subsets. Every occupied weight has positive multiplicity, so pruning supersets of a deficient set or branches exceeding the best demand preserves the minimum witness size.',
          'sanity_checks': {'factor_polynomials_checked_against_divided_differences': len(perms),
                            'signed_totals_checked_by_coefficient_extraction': tested,
                            'synthetic_matching_cases_passed': 2}, 'witness': witness}
with open('result.json', 'w') as output:
    json.dump(result, output)
