# MathResearchLab experiment 72e0c49c-c5a5-4b15-a535-afaca95f996d
# Can two consecutive changes cancel every negative pipe-dream chain?
# sha256(code) = da4755d73a9ab9295611161ba7a87e375f8efbaa503689a488188ca2ab6cce2c
# parameters: {"seconds": 85, "ranges": [{"n": 4, "u_max": 6, "v_max": 6}, {"n": 5, "u_max": 3, "v_max": 3}]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from collections import Counter, defaultdict, deque
from functools import cache
from itertools import permutations
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
start = monotonic()
deadline = start + min(95, params.get('seconds', 85))


def swap(p, a, b):
    q = list(p)
    q[a], q[b] = q[b], q[a]
    return tuple(q)


def length(p):
    return sum(x > y for j, x in enumerate(p) for y in p[j + 1:])


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


@cache
def dd_terms(alpha, j):
    # Terms of (x^alpha - s_j x^alpha)/(x_j - x_{j+1}).
    a, b = alpha[j:j + 2]
    sign = 1 if a > b else -1
    terms = []
    for t in range(abs(a - b)):
        beta = list(alpha)
        beta[j:j + 2] = [max(a, b) - 1 - t, min(a, b) + t]
        terms.append((tuple(beta), sign))
    return tuple(terms)


@cache
def schubert(p):
    n = len(p)
    for j in range(n - 1):
        if p[j] < p[j + 1]:
            poly = Counter()
            for alpha, coeff in schubert(swap(p, j, j + 1)).items():
                for beta, sign in dd_terms(alpha, j):
                    poly[beta] += coeff * sign
            return {a: c for a, c in poly.items() if c}
    return {tuple(reversed(range(n))): 1}


@cache
def extract(w, alpha):
    # Strip right descents of w. In degree length(w) this functional
    # is 1 on S_w and 0 on every other Schubert basis element.
    for j in range(len(w) - 1):
        if w[j] > w[j + 1]:
            shorter = swap(w, j, j + 1)
            return sum(sign * extract(shorter, beta) for beta, sign in dd_terms(alpha, j))
    return int(not any(alpha))


def polynomial_product(p, q):
    result = Counter()
    for a, c in schubert(p).items():
        for b, d in schubert(q).items():
            result[tuple(x + y for x, y in zip(a, b))] += c * d
    return result


def pipe_dreams(n):
    # One-based cells, top row first, right to left within each row.
    cells = [(r, c) for r in range(1, n) for c in range(n - r, 0, -1)]
    identity = tuple(range(1, n + 1))
    groups = defaultdict(list)
    for mask in range(1 << len(cells)):
        p = identity
        chosen = []
        for bit, (r, c) in enumerate(cells):
            if mask & (1 << bit):
                j = r + c - 2
                if p[j] > p[j + 1]:
                    break
                p = swap(p, j, j + 1)
                chosen.append((r, c))
        else:
            groups[p].append(tuple(chosen))
    return groups


@cache
def covers(p, row):
    edges = []
    for a in range(len(p)):
        for b in range(a + 1, len(p)):
            if row not in (a + 1, b + 1) or p[a] >= p[b]:
                continue
            if any(p[a] < x < p[b] for x in p[a + 1:b]):
                continue
            edges.append((a + 1, b + 1, swap(p, a, b), 1 if row == a + 1 else -1))
    return tuple(edges)


def signed_objects(dreams, v):
    groups = defaultdict(lambda: ([], []))
    for dream in dreams:
        def visit(j, p, sign, steps):
            if j == len(dream):
                groups[p][int(sign < 0)].append(steps)
                return
            r, c = dream[j]
            for a, b, q, weight in covers(p, r):
                visit(j + 1, q, sign * weight, steps + ((r, c, a, b),))
        visit(0, v, 1, ())
    return groups


def near(x, y, width):
    # Once the first differing step is known, only the suffix past
    # the allowed interval still needs comparison.
    for j, (a, b) in enumerate(zip(x, y)):
        if a != b:
            return x[j + width:] == y[j + width:]
    return True


