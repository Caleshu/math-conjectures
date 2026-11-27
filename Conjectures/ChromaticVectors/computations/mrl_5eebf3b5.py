# MathResearchLab experiment 5eebf3b5-b1c2-4511-a513-375b73e2e5f7
# Witness coverage and exact feasibility for missing septuples
# sha256(code) = de0c93fa8e35e86c091f4f015a948c6e7aea0f1b4d3158b8a2290e2312b8b473
# parameters: {"seed": 731, "words": [], "focus": null}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import random
import time
from collections import deque
from itertools import accumulate

start = time.monotonic()
params = json.load(open(os.environ['MRL_PARAMS']))
from ortools.sat.python import cp_model

rng = random.Random(params.get('seed', 731))
N = 128
D = 7
unit = [bytes([i]) for i in range(D)]

def scope(prefix=(), remaining=64):
    slots = D - len(prefix)
    lo = prefix[-1] if prefix else 1
    if slots == 1:
        if remaining >= lo:
            yield tuple(2*x for x in prefix + (remaining,))
        return
    for x in range(lo, remaining // slots + 1):
        if 64 - remaining + x >= 1 << len(prefix):
            yield from scope(prefix + (x,), remaining - x)

# Independent enumeration: choose largest entries first, and filter only at leaves.
def reverse_scope(left, slots, cap, descending=()):
    if slots == 1:
        if 1 <= left <= cap:
            half = (left,) + descending[::-1]
            if all(s >= 1 << i for i, s in enumerate(accumulate(half))):
                yield tuple(2*x for x in half)
        return
    for x in range((left + slots - 1)//slots, min(cap, left - slots + 1) + 1):
        yield from reverse_scope(left-x, slots-1, x, descending+(x,))

targets = list(scope())
universe = set(targets)
assert len(targets) == len(universe) and targets == sorted(targets)
assert universe == set(reverse_scope(64, 7, 64))

def audit(word, n):
    size = 1 << n
    if len(word) != size:
        raise ValueError('wrong cycle length')
    seen = bytearray(size)
    counts = [0]*n
    v = 0
    for d in word:
        if d >= n or seen[v]:
            raise ValueError('invalid symbol or repeated vertex')
        seen[v] = 1
        counts[d] += 1
        v ^= 1 << d
    if v != 0:
        raise ValueError('open walk')
    return tuple(sorted(counts))

def vertices(word):
    path = [0]
    for d in word:
        path.append(path[-1] ^ (1 << d))
    return path

def interleave(word, d):
    out = bytearray(2*len(word))
    out[::2] = unit[d]*len(word)
    out[1::2] = word
    return bytes(out)

def exact(target, seconds):
    n = len(target)
    size = 1 << n
    model = cp_model.CpModel()
    arcs = []
    by_dim = [[] for _ in target]
    outgoing = [[] for _ in range(size)]
    for v in range(size):
        for d in range(n):
            u = v ^ (1 << d)
            take = model.NewBoolVar(f'e_{v}_{d}')
            arcs.append((v, u, take))
            by_dim[d].append(take)
            outgoing[v].append(take)
    model.AddCircuit(arcs)
    for d, count in enumerate(target):
        model.Add(sum(by_dim[d]) == count)
    assert target[-1] > 0
    model.Add(outgoing[0][-1] == 1)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 731
    solver.parameters.max_time_in_seconds = seconds
    status = solver.Solve(model)
    name = solver.StatusName(status)
    word = None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        v = 0
        symbols = []
        for _ in range(size):
            d, = [d for d, take in enumerate(outgoing[v]) if solver.Value(take)]
            symbols.append(d)
            v ^= 1 << d
        word = bytes(symbols)
        assert audit(word, n) == target
    elif status not in (cp_model.INFEASIBLE, cp_model.UNKNOWN):
        raise RuntimeError(name + ': ' + solver.ResponseStats())
    return name, word

sanity = {}
for small in [(2, 2, 4), (0, 4, 4)]:
    name, word = exact(small, 2.0)
    sanity[str(small)] = name
    assert (word is not None) if small[0] else (name == 'INFEASIBLE')

found = {}
queue = deque()

def register(word):
    key = audit(word, D)
    assert key in universe
    if key not in found:
        found[key] = word
        if key[-1] < 64:
            queue.append(word)
    return key

# Optional input consists only of complete words; supplied labels are unnecessary.
for digits in params.get('words', []):
    register(bytes(int(ch) for ch in digits))

# For a spanning path, join its final vertex to a neighbor at position i,
# remove edge i, and reverse the intervening tail. The new path is spanning.
def rotations(word, n):
    path = vertices(word)
    pos = [0]*len(path)
    for i, v in enumerate(path):
        pos[v] = i
    for d in range(n):
        if d != word[-1]:
            i = pos[path[-1] ^ (1 << d)]
            yield word[:i] + unit[d] + word[i+1:][::-1]

def path_bank():
    bank = [bytes([0])]
    for n, until in [(2, 0), (3, 0), (4, 1.8), (5, 3.5), (6, 13.0)]:
        old = bank
        bank = []
        seen = set()
        todo = deque()
        def add(w):
            key = tuple(sorted(w.count(d) for d in range(n)))
            if key not in seen:
                seen.add(key)
                bank.append(w)
                todo.append(w)
        for w in old:
            add(interleave(w, n-1) + unit[n-1])
            add(w + unit[n-1] + w)
            perm = list(range(n-1))
            rng.shuffle(perm)
            other = bytes(perm[d] for d in rng.choice(old))
            add(w + unit[n-1] + other)
        walk = bank[0]
        while time.monotonic() < start + until:
            w = todo.popleft() if todo else walk
            if rng.randrange(2):
                w = w[::-1]
            options = list(rotations(w, n))
            for candidate in options:
                add(candidate)
            walk = rng.choice(bank) if rng.randrange(25) == 0 else rng.choice(options)
    return bank

focus = params.get('focus')
if focus is not None:
    focus = tuple(focus)
    if focus not in universe:
        raise ValueError('focus must be a sorted admissible septuple')

if focus is None and len(found) < len(targets):
    for path in path_bank():
        register((path + unit[6])*2)
        odds = [d for d in range(6) if path.count(d) % 2]
        if len(odds) == 1:
            base_cycle = path + unit[odds[0]]
            register(interleave(base_cycle, 6))

# Given two equally oriented a-edges starting at x and x xor 2**b,
# replace them by the b-edges of that square and reverse the intervening arc.
def spread(word):
    path = vertices(word)[:-1]
    pos = [0]*N
    locations = [[] for _ in range(D)]
    for i, (v, d) in enumerate(zip(path, word)):
        pos[v] = i
        locations[d].append(i)
    counts = list(map(len, locations))
    for a in range(D):
        if counts[a] <= 2:
            continue
        for b in range(D):
            if a == b:
                continue
            changed = counts.copy()
            changed[a] -= 2
            changed[b] += 2
            key = tuple(sorted(changed))
            if key in found or key not in universe:
                continue
            for i in locations[a]:
                j = pos[path[i] ^ (1 << b)]
                if word[j] == a:
                    l, r = sorted((i, j))
                    new = word[:l] + unit[b] + word[l+1:r][::-1] + unit[b] + word[r+1:]
                    assert register(new) == key
                    break

if focus is None:
    while queue and len(found) < len(targets) and time.monotonic() < start + 62:
        spread(queue.popleft())

# If a path histogram fits coordinatewise under a permuted target, its
# deficit is exactly one symbol. Parity then forces that symbol to close it.
def seek(target):
    source = None
    for a in range(D):
        for b in range(D):
            if a != b:
                near = list(target)
                near[a] += 2
                near[b] -= 2
                source = found.get(tuple(sorted(near)))
                if source is not None:
                    break
        if source is not None:
            break
    if source is None:
        source = found[targets[0]] if targets[0] in found else next(iter(found.values()))
    cut = rng.randrange(N)
    w = source[cut+1:] + source[:cut]
    for _ in range(95):
        if rng.randrange(2):
            w = w[::-1]
        options = []
        for candidate in rotations(w, D):
            counts = [candidate.count(d) for d in range(D)]
            ranked = sorted(counts)
            excess = sum(max(0, x-y) for x, y in zip(ranked, target))
            if excess == 0:
                d, = [i for i, x in enumerate(counts) if x % 2]
                assert register(candidate + unit[d]) == target
                return
            options.append((excess, rng.random(), candidate))
        w = (rng.choice(options) if rng.randrange(5) == 0 else min(options))[2]

if focus is None and found:
    missing = [s for s in targets if s not in found]
    rng.shuffle(missing)
    i = 0
    while missing and len(found) < len(targets) and time.monotonic() < start + 85:
        s = missing[i % len(missing)]
        i += 1
        if s not in found:
            seek(s)
        for _ in range(min(8, len(queue))):
            spread(queue.popleft())
        if i % len(missing) == 0:
            missing = [s for s in missing if s not in found]
            i = 0

solver_log = []
negative = None
pending = [s for s in targets if s not in found]
if focus is not None:
    pending = [focus] if focus not in found else []
for s in pending:
    left = start + 102 - time.monotonic()
    if left < 0.45:
        break
    name, word = exact(s, min(left - 0.25, 95.0 if focus is not None else 1.5))
    solver_log.append({'target': s, 'status': name})
    if word is not None:
        assert register(word) == s
    elif name == 'INFEASIBLE':
        negative = s
        break

rows = []
missing = []
for s in targets:
    w = found.get(s)
    digits = None
    if w is None:
        missing.append(s)
    else:
        digits = ''.join(map(str, w))
        assert len(digits) == N and audit(bytes(int(ch) for ch in digits), D) == s
    rows.append([s, digits])
verdict = 'counterexample' if negative is not None else ('full_coverage' if not missing else 'partial')
out = {'summary': f'{verdict}: {len(found)} of {len(targets)} sorted Q7 targets have audited words', 'verdict': verdict, 'target_count': len(targets), 'rows_target_and_word': rows, 'missing_words': missing, 'proved_infeasible_target': negative, 'solver_calls': solver_log, 'solver_sanity': sanity}
with open('result.json', 'w') as f:
    json.dump(out, f, separators=(',', ':'))
