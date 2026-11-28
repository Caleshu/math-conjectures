# MathResearchLab experiment 235db9da-9e1c-4375-b61f-cf568e68cc40
# Decide the length-three forbidden-block rule for $645312$
# sha256(code) = 66d74217b186de2003783a6e1d63ce66a8eb610eb4250525cf3cb64405016097
# parameters: {"seconds": 85, "solver_seconds": 0.5, "start_rank": 0}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import time
from collections import Counter, defaultdict
from functools import cache
from itertools import permutations
import numpy as np
from ortools.sat.python import cp_model

started = time.monotonic()
deadline = started + min(95.0, float(params.get('seconds', 85)))
perms = list(permutations(range(1, 7)))
index = {p: i for i, p in enumerate(perms)}
N = len(perms)
e = index[(1, 2, 3, 4, 5, 6)]
w = index[(6, 4, 5, 3, 1, 2)]
length = [sum(a > b for i, a in enumerate(p) for b in p[i+1:]) for p in perms]
L = length[w]
assert L == 13
right = [[index(p[:j] + (p[j+1], p[j]) + p[j+2:]) for j in range(5)] for p in perms]

def add_poly(column, x, poly, shift, scale):
    dest = column.setdefault(x, [])
    dest.extend([0] * max(0, len(poly) + shift - len(dest)))
    for i, a in enumerate(poly):
        dest[i + shift] += scale * a

@cache
def kl_column(u):
    if u == e:
        return {e: (1,)}
    j = next(j for j, v in enumerate(right[u]) if length[v] < length[u])
    v = right[u][j]
    prev = kl_column(v)
    out = {}
    # In the right-descent KL recurrence, P_{y,v} contributes to
    # both indices y and ys, shifted by one exactly when ys < y.
    for y, poly in prev.items():
        ys = right[y][j]
        shift = int(length[ys] < length[y])
        add_poly(out, y, poly, shift, 1)
        add_poly(out, ys, poly, shift, 1)
    for z, poly in prev.items():
        gap = length[v] - length[z]
        if gap % 2 == 0 or length[right[z][j]] >= length[z]:
            continue
        top = (gap - 1) // 2
        if top < len(poly) and poly[top]:
            for x, lower in kl_column(z).items():
                add_poly(out, x, lower, top + 1, -poly[top])
    for poly in out.values():
        while poly and poly[-1] == 0:
            poly.pop()
    return {x: tuple(poly) for x, poly in out.items() if poly}

def below(p, q):
    return all(all(a <= b for a, b in zip(sorted(p[:i]), sorted(q[:i]))) for i in range(1, 6))

column = kl_column(w)
assert set(column) == {i for i, p in enumerate(perms) if below(p, perms[w])}
assert column[w] == (1,)
assert all(p[0] == 1 and min(p) >= 0 and (x == w or 2*(len(p)-1) < L-length[x]) for x, p in column.items())
assert kl_column(index[(3, 4, 1, 2, 5, 6)])[e] == (1, 1)
C = (L + 1) * N
target = np.zeros(C, dtype=np.int32)
for x, poly in column.items():
    for k, a in enumerate(poly):
        target[k*N+x] = a

# Group code k*N+x. The low bit of the mask marks the first letter.
state = np.arange(C, dtype=np.int32)
steps = []
for j in range(5):
    xs = np.array([row[j] for row in right], dtype=np.int32)
    defect = np.array([length[ys] < length[y] for y, ys in enumerate(xs)], dtype=np.int32)
    skip = state + N*defect[state % N]
    keep = skip + xs[state % N] - state % N
    steps.append((skip, keep))

def extend(groups, j):
    skip, keep = steps[j]
    return np.concatenate((skip[groups], keep[groups]))

def bits(flags):
    return int.from_bytes(np.packbits(flags, bitorder='little').tobytes(), 'little')

M = 1 << L
masks = np.arange(M, dtype=np.int32)
all_masks = (1 << M) - 1

