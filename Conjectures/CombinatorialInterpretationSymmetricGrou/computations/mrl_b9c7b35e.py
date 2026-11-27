# MathResearchLab experiment b9c7b35e-3aaa-4528-b15b-0357aca1fed4
# Check every necklace-vector rank against a centralizer character average
# sha256(code) = 5e5e2414c5d6aa22098b4433e01a05a616aa62a78c0488a77e6ffd16b221bbb0
# parameters: {"n_max": 6}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from collections import Counter, defaultdict
from fractions import Fraction
from functools import cache
from itertools import permutations
from math import factorial, prod

params = json.load(open(os.environ["MRL_PARAMS"]))
n_max = int(params.get('n_max', 6))
if not 1 <= n_max <= 6:
    raise ValueError('This exhaustive implementation supports 1 <= n_max <= 6')
deadline = time.monotonic() + 95

def partitions(n, cap):
    if n == 0:
        yield ()
    for first in range(min(n, cap), 0, -1):
        for rest in partitions(n - first, first):
            yield (first,) + rest

def sign(seq):
    inversions = sum(x > y for i, x in enumerate(seq) for y in seq[i + 1:])
    return -1 if inversions % 2 else 1

@cache
def assignments(cycles, capacities):
    # Each cycle is a separate factor of a power-sum product.
    if not cycles:
        return int(not any(capacities))
    size = cycles[0]
    total = 0
    for i, room in enumerate(capacities):
        if room >= size:
            rest = capacities[:i] + (room - size,) + capacities[i + 1:]
            total += assignments(cycles[1:], rest)
    return total

@cache
def character(shape, cycles):
    # Frobenius coefficient formula: expand the Vandermonde determinant.
    total = 0
    for perm in permutations(range(len(shape))):
        capacities = tuple(length - i + perm[i] for i, length in enumerate(shape))
        if min(capacities) >= 0:
            total += sign(perm) * assignments(cycles, capacities)
    return total

def blocks(lengths):
    start = 0
    for length in lengths:
        yield tuple(range(start, start + length))
        start += length

def cycle_type(perm):
    seen = set()
    lengths = []
    for start in range(len(perm)):
        if start in seen:
            continue
        i = start
        length = 0
        while i not in seen:
            seen.add(i)
            length += 1
            i = perm[i]
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))

def centralizer_histogram(rho, perms):
    n = sum(rho)
    g = list(range(n))
    for cycle in blocks(rho):
        for i, x in enumerate(cycle):
            g[x] = cycle[(i + 1) % len(cycle)]
    hist = Counter(cycle_type(p) for p in perms if all(p[g[i]] == g[p[i]] for i in range(n)))
    expected_order = prod(k ** m * factorial(m) for k, m in Counter(rho).items())
    assert sum(hist.values()) == expected_order
    return hist

def signed_tabloids(shape, perms):
    # Every unrestricted filling is one term of exactly one column-sorted filling.
    heights = [sum(width > j for width in shape) for j in range(shape[0])]
    columns = list(blocks(heights))
    terms = defaultdict(Counter)
    for filling in perms:
        row_word = [0] * len(filling)
        sorted_filling = []
        coefficient = 1
        for positions in columns:
            entries = tuple(filling[i] for i in positions)
            sorted_filling.extend(sorted(entries))
            coefficient *= sign(entries)
            for row, label in enumerate(entries):
                row_word[label] = row
        terms[tuple(sorted_filling)][tuple(row_word)] += coefficient
    return terms

def necklace_key(word, cycles):
    necklaces = []
    for cycle in cycles:
        w = tuple(word[i] for i in cycle)
        necklaces.append(min(w[j:] + w[:j] for j in range(len(w))))
    return tuple(sorted(necklaces))

def selected_fillings(terms, rho):
    cycles = list(blocks(rho))
    keys = {}
    basis = {}
    chosen = []
    for filling, expansion in sorted(terms.items()):
        vector = Counter()
        for word, coefficient in expansion.items():
            if word not in keys:
                keys[word] = necklace_key(word, cycles)
            vector[keys[word]] += coefficient
        vector = {k: Fraction(v) for k, v in vector.items() if v}
        while vector:
            lead = min(vector)
            factor = vector[lead]
            if lead not in basis:
                basis[lead] = {k: v / factor for k, v in vector.items()}
                chosen.append(filling)
                break
            for k, v in basis[lead].items():
                value = vector.get(k, 0) - factor * v
                if value:
                    vector[k] = value
                else:
                    vector.pop(k, None)
    return chosen

def investigate():
    out = {'complete': False, 'completed_n': [], 'rows': [], 'checked_pairs': 0}
    for n in range(1, n_max + 1):
        parts = list(partitions(n, n))
        perms = list(permutations(range(n)))
        hist = {rho: centralizer_histogram(rho, perms) for rho in parts}
        for rho in parts:
            assert character((n,), rho) == 1
            assert character((1,) * n, rho) == (-1) ** (n - len(rho))
        for shape in parts:
            terms = signed_tabloids(shape, perms)
            row = {'n': n, 'shape': shape, 'by_cycle_type': [], 'character_row_sum': sum(character(shape, rho) for rho in parts)}
            out['rows'].append(row)
            for rho in parts:
                if time.monotonic() >= deadline:
                    out['summary'] = 'Partial exact check. The time guard stopped before the next pair.'
                    return out
                chosen = selected_fillings(terms, rho)
                h = hist[rho]
                numerator = sum(count * character(shape, typ) for typ, count in h.items())
                order = sum(h.values())
                row['by_cycle_type'].append({'rho': rho, 'rank': len(chosen), 'trace_sum': numerator, 'centralizer_order': order})
                if len(chosen) * order != numerator:
                    out['summary'] = 'Rank and centralizer average disagree at the last recorded pair.'
                    return out
                out['checked_pairs'] += 1
                if shape == (3, 2, 1) and rho == (3, 2, 1):
                    out['example'] = {'shape': shape, 'rho': rho, 'selected_fillings_in_column_order': [[x + 1 for x in f] for f in chosen]}
            row['total_selected'] = sum(entry['rank'] for entry in row['by_cycle_type'])
            if row['total_selected'] != row['character_row_sum']:
                out['summary'] = 'Total count and unweighted character row sum disagree at the last recorded shape.'
                return out
            if shape == (n,):
                assert all(entry['rank'] == 1 for entry in row['by_cycle_type'])
            if n == 3 and shape == (2, 1):
                assert row['character_row_sum'] == 1
        out['completed_n'].append(n)
    out['complete'] = True
    out['summary'] = f'Exact agreement for all {out["checked_pairs"]} ordered pairs of partitions of equal size through n={n_max}.'
    return out

with open('result.json', 'w') as output:
    json.dump(investigate(), output)
