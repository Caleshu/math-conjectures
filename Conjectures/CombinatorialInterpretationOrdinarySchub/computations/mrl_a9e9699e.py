# MathResearchLab experiment a9e9699e-472d-48a8-9080-0b048ceb2730
# Check every possible rank-six summand index at degree fifteen
# sha256(code) = 455d4de7746cd10525860f066c3bf1ccc95e607c70a59388d7867bc27f39d8db
# parameters: {"n": 6}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from collections import Counter
from itertools import permutations
from math import comb, factorial

params = json.load(open(os.environ["MRL_PARAMS"]))
n = params['n']
if n != 6:
    raise ValueError('This finite check is scoped to n=6')
N = n * (n - 1) // 2

def compositions(total, slots):
    if slots == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for tail in compositions(total - first, slots - 1):
            yield (first,) + tail

def decode(code):
    # At position j (one-based), the chosen value is at most j + code[j-1].
    size = max([n] + [j + digit for j, digit in enumerate(code, 1)])
    unused = list(range(1, size + 1))
    prefix = [unused.pop(digit) for digit in code]
    return tuple(prefix + unused)

def encode(p):
    return tuple(sum(y < x for y in p[i+1:]) for i, x in enumerate(p))

def trim(p):
    end = len(p)
    while end and p[end-1] == end:
        end -= 1
    return p[:end]

# An index outside S6 exercises the fixed-tail convention in the decoder.
assert trim(decode((0, 0, 0, 0, 2))) == (1, 2, 3, 4, 7, 5, 6)
assert trim(decode((5, 4, 3, 2, 1))) == (6, 5, 4, 3, 2, 1)
seen = set()
exceptional = []
first_ascent_counts = Counter()
for code in compositions(N, n - 1):
    p = decode(code)
    recovered = encode(p)
    assert recovered[:n-1] == code and not any(recovered[n-1:])
    assert sum(recovered) == N
    key = trim(p)
    assert key not in seen
    seen.add(key)
    ascent = next((i for i in range(1, n) if p[i-1] < p[i]), None)
    if ascent is None:
        exceptional.append({'code': code, 'permutation_without_fixed_tail': key})
    else:
        first_ascent_counts[ascent] += 1
assert len(seen) == comb(N + n - 2, n - 2)

delta = tuple(reversed(range(n)))
# Relative to decreasing delta, sign is the parity of increasing pairs.
parity = {w: sum(x < y for i, x in enumerate(w) for y in w[i+1:]) % 2
          for w in permutations(delta)}
assert parity[delta] == 0 and len(parity) == factorial(n)
pair_counts = {}
for i in sorted(first_ascent_counts):
    pairs = set()
    for weight, sign in parity.items():
        swapped = weight[:i-1] + (weight[i], weight[i-1]) + weight[i+1:]
        assert parity[swapped] == 1 - sign
        pairs.add(tuple(sorted((weight, swapped))))
    assert 2 * len(pairs) == len(parity)
    pair_counts[i] = len(pairs)
expected = tuple(range(n, 0, -1))
passed = [entry['permutation_without_fixed_tail'] for entry in exceptional] == [expected]
result = {
    'summary': 'Only the longest index lacks a usable ascent.' if passed else 'The exception list differs from the prediction.',
    'author_support': 'proved_here',
    'justification': 'Every nonnegative five-entry code summing to fifteen is enumerated once. Decoding selects the entry with the specified number of smaller unused values and appends the unused values in increasing order. Direct inversion counts recover every code. All six-coordinate staircase weights are checked for each selected swap.',
    'status': 'verified' if passed else 'exception_list_mismatch',
    'candidate_indices': len(seen),
    'exceptional_indices': exceptional,
    'first_ascent_counts_one_based': dict(first_ascent_counts),
    'orbit_pairs_by_ascent_one_based': pair_counts
}
with open('result.json', 'w') as out:
    json.dump(result, out)