def flags(b):
    return np.unpackbits(np.frombuffer(b.to_bytes(M//8, 'little'), dtype=np.uint8), bitorder='little')

# A block key is (tuple of zero-based generators, mask bits low-to-high).
positions = [(i, d, [bits(((masks >> i) & ((1 << d)-1)) == t) for t in range(1 << d)]) for d in (1, 2, 3) for i in range(L-d+1)]

def cell(g):
    k, x = divmod(int(g), N)
    return {'x': ''.join(map(str, perms[x])), 'k': k, 'target': int(target[g])}

def screen(word, groups):
    counts = np.bincount(groups, minlength=C)
    short = np.flatnonzero(counts < target)
    if len(short):
        g = short[0]
        return 'shortage', dict(cell(g), available=int(counts[g]))
    compulsory = bits(counts[groups] == target[groups])
    occurrences = {}
    for i, d, patterns in positions:
        letters = word[i:i+d]
        for t, occurrence in enumerate(patterns):
            key = (letters, t)
            occurrences[key] = occurrences.get(key, 0) | occurrence
    bans = {key: b for key, b in occurrences.items() if not (b & compulsory)}
    killed = 0
    for b in bans.values():
        killed |= b
    fixed = np.bincount(groups[flags(all_masks ^ killed).astype(bool)], minlength=C)
    excess = np.flatnonzero(fixed > target)
    if len(excess):
        g = excess[0]
        return 'forced_surplus', dict(cell(g), forced=int(fixed[g]))
    if np.array_equal(fixed, target):
        return 'witness', list(bans)
    return 'residual', (bans, fixed)

def solve(groups, bans, fixed):
    keys = list(bans)
    incidence = np.column_stack([flags(bans[key]) for key in keys])
    rows = np.packbits(incidence, axis=1, bitorder='little')
    signatures = [int.from_bytes(row, 'little') for row in rows]
    model = cp_model.CpModel()
    allow = [model.NewBoolVar('') for key in keys]
    live = {}
    for sig in set(signatures) - {0}:
        variables = [var for j, var in enumerate(allow) if (sig >> j) & 1]
        if len(variables) == 1:
            live[sig] = variables[0]
        else:
            live[sig] = model.NewBoolVar('')
            model.AddMinEquality(live[sig], variables)
    sums = defaultdict(list)
    for (g, sig), count in Counter(zip(groups.tolist(), signatures)).items():
        if sig:
            sums[g].append(count * live[sig])
    for g, terms in sums.items():
        model.Add(sum(terms) == int(target[g] - fixed[g]))
    # A cell lacking variable masks already has fixed == target:
    # screen checked fixed <= target <= total in every cell.
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    solver.parameters.max_time_in_seconds = max(0.001, min(float(params.get('solver_seconds', 0.5)), deadline-time.monotonic()))
    status = solver.Solve(model)
    name = solver.StatusName(status)
    chosen = [key for key, var in zip(keys, allow) if not solver.Value(var)] if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
    return name, chosen

def literal_counts(word, forbidden):
    # Independent scalar pass. Signed generator +j is kept, -j skipped.
    counts = Counter()
    for mask in range(1 << len(word)):
        marked = tuple((j+1) if mask >> i & 1 else -(j+1) for i, j in enumerate(word))
        if any(marked[i:i+d] in forbidden for d in (1, 2, 3) for i in range(len(word)-d+1)):
            continue
        p = list(perms[e])
        k = 0
        for a in marked:
            j = abs(a)-1
            k += p[j] > p[j+1]
            if a > 0:
                p[j], p[j+1] = p[j+1], p[j]
        counts[k*N + index[tuple(p)]] += 1
    return counts

# For 121, keeping the first 1 and skipping 2 causes the only possible
# defect, at the last 1. Removing that pair leaves six distinct products.
small = (0, 1, 0)
small_w = index[(3, 2, 1, 4, 5, 6)]
small_counts = literal_counts(small, {(1, -2)})
assert small_counts == Counter({x: 1 for x in kl_column(small_w)}) and len(small_counts) == 6
small_groups = np.array([e], dtype=np.int32)
for j in small:
    small_groups = extend(small_groups, j)
assert Counter(small_groups.tolist()) == literal_counts(small, set())

# Sorted edges define zero-based lexicographic word ranks.
successors = defaultdict(list)
seen = {w}
stack = [w]
while stack:
    u = stack.pop()
    for j, v in enumerate(right[u]):
        if length[v] < length[u]:
            successors[v].append((j, u))
            if v not in seen:
                seen.add(v)
                stack.append(v)
for children in successors.values():
    children.sort()

@cache
def ways(u):
    return 1 if u == w else sum(ways(v) for j, v in successors[u])

total = ways(e)
lo = max(0, min(total, int(params.get('start_rank', 0))))
hi = max(lo, min(total, int(params.get('stop_rank', total))))

def visit(u, word, groups, rank):
    if rank >= hi or rank + ways(u) <= lo or time.monotonic() >= deadline:
        return
    if u == w:
        yield rank, word, groups
        return
    for j, v in successors[u]:
        if rank < hi and rank + ways(v) > lo and time.monotonic() < deadline:
            yield from visit(v, word+(j,), extend(groups, j), rank)
        rank += ways(v)

raw_target = Counter({int(g): int(target[g]) for g in np.flatnonzero(target)})
tallies = Counter()
statuses = Counter()
examples = {}
unknown = []
witness = None
next_rank = lo
for rank, word, groups in visit(e, (), np.array([e], dtype=np.int32), 0):
    assert rank == next_rank
    kind, data = screen(word, groups)
    tallies[kind] += 1
    chosen = None
    if kind == 'residual':
        status, chosen = solve(groups, *data)
        statuses[status] += 1
        if status not in ('OPTIMAL', 'FEASIBLE', 'INFEASIBLE'):
            unknown.append([rank, status])
    elif kind == 'witness':
        chosen = data
    elif kind not in examples:
        examples[kind] = dict(data, rank=rank, word=[j+1 for j in word])
    next_rank = rank+1
    if chosen is not None:
        forbidden = {tuple(j+1 if t >> i & 1 else -(j+1) for i, j in enumerate(letters)) for letters, t in chosen}
        actual = literal_counts(word, forbidden)
        assert actual == raw_target
        witness = {'rank': rank, 'word': [j+1 for j in word], 'forbidden_signed_blocks': sorted(forbidden), 'survivor_counts': [dict(cell(g), observed=actual[g]) for g in sorted(actual)]}
        break

unvisited = [[a, b] for a, b in ((0, lo), (next_rank, total)) if a < b]
if witness is not None:
    answer = 'YES: independently recounted witness'
elif not unvisited and not unknown:
    answer = 'NO: all reduced words excluded'
else:
    answer = 'UNDECIDED: open ranks are the unvisited half-open ranges and the individually listed unresolved ranks'
result = {'summary': answer, 'author_support': 'proved_here', 'justification': 'The decision follows from compulsory-mask screening, exact survivor constraints, and the reported rank coverage. A positive witness also passed literal enumeration.', 'length': L, 'masks_per_word': M, 'total_words': total, 'interval_size': len(column), 'screen_outcomes': dict(tallies), 'cp_sat_statuses': dict(statuses), 'sample_obstructions': examples, 'witness': witness, 'processed_half_open': [lo, next_rank], 'unvisited_half_open': unvisited, 'unresolved_processed_ranks': unknown, 'sanity_checks_passed': True}
with open('result.json', 'w') as out:
    json.dump(result, out)
