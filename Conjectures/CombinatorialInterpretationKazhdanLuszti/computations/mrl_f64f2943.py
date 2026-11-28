# MathResearchLab experiment f64f2943-e870-4120-97fe-40d78f5d6cda
# Exhaustive protected-mask test for $645312$
# sha256(code) = 056b08208ba0c75e918a8f705396920c4668edeb3a79925c451be43814344c0d
# parameters: {"start_ordinal": 0, "budget_seconds": 100, "solver_seconds": 10}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import base64
import struct
import time
import zlib
from collections import Counter, defaultdict
from functools import cache
from itertools import permutations
import numpy as np
from ortools.sat.python import cp_model

start = time.monotonic()
deadline = start + min(104.0, float(params.get('budget_seconds', 100)))
solver_seconds = float(params.get('solver_seconds', 10))
first = int(params.get('start_ordinal', 0))
perms = list(permutations(range(1, 7)))
index = {p: i for i, p in enumerate(perms)}
e = index[(1, 2, 3, 4, 5, 6)]
w = index[(6, 4, 5, 3, 1, 2)]
N = len(perms)
length = [sum(p[i] > p[j] for i in range(6) for j in range(i + 1, 6)) for p in perms]
L = length[w]
assert L == 13
step = []
for p in perms:
    row = []
    for s in range(5):
        u = list(p)
        u[s], u[s + 1] = u[s + 1], u[s]
        row.append(index[tuple(u)])
    step.append(row)
S = np.array(step, dtype=np.intp)
h = np.array(length)
down = h[S] < h[:, None]
greedy = np.where(down, S, np.arange(N)[:, None])
assert all(step[step[x][s]][s] == x for x in range(N) for s in range(5))

def leq(x, y):
    p, r = perms[x], perms[y]
    return all(all(a <= b for a, b in zip(sorted(p[:j]), sorted(r[:j]))) for j in range(1, 6))

