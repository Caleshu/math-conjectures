# MathResearchLab experiment c88e688a-4917-468f-8c9e-7891d55c3e6c
# Exact existence test across reduced words of $645312$
# sha256(code) = 98af86943443b9040c9a606296d167d4d2dd521030a528d3d1fd5cc9967364cb
# parameters: {"seconds": 100}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import time
from collections import Counter, defaultdict
from functools import cache
from hashlib import sha256
from itertools import permutations
import numpy as np

start = time.monotonic()
deadline = start + min(104.0, float(params.get('seconds', 100)))
E = (1, 2, 3, 4, 5, 6)
W = (6, 4, 5, 3, 1, 2)
prior = '2342512342321'
perms = list(permutations(E))
index = {x: i for i, x in enumerate(perms)}
N = len(perms)

@cache
def length(x):
    return sum(u > v for i, u in enumerate(x) for v in x[i+1:])

@cache
def swap(x, s):
    return x[:s] + (x[s+1], x[s]) + x[s+2:]

L = length(W)
D = (L+1)*N
assert L == 13

def wordstr(a):
    return ''.join(str(s+1) for s in a)

# Reuse the triangular Hecke-basis algorithm supplied with E-46824c.
@cache
def monomial(y):
    letters = []
    while y != E:
        s = next(i for i in range(5) if y[i] > y[i+1])
        letters.append(s)
        y = swap(y, s)
    row = Counter({(E, 0): 1})
    for s in reversed(letters):
        nxt = Counter()
        for (x, k), c in row.items():
            j = k + int(x[s] > x[s+1])
            nxt[x, j] += c
            nxt[swap(x, s), j] += c
        row = nxt
    return row

