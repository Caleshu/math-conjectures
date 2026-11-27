# MathResearchLab experiment abe57a3e-8da6-4571-aa5c-3ce8168abe56
# Verify supplied words and recover missing six-dimensional certificates
# sha256(code) = 80e90c0c82bb8a02acd5840b7eb49e931b095e256fa0c2ff2f477aec8a2dd8e1
# parameters: {"residual": null, "words": [], "recover": true, "seconds": 80, "seed": 69276}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import base64
import hashlib
import itertools
import json
import os
import random
import time
import zlib

params = json.load(open(os.environ['MRL_PARAMS']))
started = time.monotonic()
deadline = started + min(85.0, max(0.0, float(params.get('seconds', 80))))
rng = random.Random(int(params.get('seed', 69276)))


def candidates(n):
    total = 1 << n
    return {t for t in itertools.combinations_with_replacement(range(2, total // 2 + 1, 2), n)
            if sum(t) == total and all(sum(t[:k]) >= 1 << k for k in range(1, n + 1))}


def check(word, n):
    if len(word) != 1 << n:
        return None
    vertex = 0
    seen = set()
    counts = [0] * n
    for d in word:
        if type(d) is not int or not 0 <= d < n or vertex in seen:
            return None
        seen.add(vertex)
        counts[d] += 1
        vertex ^= 1 << d
    return tuple(counts) if vertex == 0 else None


def register(bank, word, n):
    counts = check(word, n)
    if counts is None:
        raise ValueError('Internally generated word failed independent cycle check')
    key = tuple(sorted(counts))
    if key not in bank:
        order = sorted(range(n), key=counts.__getitem__)
        rename = {old: new for new, old in enumerate(order)}
        bank[key] = tuple(rename[d] for d in word)
    return key


assert check((0, 1, 0, 1), 2) == (2, 2)
assert check((0, 0, 1, 1), 2) is None  # Right multiplicities, repeated vertex.
assert check((0, 1, 0, 0), 2) is None  # Four distinct departures, wrong endpoint.
U = candidates(6)
raw = params.get('residual')
if raw is None:
    scope = U
else:
    if not isinstance(raw, list) or any(not isinstance(row, list) or len(row) != 6 or any(type(x) is not int for x in row) for row in raw):
        raise ValueError('residual must contain integer sextuples')
    scope = {tuple(row) for row in raw}
    if len(raw) != 120 or len(scope) != 120 or not scope <= U:
        raise ValueError('Expected 120 distinct sorted admissible sextuples')

supplied = {}
input_rows = {}
rejected = []
for i, s in enumerate(params.get('words', [])):
    if not isinstance(s, str) or len(s) != 64 or any(ch not in '012345' for ch in s):
        rejected.append(i)
        continue
    w = tuple(map(int, s))
    if check(w, 6) is None:
        rejected.append(i)
        continue
    target = register(supplied, w, 6)
    input_rows.setdefault(target, i)
input_missing = scope.difference(supplied)


def seed_from_layers(bank, lower, goals, n):
    k = n - 1
    # Visit both copies of each lower vertex before the next lower transition.
    for w in lower.values():
        register(bank, tuple(d for old in w for d in (k, old)), n)
    # Cut one edge of the same dimension in each of two cycles. Translate the
    # resulting paths to align endpoints and join them by two layer crossings.
    labeled = {}
    for counts, w in lower.items():
        for perm in itertools.permutations(range(k)):
            x = tuple(counts[i] for i in perm)
            if x not in labeled:
                rename = {old: new for new, old in enumerate(perm)}
                labeled[x] = tuple(rename[d] for d in w)
    for t in sorted(goals.difference(bank)):
        if t[0] != 2:
            continue
        for x, a in labeled.items():
            diff = [t[i + 1] - x[i] for i in range(k)]
            for j in range(k):
                diff[j] += 2
                b = labeled.get(tuple(diff))
                diff[j] -= 2
                if b is not None:
                    ia, ib = a.index(j), b.index(j)
                    w = a[ia + 1:] + a[:ia] + (k,) + b[ib + 1:] + b[:ib] + (k,)
                    assert register(bank, w, n) == t
                    break
            else:
                continue
            break


def rotate_search(bank, t, n, steps, stop):
    # Remove one edge of a nearby certified cycle to obtain a spanning path.
    near = sorted(bank, key=lambda x: sum(abs(a - b) for a, b in zip(x, t)))
    key = rng.choice(near[:min(4, len(near))])
    w = bank[key]
    cut = rng.randrange(len(w))
    transitions = w[cut + 1:] + w[:cut]
    path = [0]
    for d in transitions:
        path.append(path[-1] ^ (1 << d))
    counts = list(key)
    counts[w[cut]] -= 1
    uphill = rng.choice((0.015, 0.05, 0.12))
    for step in range(steps):
        if step % 128 == 0 and time.monotonic() >= stop:
            break
        if rng.getrandbits(1):
            path.reverse()
        add = rng.randrange(n)
        pivot = path.index(path[0] ^ (1 << add))
        if pivot == 1:
            continue
        drop = (path[pivot] ^ path[pivot - 1]).bit_length() - 1
        # Change in sum_i max(counts[i] - t[i], 0). Here add != drop.
        change = int(counts[add] >= t[add]) - int(counts[drop] > t[drop])
        if change > 0 and rng.random() >= uphill:
            continue
        path[:pivot] = path[:pivot][::-1]
        counts[add] += 1
        counts[drop] -= 1
        closing = path[0] ^ path[-1]
        if closing.bit_count() != 1:
            continue
        c = counts.copy()
        c[closing.bit_length() - 1] += 1
        candidate = tuple(sorted(c))
        if candidate not in bank:
            cycle = tuple((v ^ path[i - 1]).bit_length() - 1 for i, v in enumerate(path))
            assert register(bank, cycle, n) == candidate
        if candidate == t:
            break


bank6 = dict(supplied)
if input_missing and params.get('recover', True) and time.monotonic() < deadline:
    banks = {2: {(2, 2): (0, 1, 0, 1)}}
    for n in range(3, 7):
        if time.monotonic() >= deadline:
            break
        bank = bank6 if n == 6 else {}
        goals = scope if n == 6 else candidates(n)
        seed_from_layers(bank, banks[n - 1], goals, n)
        banks[n] = bank
        if n == 6 and (4, 4, 4, 4) in banks[4]:
            # Tight four-coordinate projection. Traverse a square fiber by
            # 4,5,4 or by 5,4,5 before each transition of the base cycle.
            base = banks[4][(4, 4, 4, 4)]
            for switch in range(0, 9, 2):
                w = []
                for i, d in enumerate(base):
                    w.extend((4, 5, 4) if i < switch else (5, 4, 5))
                    w.append(d)
                register(bank, w, 6)
        stop = deadline if n == 6 else min(deadline, time.monotonic() + (3.0 if n == 5 else 1.0))
        round_no = 0
        while time.monotonic() < stop:
            missing = sorted(goals.difference(bank))
            if not missing:
                break
            rng.shuffle(missing)
            for t in missing:
                if time.monotonic() >= stop:
                    break
                if t not in bank:
                    rotate_search(bank, t, n, min(16000, 600 * (1 + round_no)), stop)
            round_no += 1

# Final audit starts from the actual serialized digits. Each line is a whole
# word. Its target is recoverable from the line alone, with no label table.
lines = [''.join(map(str, bank6[t])) for t in sorted(scope.intersection(bank6))]
payload = '\n'.join(lines).encode('ascii')
archive = base64.b64encode(zlib.compress(payload, 9)).decode('ascii')
restored = zlib.decompress(base64.b64decode(archive, validate=True))
verified = set()
for line in restored.decode('ascii').splitlines():
    counts = check(tuple(map(int, line)), 6)
    if counts is None or counts not in scope or counts in verified:
        raise ValueError('Archive audit failed')
    verified.add(counts)
assert verified == scope.intersection(bank6)
missing = sorted(scope - verified)
named_gap = missing if raw is not None or not missing else None
result = {
    'summary': f'{len(verified)} of {len(scope)} targets in the audit scope have independently checked words. {len(missing)} lack a certificate.',
    'scope': 'provided residual list' if raw is not None else 'entire projection-admissible superset U',
    'scope_size': len(scope),
    'supplied_word_rows_rejected_zero_based': rejected,
    'first_valid_supplied_row_by_target': [[list(t), input_rows[t]] for t in sorted(scope.intersection(input_rows))],
    'missing_from_supplied_words_in_scope': sorted(input_missing),
    'missing_after_recovery_in_scope': missing,
    'named_residual_missing': named_gap,
    'named_gap_interpretation': 'exact list' if named_gap is not None else 'Intersect missing_after_recovery_in_scope with P-69276d. Its membership test was unavailable.',
    'verified_word_count': len(verified),
    'archive_format': 'base64 of zlib-compressed ASCII, one complete 64-digit word per line, sorted by count tuple',
    'uncompressed_sha256': hashlib.sha256(restored).hexdigest(),
    'verified_words_archive': archive
}
with open('result.json', 'w') as output:
    json.dump(result, output)
