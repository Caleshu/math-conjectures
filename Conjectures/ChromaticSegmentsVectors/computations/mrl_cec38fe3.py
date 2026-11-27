# MathResearchLab experiment cec38fe3-1c03-4e36-8695-2b8059533d13
# Exact classification by the two unused crossing coordinates
# sha256(code) = 8a43ee4342491a60f8c7206cd4901febe0aaaea31ad74d9277d97614d94ed0d3
# parameters: {"seconds": 85}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from itertools import combinations, product

params = json.load(open(os.environ['MRL_PARAMS']))
deadline = time.monotonic() + min(95.0, float(params.get('seconds', 85)))

def check_time():
    if time.monotonic() >= deadline:
        raise TimeoutError

def orbit(g, step=1):
    return {s[k:] + s[:k] for s in (g, g[::-1]) for k in range(0, 14, step)}

def canon(g):
    return min(orbit(tuple(g)))

def halves():
    for a in range(7):
        h = [2] * 7
        h[a] = 4
        yield h
    for a, b in combinations(range(7), 2):
        h = [2] * 7
        h[a] = h[b] = 3
        yield h

def cycle_gaps(h):
    assert len(h) == 32 and set(h) == set(range(32))
    assert h[0] < 16 and h[0] ^ h[1] == 16
    edges = [h[k] ^ h[(k + 1) % 32] for k in range(32)]
    assert all(e in (1, 2, 4, 8, 16) for e in edges)
    starts = [k for k, e in enumerate(edges) if e == 16]
    return tuple(b - a for a, b in zip(starts, starts[1:] + [32]))

def boundary_colour_counts(g):
    colour = 0
    counts = [0, 0]
    for length in g:
        counts[colour] += 1
        colour ^= (length - 1) % 2
    assert colour == 0
    return counts

# For fixed interior labels, row a of this relation is the bitset of
# possible next crossing labels b. All endpoints must belong to B.
def relation(inner, B):
    rows = [0] * 16
    for a in range(16):
        if not (B >> a & 1):
            continue
        for b in range(16):
            if a == b or not (B >> b & 1):
                continue
            walk = (a,) + inner + (b,)
            if all((x ^ y).bit_count() == 1 for x, y in zip(walk, walk[1:])):
                rows[a] |= 1 << b
    return rows

def paths(start, relations):
    def visit(path, used):
        depth = len(path) - 1
        if depth == len(relations):
            yield path, used
            return
        options = relations[depth][path[-1]] & ~used
        while options:
            bit = options & -options
            options ^= bit
            yield from visit(path + (bit.bit_length() - 1,), used | bit)
    yield from visit((start,), 1 << start)

def lift(boundary, interiors):
    h = []
    for k, x in enumerate(boundary):
        before = (k % 2) * 16
        after = before ^ 16
        h.extend((before | x, after | x))
        h.extend(after | y for y in interiors[k])
    return h

def try_assignment(g, v, odd_order):
    # The even-index gaps use 0 then v as their two interior occurrences.
    # The odd-index gaps can use them in either order.
    B = 65535 ^ 1 ^ (1 << v)
    orders = [iter((0, v)), iter(odd_order)]
    interiors = [tuple(next(orders[k % 2]) for _ in range(length - 2))
                 for k, length in enumerate(g)]
    forward = [relation(s, B) for s in interiors[:7]]
    backward = [relation(s[::-1], B) for s in reversed(interiors[7:])]
    audit = {'omitted': [0, v], 'odd_order': odd_order,
             'forward_endpoint_mask_keys': 0, 'backward_endpoint_mask_keys': 0,
             'complementary_key_found': False}
    for start in range(16):
        check_time()
        if not (B >> start & 1):
            continue
        left = {(p[-1], mask): p for p, mask in paths(start, forward)}
        right = {(p[-1], mask): p for p, mask in paths(start, backward)}
        audit['forward_endpoint_mask_keys'] += len(left)
        audit['backward_endpoint_mask_keys'] += len(right)
        for (end, mask), back in right.items():
            target = (B ^ mask) | (1 << start) | (1 << end)
            front = left.get((end, target))
            if front is not None:
                boundary = front + back[-2:0:-1]
                assert len(set(boundary)) == len(boundary) == 14
                h = lift(boundary, interiors)
                assert cycle_gaps(h) == g
                audit['complementary_key_found'] = True
                return h, audit
    return None, audit

def classify(g):
    counts = boundary_colour_counts(g)
    if counts != [7, 7]:
        return {'gaps': g, 'status': 'INFEASIBLE', 'boundary_colour_counts': counts}
    audits = []
    for v in (1, 7):
        for order in ((0, v), (v, 0)):
            h, audit = try_assignment(g, v, order)
            audits.append(audit)
            if h is not None:
                return {'gaps': g, 'status': 'FEASIBLE', 'cycle': h}
    return {'gaps': g, 'status': 'INFEASIBLE', 'boundary_colour_counts': counts,
            'exhausted_assignments': audits,
            'even_rotation_and_reversal_representatives': sorted({min(orbit(s, 2)) for s in orbit(g)})}