def hall_test(negative, positive, width):
    # Indices refer to lexicographically sorted objects on each side.
    neighbors = [[j for j, y in enumerate(positive) if near(x, y, width)] for x in negative]
    neg_match, pos_match = {}, {}
    for root in range(len(negative)):
        queue = deque([root])
        seen = {root}
        parent = {}
        free = None
        while queue and free is None:
            i = queue.popleft()
            for j in neighbors[i]:
                if j in parent:
                    continue
                parent[j] = i
                if j not in pos_match:
                    free = j
                    break
                mate = pos_match[j]
                if mate not in seen:
                    seen.add(mate)
                    queue.append(mate)
        if free is None:
            hood = {j for i in seen for j in neighbors[i]}
            require(hood == set(parent) and len(hood) < len(seen), 'Invalid Hall witness')
            return {'negative_indices': sorted(seen), 'positive_neighbor_indices': sorted(hood), 'sample_negative_steps': negative[min(seen)]}
        while free is not None:
            i = parent[free]
            old = neg_match.get(i)
            neg_match[i], pos_match[free] = free, i
            free = old
    require(len(set(neg_match.values())) == len(negative) and all(j in neighbors[i] for i, j in neg_match.items()), 'Invalid saturating matching')
    return None


def investigate(config):
    n = config['n']
    require(2 <= n <= 5, 'Supported ranks are 2 through 5')
    perms = sorted(permutations(range(1, n + 1)), key=lambda p: (length(p), p))
    by_degree = defaultdict(list)
    for p in perms:
        by_degree[length(p)].append(p)
    dreams = pipe_dreams(n)
    for p in perms:
        monomials = Counter()
        for dream in dreams[p]:
            rows = Counter(r for r, c in dream)
            monomials[tuple(rows[i] for i in range(1, n + 1))] += 1
        require(dict(monomials) == schubert(p), 'Pipe-dream polynomial mismatch at ' + str(p))
    if n >= 3:
        identity = perms[0]
        s1, s2 = swap(identity, 0, 1), swap(identity, 1, 2)
        pos, neg = signed_objects(dreams[s2], identity)[s1]
        require(len(pos) == len(neg) == 1 and hall_test(neg, pos, 1) is None, 'Simple-reflection cancellation failed')
        square_target = (3, 1, 2) + tuple(range(4, n + 1))
        pos, neg = signed_objects(dreams[s1], s1)[square_target]
        require(len(pos) == 1 and not neg, 'Simple-reflection square failed')
    pairs = [(u, v) for u in perms for v in perms if length(u) <= config['u_max'] and length(v) <= config['v_max'] and length(u) + length(v) in by_degree]
    pairs.sort(key=lambda pair: (sum(length(p) for p in pair), length(pair[0]), pair))
    widths = (1, 2)
    stats = {k: {'saturated': 0, 'failed': 0, 'first_failure': None} for k in widths}
    report = {'config': config, 'eligible_pairs_with_targets': len(pairs), 'pairs_finished': 0, 'triples_checked': 0, 'triples_with_negatives': 0, 'widths': stats, 'complete': False, 'sanity_checks_passed': True}
    for u, v in pairs:
        if monotonic() >= deadline:
            return report
        groups = signed_objects(dreams[u], v)
        poly = polynomial_product(u, v)
        for w in by_degree[length(u) + length(v)]:
            pos, neg = groups.get(w, ([], []))
            pos, neg = sorted(pos), sorted(neg)
            coeff = sum(c * extract(w, a) for a, c in poly.items())
            require(coeff == len(pos) - len(neg), 'Signed coefficient mismatch at ' + str((u, v, w)))
            report['triples_checked'] += 1
            report['triples_with_negatives'] += int(bool(neg))
            for k in widths:
                witness = hall_test(neg, pos, k) if neg else None
                row = stats[k]
                if witness is None:
                    row['saturated'] += 1
                else:
                    row['failed'] += 1
                    if row['first_failure'] is None:
                        row['first_failure'] = {'u': u, 'v': v, 'w': w, 'coefficient': coeff, 'positive_count': len(pos), 'negative_count': len(neg), 'hall_witness': witness}
        report['pairs_finished'] += 1
    report['complete'] = True
    return report


reports = []
for config in params['ranges']:
    if monotonic() >= deadline:
        break
    reports.append(investigate(config))
complete = len(reports) == len(params['ranges']) and all(r['complete'] for r in reports)
failures = sum(r['widths'][2]['failed'] for r in reports)
count = sum(r['triples_checked'] for r in reports)
result = {'summary': f'Checked {count} degree-compatible triples. Width two failed on {failures}. Requested ranges complete: {complete}.', 'complete': complete, 'reports': reports, 'witness_convention': 'Indices are zero-based within each sign, sorted lexicographically by the full step sequence. Each step is [row, column, left position, right position], all one-based.'}
with open('result.json', 'w') as out:
    json.dump(result, out)