@cache
def column(y):
    # A[x,k] = [q^k]P_{x,y}. Object arrays use Python integers.
    if y == e:
        A = np.zeros((N, L + 2), dtype=object)
        A[e, 0] = 1
        return A
    s = next(s for s in range(5) if down[y, s])
    v = step[y][s]
    B = column(v)
    Bs = B[S[:, s]]
    A = np.where(down[:, s, None], Bs, B)
    shifted = np.where(down[:, s, None], B, Bs)
    assert not np.any(shifted[:, -1])
    A[:, 1:] += shifted[:, :-1]
    for z in range(N):
        gap = length[v] - length[z]
        if gap <= 0 or gap % 2 == 0 or not down[z, s]:
            continue
        mu = B[z, (gap - 1) // 2]
        if mu:
            power = (gap + 1) // 2
            C = column(z)
            assert not np.any(C[:, -power:])
            A[:, power:] -= mu * C[:, :-power]
    return A

K = column(w).astype(np.int64)
domain = np.array([x for x in range(N) if leq(x, w)], dtype=np.intp)
assert np.array_equal(np.flatnonzero(K[:, 0]), domain)
assert np.all(K[domain, 0] == 1) and np.all(K >= 0)
for x, k in zip(*np.nonzero(K)):
    assert leq(int(x), w) and (k == 0 or 2 * k < L - length[x])
small = index[(3, 4, 1, 2, 5, 6)]
assert list(column(small)[e]) == [1, 1] + [0] * L

@cache
def number(y):
    if y == e:
        return 1
    return sum(number(step[y][s]) for s in range(5) if down[y, s])

def words(y, suffix, offset):
    # Lexicographic order on the reversed word, generators numbered 0..4 internally.
    if y == e:
        yield offset, suffix
        return
    for s in range(5):
        if down[y, s]:
            v = step[y][s]
            end = offset + number(v)
            if end > first:
                yield from words(v, (s,) + suffix, offset)
            offset = end

def trace(a, m):
    x, d = e, 0
    for j, s in enumerate(a):
        v = step[x][s]
        d += int(length[v] < length[x])
        if (m >> j) & 1:
            x = v
    return x, d

def all_masks(a):
    # At step j the second half of each array keeps the new letter.
    X = np.array([e], dtype=np.intp)
    D = np.zeros(1, dtype=np.intp)
    for s in a:
        D = np.tile(D + down[X, s], 2)
        X = np.concatenate((X, S[X, s]))
    return X, D

def pack(bits):
    return int.from_bytes(np.packbits(bits, bitorder='little').tobytes(), 'little')

U = (1 << len(domain)) - 1

def planes_for(a):
    states = domain.copy()
    planes = [0] * len(a)
    for j in reversed(range(len(a))):
        s = a[j]
        planes[j] = pack(down[states, s])
        states = greedy[states, s]
    assert np.all(states == e)
    return planes

def matching(planes, j, p):
    endpoints = U
    for t in range(3):
        b = planes[j + t]
        endpoints &= b if (p >> t) & 1 else U ^ b
    return endpoints

# Reuse the proposed skip position for the two supplied words. Its coefficient,
# defect and protection must pass the same independent tests as a new witness.
prior = {'2132143254321': 5, '2135421534231': 7}

def single(a, planes, word):
    full = (1 << L) - 1
    order = [prior[word]] if word in prior else range(L)
    for i in order:
        m = full ^ (1 << i)
        x, d = trace(a, m)
        if K[x, d] != 0:
            continue
        # Every window away from i is covered by the all-kept reduced word.
        if all(matching(planes, j, (m >> j) & 7) for j in range(max(0, i - 2), min(i, L - 3) + 1)):
            return m
    if word in prior:
        # A bad supplied witness cannot eliminate the other twelve candidates.
        for i in range(L):
            m = full ^ (1 << i)
            x, d = trace(a, m)
            if K[x, d] == 0 and all(matching(planes, j, (m >> j) & 7) for j in range(L - 2)):
                return m
    return None

def expanded(a, planes):
    X, D = all_masks(a)
    ids = np.arange(len(X))
    zeros = ids[D == 0]
    assert np.array_equal(np.bincount(X[zeros], minlength=N), K[:, 0])
    protected = np.ones(len(X), dtype=bool)
    for j in range(L - 2):
        allowed = np.array([bool(matching(planes, j, p)) for p in range(8)])
        actual = np.bincount((zeros >> j) & 7, minlength=8) > 0
        assert np.array_equal(allowed, actual)
        protected &= allowed[(ids >> j) & 7]
    hits = np.flatnonzero(protected & (K[X, D] == 0))
    stats = {'all_masks': len(X), 'protected': int(protected.sum()), 'protected_zero_coefficient': len(hits)}
    return (int(hits[0]) if len(hits) else None), X, D, stats

def certificate(a, planes, m):
    covers = []
    for j in range(L - 2):
        pool = matching(planes, j, (m >> j) & 7)
        assert pool
        i = (pool & -pool).bit_length() - 1
        f = sum(((v >> i) & 1) << t for t, v in enumerate(planes))
        assert trace(a, f) == (domain[i], 0) and ((f ^ m) >> j) & 7 == 0
        covers.append(f)
    x, d = trace(a, m)
    assert K[x, d] == 0
    return {'mask': m, 'product': perms[x], 'defect': d, 'KL_row': K[x].tolist(), 'cover_masks_in_window_order': covers}

def solve(a, target, X, D, seconds):
    # The background fixes only bans contradicted by forced degree-zero masks.
    ids = np.arange(len(X))
    zeros = ids[D == 0]
    assert np.array_equal(np.bincount(X[zeros], minlength=N), target[:, 0]) and max(target[:, 0]) == 1
    triples = [a[j:j + 3] for j in range(len(a) - 2)]
    forced = {(t, int(p)) for j, t in enumerate(triples) for p in np.unique((zeros >> j) & 7)}
    labels = sorted({(t, p) for t in triples for p in range(8)} - forced)
    label_id = {key: i for i, key in enumerate(labels)}
    local = [[label_id.get((t, p), -1) for p in range(8)] for t in triples]
    model = cp_model.CpModel()
    bans = [model.new_bool_var('b' + str(i)) for i in range(len(labels))]
    alive = {(): 1}
    groups = defaultdict(Counter)
    for m, (x, d) in enumerate(zip(X, D)):
        choices = {row[(m >> j) & 7] for j, row in enumerate(local)}
        choices.discard(-1)
        sig = tuple(sorted(choices))
        if sig not in alive:
            v = model.new_bool_var('r' + str(len(alive)))
            model.add_bool_or([v] + [bans[i] for i in sig])
            for i in sig:
                model.add_implication(v, bans[i].Not())
            alive[sig] = v
        groups[int(x), int(d)][sig] += 1
    assumptions = {}
    keys = set(groups) | {(int(x), int(k)) for x, k in zip(*np.nonzero(target))}
    for x, k in sorted(keys):
        total = sum(n * alive[sig] for sig, n in groups[x, k].items())
        rhs = int(target[x, k])
        if isinstance(total, int) and total == rhs:
            continue
        g = model.new_bool_var('g' + str(len(assumptions)))
        model.add(total == rhs).only_enforce_if(g)
        model.add_assumption(g)
        assumptions[g.Index()] = [perms[x], k, rhs]
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 1
    solver.parameters.max_time_in_seconds = max(0.001, min(seconds, deadline - time.monotonic()))
    status = solver.solve(model)
    name = solver.status_name(status)
    out = {'solver_status': name, 'free_ban_count': len(bans), 'forced_allowed_label_count': len(forced)}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        chosen = {key for key, v in zip(labels, bans) if solver.value(v)}
        keep = np.ones(len(X), dtype=bool)
        for j, t in enumerate(triples):
            keep &= np.array([(t, p) not in chosen for p in range(8)])[(ids >> j) & 7]
        check = np.zeros(target.shape, dtype=np.int64)
        np.add.at(check, (X[keep], D[keep]), 1)
        assert np.array_equal(check, target)
        out['bans_letters_and_pattern'] = [[tuple(s + 1 for s in t), p] for t, p in sorted(chosen)]
    elif status == cp_model.INFEASIBLE:
        out['sufficient_core_product_degree_required_count'] = [assumptions[int(i)] for i in solver.sufficient_assumptions_for_infeasibility()]
    return out

# The length-three word 121 allows each full mask to be banned individually.
# The model must realize its KL column. Its returned list is replayed by solve().
toy = (0, 1, 0)
TX, TD = all_masks(toy)
toy_target = column(trace(toy, 7)[0]).astype(np.int64)
assert not np.any(toy_target[:, 1:])
san = solve(toy, toy_target, TX, TD, 3.0)
assert san['solver_status'] in ('OPTIMAL', 'FEASIBLE')

count = number(w)
assert 0 <= first < count
stop = min(count, first + int(params.get('max_words', count)))
assert stop > first
records = bytearray()
miss_single = None
miss_any = None
example = None
solves = {}
next_index = first
single_count = 0
for ordinal, a in words(w, (), 0):
    if ordinal >= stop or time.monotonic() >= deadline - 2:
        break
    assert ordinal == next_index
    word = ''.join(str(s + 1) for s in a)
    planes = planes_for(a)
    m = single(a, planes, word)
    if m is None:
        m, X, D, stats = expanded(a, planes)
        row = {'word': word, 'ordinal': ordinal, **stats}
        if m is not None:
            row['general_witness'] = certificate(a, planes, m)
        if miss_single is None or m is None:
            solves[word] = solve(a, K, X, D, solver_seconds)
        if miss_single is None:
            miss_single = row
        if m is None:
            miss_any = row
    else:
        single_count += 1
    if m is not None and example is None:
        example = {'word': word, **certificate(a, planes, m)}
    records.extend(struct.pack('<H', 65535 if m is None else m))
    next_index += 1
    if miss_any is not None:
        break

complete = first == 0 and next_index == count
verdict = 'false' if miss_any is not None else ('true' if complete else 'undecided outside checked range')
narrow = 'false' if miss_single is not None else ('true' if complete else 'undecided outside checked range')
out = {'summary': 'All-mask assertion: ' + verdict + '. Single-skip assertion: ' + narrow + '.', 'word_count_by_descent_recursion': count, 'checked_half_open_ordinal_range': [first, next_index], 'single_skip_witness_count': single_count, 'first_single_skip_failure_in_range': miss_single, 'first_all_mask_failure_in_range': miss_any, 'conditional_CP_SAT_results': solves, 'example_certificate': example, 'sanity_solver_status': san['solver_status'], 'KL_column_sums_by_degree': [int(v) for v in K.sum(axis=0)], 'P_e_w': K[e].tolist(), 'witnesses_zlib_base64': base64.b64encode(zlib.compress(records)).decode('ascii'), 'decoding': 'Enumerate words lexicographically by reversed generator sequence. Each little-endian uint16 is one witness for the next ordinal. Bit j keeps position j+1. Value 65535 denotes exhaustive failure. Window patterns use the same least-significant-bit-first order.', 'author_support': 'proved_here', 'justification': 'For the reported finite range, right descents partition reduced words by their last letter. Each KL column comes from the right-descent recurrence with exact integer arithmetic. At a defect-zero step the pre-step permutation is ascending at the generator, so the post-step permutation has a descent there exactly when the bit is one. This forces every reverse decision. The program checks that all interval endpoints reverse to the identity and have constant coefficient one. Their masks are therefore forced survivors. Every window of a reported witness is covered by one of these masks, so banning it would remove a forced survivor. Every shorter window extends to a triple. The witness itself lies in a zero-coefficient class. For an all-mask failure the forward table considers both decisions at every position, counts descents before the decision, and compares the full protected set with every zero-coefficient class. For CP-SAT each survival variable is equivalent to the absence of all bans in its signature. Its multiplicity is counted separately in every product and degree class. An infeasible core is relative to the explicitly reconstructible background that all labels occurring in a defect-zero mask must be allowed.'}
with open('result.json', 'w') as f:
    json.dump(out, f)