halflists = list(halves())
raw = {tuple(x for pair in zip(a, b) for x in pair) for a, b in product(halflists, repeat=2)}
classes = sorted({canon(g) for g in raw})
assert len(raw) == 784 and sum(len(orbit(g)) for g in classes) == 784
assert all(s in raw for g in classes for s in orbit(g))

# Independently validate the supplied control cycle, then require the search
# to construct a witness for its class using only the canonical gap list.
control = [0,16,17,19,18,2,3,1,5,21,20,4,6,22,23,7,15,31,30,14,12,28,29,13,9,25,27,11,10,26,24,8]
control_g = canon(cycle_gaps(control))
assert control_g == canon((4, 4) + (2,) * 12) and control_g in classes
run_order = [control_g] + [g for g in classes if g != control_g]
rows = []
for index, g in enumerate(run_order):
    try:
        check_time()
        row = classify(g)
    except TimeoutError:
        rows.extend({'gaps': s, 'status': 'UNKNOWN'} for s in run_order[index:])
        break
    if g == control_g:
        assert row['status'] == 'FEASIBLE' and cycle_gaps(row['cycle']) == control_g
    rows.append(row)

complete = all(r['status'] != 'UNKNOWN' for r in rows)
feasible = [r for r in rows if r['status'] == 'FEASIBLE']
missing = [r for r in rows if 'exhausted_assignments' in r]
balanced_count = sum(boundary_colour_counts(g) == [7, 7] for g in classes)
predicted = canon((3,2,3,2,2,2,2,4,2,2,2,2,2,2))
old_missing = sorted({s for r in missing for s in r['even_rotation_and_reversal_representatives']})
result = {
    'summary': ('Complete exact classification.' if complete else 'Partial classification. UNKNOWN classes are unresolved.'),
    'scope': 'Q5, coordinate bit 16, exactly 14 crossings, full rotations and reversal',
    'method': 'Exact finite path enumeration. Status labels report search outcomes.',
    'control_search_passed': rows[0]['status'] == 'FEASIBLE',
    'ordered_half_sum_candidates': len(raw), 'full_dihedral_candidates': len(classes),
    'parity_balanced_classes': balanced_count, 'certified_feasible_classes': len(feasible),
    'certified_balanced_exclusions': [r['gaps'] for r in missing],
    'certified_balanced_exclusions_even_rotations_and_reversal': old_missing,
    'unknown_count': sum(r['status'] == 'UNKNOWN' for r in rows),
    'prediction_confirmed': (balanced_count == 30 and len(feasible) == 29 and
                             [r['gaps'] for r in missing] == [predicted] and len(old_missing) == 2) if complete else None,
    'author_support': 'proved_here',
    'justification': [
        'Fix the fifth coordinate by coordinate permutation. A cyclic shift of the list is obtained by starting at the corresponding crossing and flipping the fifth bit if needed. Reversing traversal about the first crossing reverses the gap list, again allowing a fifth-bit flip. These operations justify full dihedral reduction.',
        'Deleting the crossing edges leaves seven paths in each layer. A gap of length $d$ contributes $d$ vertices to its path, including two distinct ends. In each layer the seven lengths sum to 16, so their excesses over two sum to two. This gives seven choices for a single 4 or 21 choices for two 3s.',
        'The 14 crossing labels in the projected $Q_4$ are distinct, since using one twice would repeat the same crossing edge. Their set $B$ is exactly the endpoint set in each layer. The other two projected labels occur once each as path interiors in each layer. In a layer the path edges have equal degree sums on the two cube colours. Each colour has eight vertices, of degree two except for the crossing labels of degree one. Thus $B$ has seven labels of each colour. The boundary colour changes across a gap of length $d$ by $(d-1)\\bmod 2$, which proves the list-only parity test.',
        'The two omitted labels consequently have opposite colours. Translate the first interior label in even-index gaps to zero, then permute the four projected coordinates. The second label becomes 1 or 7, according as its Hamming weight is one or three. Both possible orders in odd-index gaps are tested. This exhausts interior assignments up to cube symmetries.',
        'For a fixed assignment each relation checks every required horizontal edge through the specified interiors. Two simple seven-step paths, one traversing each arc from crossing 0 to crossing 7, form a valid boundary sequence exactly when they agree at their ends and their other six labels on each side are disjoint. The complementary-mask lookup tests precisely this equality. Keeping one path per endpoint and mask preserves every possible join. A join lifts by crossing at each boundary and following the assigned interiors. Every returned lift is checked for all 32 vertices, all 32 edges including closure, normalization, and the exact ordered gaps.'
    ],
    'classes': sorted(rows, key=lambda r: r['gaps'])
}
with open('result.json', 'w') as output:
    json.dump(result, output)
