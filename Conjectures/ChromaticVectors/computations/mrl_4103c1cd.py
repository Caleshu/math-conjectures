# MathResearchLab experiment 4103c1cd-92a4-4edd-909d-0aaa9924eab1
# Construct and replay a cycle for every admissible sextuple
# sha256(code) = 11a26c688f254f1bc56f629d054e5fdfd9259ec7d9b87bfd3569beda9aaa3139
# parameters: {"seed": 1729}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import itertools
import random
import time

started = time.monotonic()
params = json.load(open(os.environ['MRL_PARAMS']))
from ortools.sat.python import cp_model

rng = random.Random(params['seed'])
end = started + 102

def candidates(n):
    total = 1 << n
    def extend(prefix, used, low):
        left = n - len(prefix)
        if left == 1:
            last = total - used
            if last >= low and last % 2 == 0:
                yield prefix + (last,)
            return
        for x in range(low, (total - used) // left + 1, 2):
            if used + x >= 1 << (len(prefix) + 1):
                yield from extend(prefix + (x,), used + x, x)
    return set(extend((), 0, 2))

def dim(bit):
    return bit.bit_length() - 1

def steps(path):
    for i, v in enumerate(path):
        bit = v ^ path[(i + 1) % len(path)]
        if bit == 0 or bit & (bit - 1):
            raise ValueError('Non-cube edge')
        yield dim(bit)

def relabel(path, order):
    return tuple(sum(((v >> old) & 1) << new for new, old in enumerate(order)) for v in path)

def register(path, n, wanted, pool):
    size = 1 << n
    if len(path) != size or set(path) != set(range(size)):
        raise ValueError('Cycle does not span exactly once')
    word = tuple(steps(path))
    counts = tuple(word.count(i) for i in range(n))
    order = sorted(range(n), key=counts.__getitem__)
    key = tuple(counts[i] for i in order)
    if key not in wanted:
        raise ValueError('Witness outside candidate enumeration')
    if key not in pool:
        pool[key] = relabel(path, order)
    return key

def cut(path, j):
    i = next(i for i, d in enumerate(steps(path)) if d == j)
    return path[i + 1:] + path[:i + 1]

def seed_from_lower(n, wanted, pool, lower):
    m = n - 1
    high = 1 << m
    # Traverse each two-vertex fiber and follow the lower cycle between fibers.
    for path in lower.values():
        lifted = []
        for i, v in enumerate(path):
            lifted.extend((v | ((i % 2) << m), v | (((i + 1) % 2) << m)))
        register(tuple(lifted), n, wanted, pool)
    # Glue two lower cycles along one translated common edge. Only the relative
    # coordinate permutation matters, so keep the first cycle's labels fixed.
    need = {t for t in wanted - pool.keys() if t[0] == 2}
    variants = {}
    for counts, path in lower.items():
        for order in itertools.permutations(range(m)):
            key = tuple(counts[i] for i in order)
            if key not in variants:
                variants[key] = (path, order)
    for a, first in lower.items():
        first_cuts = [cut(first, j) for j in range(m)]
        for b, (second, order) in variants.items():
            if not need:
                return
            sums = [x + y for x, y in zip(a, b)]
            for j in range(m):
                sums[j] -= 2
                key = tuple(sorted([2] + sums))
                sums[j] += 2
                if key not in need:
                    continue
                p = first_cuts[j]
                q = cut(relabel(second, order), j)
                shift = high | (p[-1] ^ q[0])
                actual = register(p + tuple(v ^ shift for v in q), n, wanted, pool)
                if actual != key:
                    raise ValueError('Glue count mismatch')
                need.remove(key)

def walk(target, n, wanted, pool, length):
    distance = lambda c: sum(abs(a - b) for a, b in zip(c, target))
    best = min(map(distance, pool))
    src = rng.choice([c for c in pool if distance(c) == best])
    cycle = pool[src]
    cuts = [(i, d) for i, d in enumerate(steps(cycle)) if src[d] > target[d]]
    i, d = rng.choice(cuts)
    path = cycle[i + 1:] + cycle[:i + 1]
    counts = list(src)
    counts[d] -= 1
    for _ in range(length):
        closing = path[0] ^ path[-1]
        if closing & (closing - 1) == 0:
            j = dim(closing)
            counts[j] += 1
            key = tuple(sorted(counts))
            if key not in pool and register(path, n, wanted, pool) != key:
                raise ValueError('Path rotation count mismatch')
            counts[j] -= 1
            if target in pool:
                return
        if rng.randrange(2):
            path = path[::-1]
        tip = path[-1]
        moves = []
        for add in range(n):
            pivot = tip ^ (1 << add)
            if pivot == path[-2]:
                continue
            k = path.index(pivot)
            drop = dim(pivot ^ path[k + 1])
            delta = 0 if drop == add else int(counts[add] >= target[add]) - int(counts[drop] > target[drop])
            moves.append((delta, k, add, drop))
        if rng.random() < 0.87:
            least = min(move[0] for move in moves)
            moves = [move for move in moves if move[0] == least]
        _, k, add, drop = rng.choice(moves)
        path = path[:k + 1] + path[:k:-1]
        counts[add] += 1
        counts[drop] -= 1

def exact(target, seconds):
    n = len(target)
    size = 1 << n
    model = cp_model.CpModel()
    arcs = []
    by_dim = [[] for _ in target]
    for v in range(size):
        for j in range(n):
            w = v ^ (1 << j)
            var = model.NewBoolVar(f'a{v}_{w}')
            arcs.append((v, w, var))
            by_dim[j].append(var)
    # Every vertex is present and there are no self-loops. AddCircuit therefore
    # requires one directed cycle through every vertex.
    model.AddCircuit(arcs)
    for terms, count in zip(by_dim, target):
        model.Add(sum(terms) == count)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = params['seed']
    status = solver.Solve(model)
    name = solver.StatusName(status)
    if name in ('OPTIMAL', 'FEASIBLE'):
        succ = {v: w for v, w, var in arcs if solver.Value(var)}
        path = [0]
        for _ in range(size - 1):
            path.append(succ[path[-1]])
        if succ[path[-1]] != 0:
            raise ValueError('Solver cycle does not close')
        return name, tuple(path)
    if name not in ('UNKNOWN', 'INFEASIBLE'):
        raise RuntimeError(name)
    return name, None

small = candidates(2)
if small != {(2, 2)} or candidates(3) != {(2, 2, 4)}:
    raise ValueError('Candidate generator sanity check failed')
yes, square = exact((2, 2), 2)
no, _ = exact((0, 4), 2)
if yes not in ('OPTIMAL', 'FEASIBLE') or no != 'INFEASIBLE':
    raise ValueError(('Square sanity check failed', yes, no))
lower = {}
register(square, 2, small, lower)
for n in range(3, 7):
    wanted = candidates(n)
    pool = {}
    seed_from_lower(n, wanted, pool, lower)
    search_end = started + 79 if n == 6 else min(started + 16, time.monotonic() + 4)
    rounds = 0
    while len(pool) < len(wanted) and time.monotonic() < search_end:
        missing = sorted(wanted - pool.keys())
        rng.shuffle(missing)
        for target in missing:
            if time.monotonic() >= search_end:
                break
            if target not in pool:
                walk(target, n, wanted, pool, min(600, 48 * (rounds + 1)))
        rounds += 1
    lower = pool

statuses = []
impossible = set()
for target in sorted(wanted - pool.keys()):
    left = end - time.monotonic()
    if left < 0.8:
        break
    status, path = exact(target, min(left - 0.4, 4.0))
    statuses.append({'counts': target, 'status': status})
    if path is not None:
        if register(path, 6, wanted, pool) != target:
            raise ValueError('Solver count mismatch')
    if status == 'INFEASIBLE':
        impossible.add(target)
        break

# Independent replay of the serialized certificates, including the closing bit.
witnesses = []
for target, path in sorted(pool.items()):
    word = ''.join(str(j) for j in steps(path))
    v = 0
    seen = set()
    counts = [0] * 6
    for digit in word:
        j = int(digit)
        if j not in range(6) or v in seen:
            raise ValueError('Invalid serialized walk')
        seen.add(v)
        counts[j] += 1
        v ^= 1 << j
    if v != 0 or seen != set(range(64)) or tuple(counts) != target:
        raise ValueError('Certificate replay failed')
    witnesses.append({'counts': target, 'steps': word})
unresolved = sorted(wanted - pool.keys() - impossible)
result = {'summary': f'{len(witnesses)} of {len(wanted)} candidates have replayed witnesses. {len(impossible)} solver-proved infeasible. {len(unresolved)} unresolved.', 'n': 6, 'candidate_count': len(wanted), 'sanity_solver_statuses': {'square_2_2': yes, 'square_0_4': no}, 'witnesses': witnesses, 'solver_calls_Q6': statuses, 'infeasible': sorted(impossible), 'unresolved': unresolved, 'all_candidates_realized': len(pool) == len(wanted), 'author_support': 'proved_here', 'justification': 'Each listed word was replayed from zero and checked for vertex coverage, closure, and its labeled transition counts. Infeasibility entries require INFEASIBLE from the full directed circuit model. The unresolved list is the enumerated candidate set minus those two sets.'}
with open('result.json', 'w') as output:
    json.dump(result, output, separators=(',', ':'))