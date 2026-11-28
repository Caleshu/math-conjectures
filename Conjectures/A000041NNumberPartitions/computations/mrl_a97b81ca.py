# MathResearchLab experiment a97b81ca-cc18-4074-80da-300d6faefe41
# Exact coverage by pairwise nondividing partition weights
# sha256(code) = 168e7fa22d3e69cb4ee060db71c5cc6787956f1ee233b9f032b0f64c50843d16
# parameters: {"low": 250001, "high": 500000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import base64
import json, os
import time
import zlib
import numpy as np

params = json.load(open(os.environ['MRL_PARAMS']))
started = time.monotonic()
low, high = params['low'], params['high']
assert (low, high) == (250001, 500000)

# Coin-change DP computes every p(k) in the prefix independently of the search.
# Appending a part 1 injects partitions of k into partitions of k+1,
# so the first overweight term suffices to certify the cutoff.
limit = 16
while True:
    p = [1] + [0] * limit
    for part in range(1, limit + 1):
        for n in range(part, limit + 1):
            p[n] += p[n - part]
    if p[-1] + 2 > high:
        break
    limit *= 2
assert p[:11] == [1, 1, 2, 3, 5, 7, 11, 15, 22, 30, 42]
cut = next(k for k in range(1, limit + 1) if p[k] + 2 > high)
weights = [p[k] + 2 for k in range(1, cut)]
assert len(weights) <= 64