def column(w):
    f = monomial(w).copy()
    domain = {x for x, k in f}
    for x in sorted(domain - {w}, key=length, reverse=True):
        gap = length(w)-length(x)
        for k in range(gap, (gap+1)//2-1, -1):
            c = f[x, k]
            if c:
                for (u, j), b in monomial(x).items():
                    for shift in {k, gap-k}:
                        f[u, j+shift] -= c*b
    assert all(f[x, 0] == 1 for x in domain)
    target = np.zeros(D, dtype=np.int32)
    for (x, k), c in f.items():
        if c:
            assert c > 0 and ((x == w and k == 0 and c == 1) or (x != w and 2*k < length(w)-length(x)))
            target[N*k+index[x]] = c
    return target

# Every edge reverses a right descent of an ancestor of W.
children = defaultdict(list)
@cache
def word_count(y):
    if y == E:
        return 1
    count = 0
    for s in range(5):
        if y[s] > y[s+1]:
            x = swap(y, s)
            children[x].append((s, y))
            count += word_count(x)
    return count

total = word_count(W)
words = []
def enumerate_words(x, a):
    if x == W:
        words.append(a)
    else:
        for s, y in sorted(children[x]):
            enumerate_words(y, a+(s,))
enumerate_words(E, ())
assert len(words) == total and all(a < b for a, b in zip(words, words[1:]))
prior_rank = words.index(tuple(int(ch)-1 for ch in prior))

# The integer key N*k+i encodes defect k and permutation perms[i].
keys = np.arange(D, dtype=np.int32)
skip, keep = [], []
for s in range(5):
    step = np.array([N*int(x[s] > x[s+1]) for x in perms], dtype=np.int32)
    dest = np.array([index[swap(x, s)] for x in perms], dtype=np.int32)
    skipped = keys + step[keys % N]
    skip.append(skipped)
    keep.append(skipped - keys % N + dest[keys % N])

def mask_rows(a):
    r = np.array([index[E]], dtype=np.int32)
    for s in a:
        r = np.concatenate((skip[s][r], keep[s][r]))
    return r

# A Python integer represents a set of mask indices. Position 0 is bit 0
# both in a mask index and in its three-bit window pattern.
@cache
def windows(n):
    size = 1 << n
    universe = (1 << size)-1
    labels = []
    for j in range(n-2):
        stride = 1 << j
        runs = (universe // ((1 << (8*stride))-1))*((1 << stride)-1)
        labels.extend(runs << (p*stride) for p in range(8))
    return universe, labels

def packed(v):
    return int.from_bytes(np.packbits(v, bitorder='little').tobytes(), 'little')

def selector(bits, size):
    raw = np.frombuffer(bits.to_bytes(size//8, 'little'), dtype=np.uint8)
    return np.unpackbits(raw, bitorder='little').view(np.bool_)

def counts(r, bits):
    return np.bincount(r[selector(bits, len(r))], minlength=D)

def first_bit(bits):
    return (bits & -bits).bit_length()-1

def describe(g):
    k, i = divmod(int(g), N)
    return {'endpoint': ''.join(map(str, perms[i])), 'defect': k}

def prepare(a, target):
    r = mask_rows(a)
    zero = r < N
    assert np.array_equal(np.bincount(r[zero], minlength=N), target[:N])
    assert target[:N].max() == 1
    z = packed(zero)
    universe, lab = windows(len(a))
    free = tuple(i for i, masks in enumerate(lab) if not (z & masks))
    low = universe
    for i in free:
        low &= ~lab[i]
    return r, lab, free, low, universe

def quick(data, target):
    r, lab, free, low, universe = data
    bad = low & packed(target[r] == 0)
    if bad:
        m = first_bit(bad)
        return 'INFEASIBLE', 'protected_zero', dict(describe(r[m]), mask=m)
    lower = counts(r, low)
    over = np.flatnonzero(lower > target)
    if len(over):
        g = int(over[0])
        return 'INFEASIBLE', 'protected_overfill', dict(describe(g), required=int(target[g]), protected=int(lower[g]))
    if np.array_equal(lower, target):
        return 'FEASIBLE', 'all_free_banned', list(free)
    return 'UNKNOWN', 'requires_search', None

class Budget(Exception):
    pass

def exact(data, target, limit, stop):
    r, lab, free, initial_low, universe = data
    nodes = 0
    rules = Counter()
    def visit(open_labels, high, bans):
        nonlocal nodes
        nodes += 1
        if nodes > limit or time.monotonic() >= stop:
            raise Budget
        while True:
            # high avoids the bans. low additionally avoids all undecided labels.
            prefix = [high]
            for i in open_labels:
                prefix.append(prefix[-1] & ~lab[i])
            low = prefix[-1]
            lower, upper = counts(r, low), counts(r, high)
            if np.any(lower > target) or np.any(upper < target):
                rules['count_contradiction'] += 1
                return None
            if np.array_equal(lower, target):
                return sorted(bans.union(open_labels))
            if np.array_equal(upper, target):
                return sorted(bans)
            # All currently possible masks in a tight upper class are required.
            must_live = high & packed((upper == target)[r])
            allow = {i for i in open_labels if lab[i] & must_live}
            # A label is impossible if allowing it alone adds even one mask
            # to a class whose lower count is already the target.
            saturated = packed((lower == target)[r])
            tail = saturated
            forbid = set()
            for t in range(len(open_labels)-1, -1, -1):
                i = open_labels[t]
                if prefix[t] & lab[i] & tail:
                    forbid.add(i)
                tail &= ~lab[i]
            if allow & forbid:
                rules['opposite_forces'] += 1
                return None
            if not (allow or forbid):
                break
            rules['forced_labels'] += len(allow) + len(forbid)
            for i in forbid:
                high &= ~lab[i]
            bans = bans.union(forbid)
            open_labels = tuple(i for i in open_labels if i not in allow and i not in forbid)
        # An underfilled class must acquire at least one of its remaining masks.
        missing = np.flatnonzero(lower < target)
        g = int(missing[np.argmin((upper-lower)[missing])])
        candidates = high & ~low & packed(r == g)
        choices = set()
        while candidates:
            bit = candidates & -candidates
            candidates -= bit
            choices.add(frozenset(i for i in open_labels if lab[i] & bit))
        minimal = []
        for sig in sorted(choices, key=lambda s: (len(s), tuple(sorted(s)))):
            if not any(other <= sig for other in minimal):
                minimal.append(sig)
        assert minimal and all(minimal)
        rules['branch_nodes'] += 1
        for sig in minimal:
            answer = visit(tuple(i for i in open_labels if i not in sig), high, bans)
            if answer is not None:
                return answer
        return None
    try:
        ans = visit(free, universe, frozenset())
        status = 'INFEASIBLE' if ans is None else 'FEASIBLE'
    except Budget:
        ans, status = None, 'UNKNOWN'
    return status, ans, {'nodes_entered': nodes, 'rules': dict(rules)}

def replay(a, bans, target):
    # Independent scalar simulation for the witness, including every mask.
    observed = Counter()
    for m in range(1 << len(a)):
        if any(((m >> (i//8)) & 7) == i % 8 for i in bans):
            continue
        x, d = list(E), 0
        for j, s in enumerate(a):
            d += int(x[s] > x[s+1])
            if (m >> j) & 1:
                x[s], x[s+1] = x[s+1], x[s]
        observed[d*N+index[tuple(x)]] += 1
    assert observed == {int(g): int(target[g]) for g in np.flatnonzero(target)}
    return sum(observed.values())

# Check the KL normalization, the exact search on a feasible and an
# infeasible target, bit order, and the independent witness replay.
small = column((3, 4, 1, 2, 5, 6))
assert list(small[index[E]::N]) == [1, 1] + [0]*(L-1)
toy = (0, 1, 0)
toy_target = column((3, 2, 1, 4, 5, 6))
assert toy_target.sum() == 6
toy_target[N+index[E]] = 1
toy_data = prepare(toy, toy_target)
status, bans, _ = exact(toy_data, toy_target, 100, float('inf'))
assert status == 'FEASIBLE' and replay(toy, bans, toy_target) == 7
toy_target[N+index[E]] = 2
assert exact(toy_data, toy_target, 100, float('inf'))[0] == 'INFEASIBLE'

K = column(W)
sums = K.reshape(L+1, N).sum(axis=1).tolist()
assert sums == [564, 252, 96] + [0]*(L-2)
# A rank is closed only by an exact contradiction, a replay, or the
# supplied core for the one explicitly identified prior word.
closed = {prior_rank: 'supplied_core'}
examples = {}
witness = None
hard = []
attempts = Counter()

def record(rank, status, kind, raw):
    global witness
    if status == 'FEASIBLE':
        a = words[rank]
        count = replay(a, raw, K)
        witness = {'word': wordstr(a), 'rank': rank, 'survivors': count, 'all_classes_match': True, 'bans': [{'start_one_based': i//8+1, 'bits_in_position_order': ''.join(str((i >> t) & 1) for t in range(3))} for i in sorted(raw)]}
    closed[rank] = kind
    if kind not in examples:
        examples[kind] = {'rank': rank, 'word': wordstr(words[rank]), 'detail': raw}

for rank, a in enumerate(words):
    if time.monotonic() >= deadline or witness is not None:
        break
    if rank == prior_rank:
        continue
    status, kind, detail = quick(prepare(a, K), K)
    if status == 'UNKNOWN':
        hard.append(rank)
    else:
        record(rank, status, kind, detail)

# Give each residual word a bounded first search before revisiting any
# difficult branch tree. UNKNOWN never closes a rank.
node_limit = 64
while hard and witness is None and time.monotonic() < deadline:
    retry = []
    for rank in hard:
        if time.monotonic() >= deadline or witness is not None:
            break
        status, ans, stats = exact(prepare(words[rank], K), K, node_limit, deadline)
        attempts[status] += 1
        if status == 'UNKNOWN':
            retry.append(rank)
        elif status == 'FEASIBLE':
            record(rank, status, 'branch_witness', ans)
        else:
            record(rank, status, 'exact_search_exclusion', stats)
    hard = retry
    node_limit *= 8

remaining = [i for i in range(total) if i not in closed]
ranges = []
for i in remaining:
    if ranges and ranges[-1][1] == i-1:
        ranges[-1][1] = i
    else:
        ranges.append([i, i])
status = 'FEASIBLE' if witness is not None else ('UNKNOWN' if remaining else 'INFEASIBLE')
summary = {'FEASIBLE': 'A position-specific list exists. Its scalar replay matches the entire KL column.', 'INFEASIBLE': 'Every reduced word is excluded, including the single word covered by the supplied core.', 'UNKNOWN': 'The existence question remains open on exactly the reported rank ranges.'}[status]
ledger = '\n'.join(f'{i} {wordstr(words[i])} {closed[i]}' for i in sorted(closed))
out = {'summary': summary, 'status': status, 'author_support': 'speculative' if status == 'UNKNOWN' else 'proved_here', 'word_count': total, 'rank_convention': 'Zero-based lexicographic order on generator strings with 1 < 2 < 3 < 4 < 5. Ranges include both ends.', 'prior_word': prior, 'prior_rank': prior_rank, 'covered_by_reason': dict(Counter(closed.values())), 'example_by_reason': examples, 'coverage_ledger_sha256': sha256(ledger.encode()).hexdigest(), 'exact_search_attempt_statuses': dict(attempts), 'witness': witness, 'individually_undecided_count': len(remaining), 'individually_undecided_rank_ranges': ranges, 'KL_sums_by_defect': sums, 'sanity': {'toy_search': ['FEASIBLE', 'INFEASIBLE'], 'feasible_toy_replay_count': 7, 'P_e_341256': [1, 1]}, 'seconds': round(time.monotonic()-start, 3)}
out['justification'] = r'Every reduced expression ends at a right descent, and deleting its last letter gives a reduced expression for the predecessor. Recursion from the identity therefore enumerates precisely all reduced words, once each. For the KL target, the Hecke relation gives the two transitions of monomial on multiplication by $1+T_s$, each weighted by $1$ on ascents and $q$ on descents. For each $y$, its product $B_y$ is triangular with leading term $T_y$, and $q^{-\ell(y)/2}B_y$ is bar-invariant. A subtraction at $x$ uses shifts $k$ and $g-k$ once each, where $g=\ell(w)-\ell(x)$, so it preserves normalized bar invariance. A distinct companion shift lies below the degree cutoff. The degree at each endpoint $u$ initially is at most $\ell(w)-\ell(u)$ since each descent costs at least one unit of length compared with keeping an ascent. The shifts preserve this bound. Descending elimination thus yields the defining triangular bar-invariant KL element. Binary branching gives every mask once and increments its defect on every pre-step descent. The checked degree-zero multiplicities force all their masks and hence all their labels. Any shorter window ban is equivalent to banning all extensions at one containing triple. For any partial assignment, low survives every completion, and high contains every possible survivor. A tight upper class forces all its possible masks. If allowing one label alone adds a mask to a tight lower class, that label must be banned. At a branch, a deficient lower class must acquire a mask from high outside low. Every such mask requires one of the listed signatures, each containing an inclusion-minimal signature. Allowing each minimal signature in turn therefore covers every possible solution. Each branch decides at least one label. A count contradiction excludes its branch and equality to either extreme gives an explicit assignment. Budget exhaustion excludes nothing. For the prior word the supplied exhaustive rows force labels 9, 17 and 25 banned in the identity defect-three class. After these bans the endpoint 125436 defect-two count is either zero or two, whereas its target is one. All affirmative results are replayed with direct adjacent swaps and the decoded position-specific bans.'
with open('result.json', 'w') as f:
    json.dump(out, f)
