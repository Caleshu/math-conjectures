# MathResearchLab experiment a03d294f-9fdd-442d-a0d4-c0a056da1a21
# Exact perfect-power census through $n=20000$
# sha256(code) = 7ea9a4a8fd5858519386c318ca2a2359ef6c240f0ecb6f56829805a86580aef5
# parameters: {"n_max": 20000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from functools import cache
from math import isqrt
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


@cache
def residue_filter(q):
    # A modulus of the form a*q+1 often removes most candidates.
    for a in range(1, 65):
        modulus = a * q + 1
        if is_prime(modulus):
            residues = {pow(b, q, modulus) for b in range(modulus)}
            return modulus, residues
    return 1, {0}  # Pass all integers to the exact root test.


@cache
def tests_for_bits(bits):
    return [(q, *residue_filter(q)) for q in range(2, bits) if is_prime(q)]


def power_witness(v):
    if v < 4:
        return None
    bits = v.bit_length()
    for q, modulus, residues in tests_for_bits(bits):
        if v % modulus not in residues:
            continue
        if q == 2:
            base = isqrt(v)
        else:
            low = 1
            high = 1 << ((bits + q - 1) // q)
            while high - low > 1:
                mid = (low + high) // 2
                if mid ** q <= v:
                    low = mid
                else:
                    high = mid
            base = low
        if base > 1 and base ** q == v:
            return base, q
    return None


def main():
    deadline = monotonic() + 105
    n_max = params['n_max']
    if n_max < 0:
        raise ValueError('n_max must be nonnegative')

    small_limit = 512
    direct_powers = set()
    for base in range(2, isqrt(small_limit) + 1):
        value = base * base
        while value <= small_limit:
            direct_powers.add(value)
            value *= base
    power_errors = []
    for value in range(1, small_limit + 1):
        witness = power_witness(value)
        if (witness is not None) != (value in direct_powers):
            power_errors.append(value)
        elif witness is not None:
            base, exponent = witness
            if base < 2 or exponent < 2 or base ** exponent != value:
                power_errors.append(value)

    check_limit = min(64, n_max)
    by_part_size = [1] + [0] * check_limit
    for part in range(1, check_limit + 1):
        for total in range(part, check_limit + 1):
            by_part_size[total] += by_part_size[total - part]

    terms = []
    k = 1
    while True:
        first = k * (3 * k - 1) // 2
        if first > n_max:
            break
        sign = 1 if k % 2 else -1
        terms.append((first, sign))
        if first + k <= n_max:
            terms.append((first + k, sign))
        k += 1

    partitions = []
    witnesses = []
    for n in range(n_max + 1):
        if monotonic() >= deadline:
            break
        value = int(n == 0)
        for offset, sign in terms:
            if offset > n:
                break
            value += sign * partitions[n - offset]
        witness = power_witness(value)
        if witness is not None:
            witnesses.append([n, *witness])
        partitions.append(value)

    completed = len(partitions) - 1
    checked = min(completed, check_limit)
    partition_errors = [n for n in range(checked + 1) if partitions[n] != by_part_size[n]]
    if power_errors or partition_errors:
        summary = 'Sanity check failed.'
    elif completed < n_max:
        summary = f'Partial perfect-power census through {completed}.'
    else:
        summary = f'Exact perfect-power census through {completed}.'
    return {'summary': summary, 'completed_through': completed,
            'witnesses': witnesses,
            'direct_power_check': {'range': [1, small_limit], 'mismatches': power_errors},
            'partition_check': {'range': [0, checked], 'mismatches': partition_errors}}


with open('result.json', 'w') as output:
    json.dump(main(), output)