def members(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def conflicts(w):
    return [sum(1 << j for j, b in enumerate(w)
                if i != j and (a % b == 0 or b % a == 0))
            for i, a in enumerate(w)]


def solve(w, lo, hi, deadline):
    adj = conflicts(w)
    witness = np.zeros(hi - lo + 1, dtype=np.uint64)
    pending = np.arange(lo, hi + 1, dtype=np.int32)
    cap = (1 << (hi + 1)) - 1
    byte_count = (hi + 8) // 8
    tree = bytearray()
    stack = [((1 << len(w)) - 1, 0, 0)]

    def contains(bits, indices):
        packed = np.frombuffer(bits.to_bytes(byte_count, 'little'), dtype=np.uint8)
        return ((packed[indices >> 3] >> (indices & 7)) & 1).astype(bool)

    while stack and pending.size and time.monotonic() < deadline:
        free, forced, offset = stack.pop()
        if offset > hi or offset + sum(w[i] for i in members(free)) < lo:
            tree.append(255)
            continue
        pivot = max(members(free), key=lambda i: (adj[i] & free).bit_count(), default=None)
        if pivot is not None and adj[pivot] & free:
            bit = 1 << pivot
            rest = free ^ bit
            tree.append(pivot + 1)
            stack.append((rest & ~adj[pivot], forced | bit, offset + w[pivot]))
            stack.append((rest, forced, offset))
            continue

        # At a leaf every subset of the free indices is legal.
        tree.append(0)
        bits = 1
        prefixes = []
        for i in members(free):
            prefixes.append((i, bits))
            bits |= (bits << w[i]) & cap
        eligible = pending >= offset
        hit = eligible.copy()
        hit[eligible] = contains(bits, pending[eligible] - offset)
        targets = pending[hit]
        if not targets.size:
            continue
        remainder = targets - offset
        words = np.full(targets.size, forced, dtype=np.uint64)
        for i, previous in reversed(prefixes):
            take = ~contains(previous, remainder)
            words[take] |= np.uint64(1 << i)
            remainder[take] -= w[i]
        assert np.all(remainder == 0)
        witness[targets - lo] = words
        pending = pending[~hit]
    return witness, pending, not stack, tree


# Independent exhaustive sanity check. This instance has both conflicts
# and legal pairs, and includes unattainable targets inside the sum range.
toy = [3, 4, 12, 17]
expected = set()
for mask in range(1, 1 << len(toy)):
    chosen = [toy[i] for i in members(mask)]
    if all(b % a for j, a in enumerate(chosen) for b in chosen[j + 1:]):
        expected.add(sum(chosen))
toy_words, toy_pending, toy_done, _ = solve(toy, 1, sum(toy), float('inf'))
assert toy_done and set(np.flatnonzero(toy_words) + 1) == expected
assert set(toy_pending) == set(range(1, sum(toy) + 1)) - expected

words, pending, exhausted, tree = solve(weights, low, high, started + 90)
covered = words != 0
assert np.array_equal(np.flatnonzero(~covered) + low, pending)

# Validate every decoded witness directly against its target and all pairs.
# Store literal 1-based indices in increasing order, with a zero after each
# target's list. The rows are implicit consecutive N, including empty rows.
flags = np.array([1 << i for i in range(len(weights))], dtype=np.uint64)
labels = np.array(list(range(1, len(weights) + 1)) + [0], dtype=np.uint8)
wvec = np.array(weights, dtype=np.int64)
compressor = zlib.compressobj(1)
chunks = []
for start in range(0, len(words), 4096):
    block = words[start:start + 4096]
    selected = (block[:, None] & flags) != 0
    totals = selected.astype(np.int64) @ wvec
    targets = np.arange(low + start, low + start + len(block))
    assert np.array_equal(totals, np.where(block != 0, targets, 0))
    for j, b in enumerate(weights):
        for i in range(j):
            if b % weights[i] == 0:
                assert not np.any(selected[:, i] & selected[:, j])
    keep = np.column_stack((selected, np.ones(len(block), dtype=bool)))
    raw = np.broadcast_to(labels, keep.shape)[keep].tobytes()
    chunks.append(compressor.compress(raw))
chunks.append(compressor.flush())


def ranges(values):
    if not len(values):
        return []
    groups = np.split(values, np.flatnonzero(np.diff(values) != 1) + 1)
    return [[int(g[0]), int(g[-1])] for g in groups]


missing = ranges(pending)
complete = exhausted or not missing
certificate = None
if exhausted and missing:
    certificate = {
        'preorder_bytes_zlib_base64': base64.b64encode(zlib.compress(tree)).decode('ascii'),
        'replay': 'Start with all indices free and none forced. A byte k in 1..64 splits on free index k. Visit exclusion first, then inclusion, removing k in both children and its divisibility neighbors in the inclusion child. Add its weight to the forced sum only in the inclusion child. Byte 255 closes a node whose forced sum exceeds high or whose forced sum plus all free weights is below low. Byte 0 closes a node with pairwise nondividing free weights. At each such leaf start a bitset at 1 and OR it with its left shift by each free weight in turn. For each claimed gap N at least the forced sum, verify that bit N minus the forced sum is clear. Check that the root consumes the entire byte stream.'
    }
result = {
    'summary': f'{int(covered.sum())} of {len(words)} targets have validated index lists. {len(pending) if exhausted else 0} certified gaps. {0 if complete else len(pending)} unresolved targets.',
    'status': 'COMPLETE' if complete else 'PARTIAL',
    'scope_inclusive': [low, high],
    'weights_in_index_order_from_1': weights,
    'first_excluded_index_and_weight': [cut, p[cut] + 2],
    'witness_encoding': 'Base64-decode, then zlib-decompress. Each nonzero byte is a literal summand index k. A zero ends the current list and advances N by one, starting at scope_inclusive[0]. There is exactly one terminated list per target. An empty list corresponds to a certified gap or an unresolved target as recorded below.',
    'summand_index_lists_zlib_base64': base64.b64encode(b''.join(chunks)).decode('ascii'),
    'certified_gap_ranges_inclusive': missing if exhausted else [],
    'unresolved_ranges_inclusive': [] if complete else missing,
    'exclusion_certificate': certificate,
    'sanity_check': 'All nonempty subsets of [3,4,12,17] were checked independently against the exact search.',
    'author_support': 'proved_here',
    'justification': 'Each published list was checked for its sum and every divisibility conflict. At a split, every legal completion either omits the pivot or includes it and omits all its neighbors. These children exhaust the possibilities. At an independent leaf, bit s is set exactly when a subset sums to s, by induction on the free weights with the empty subset as base case. Positive weights make truncation above the target bound exact. Exclusion is reported only after the full tree closes.'
}
with open('result.json', 'w') as out:
    json.dump(result, out, separators=(',', ':'))