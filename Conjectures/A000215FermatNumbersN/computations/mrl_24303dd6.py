# MathResearchLab experiment 24303dd6-1ac0-4edf-bd27-d8297085b4b6
# Exhaustive scan for the reverse direction of Part 3
# sha256(code) = 655f7121024194f79a16a375366a98733fff858d7210d3911a7d6476ada5be74
# parameters: {"lower_exclusive": 10000000, "upper_inclusive": 1000000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import math
import time
import numpy as np

started = time.monotonic()
params = json.load(open(os.environ['MRL_PARAMS']))
lo = int(params['lower_exclusive'])
hi = int(params['upper_inclusive'])
if not 1 <= lo < hi <= 10**9:
    raise ValueError('Require 1 <= lower_exclusive < upper_inclusive <= 10^9')
U = np.uint64

# For m=4j, sieve necessary conditions from prime divisors of d=m-1.
# Each rule stores p, the j residue for p|d, ord_p(16), and the first
# nonnegative j satisfying both p|d and 16^j=1 mod p.
def make_rules(limit):
    least = list(range(limit + 1))
    for p in range(2, math.isqrt(limit) + 1):
        if least[p] == p:
            for z in range(p*p, limit + 1, p):
                if least[z] == z:
                    least[z] = p
    rules = []
    for p in range(3, limit + 1, 2):
        if least[p] != p:
            continue
        order = remaining = p - 1
        while remaining > 1:
            f = least[remaining]
            remaining //= f
            if order % f == 0 and pow(16, order // f, p) == 1:
                order //= f
        b = pow(4, -1, p)
        good = order * ((b * pow(order, -1, p)) % p)
        rules.append((p, b, order, good))
    return rules

# Exact uint64 left-to-right binary powering for moduli <= 10^9+1.
# Each step forms at most 2*(modulus-1)^2 before reduction.
def residues(exponents, moduli):
    if not exponents.size:
        return exponents.copy()
    shift = max(0, int(exponents.max()).bit_length() - 5)
    r = (U(1) << (exponents >> U(shift))) % moduli
    for k in reversed(range(shift)):
        bit = (exponents >> U(k)) & U(1)
        r = ((r * r) << bit) % moduli
    return r

# For q=m^2+1 the square of a residue may exceed uint64. Compute the
# square by modular addition. Every addition is < 2q < 2^61.
def square_mod(x, q):
    multiplier = int(x)
    total = U(0)
    while multiplier:
        if multiplier & 1:
            total = total + x
            if total >= q:
                total = total - q
        multiplier >>= 1
        x = x + x
        if x >= q:
            x = x - q
    return total

def last_residue(m):
    q = U(m) * U(m) + U(1)
    r = U(1)
    for k in reversed(range(m.bit_length())):
        r = square_mod(r, q)
        if (m >> k) & 1:
            r = r + r
            if r >= q:
                r = r - q
    return int(r)

def scan_block(first, stop, rules):
    # The half-open block is in j=m/4. A prime divisor contributes 1
    # when its order condition passes and 32 when it fails. Fewer than
    # 30 distinct primes divide d<2^30, so uint16 scores are exact.
    size = stop - first
    score = np.zeros(size, dtype=np.uint16)
    for p, b, order, good in rules:
        offset = (b - first) % p
        if offset >= size:
            continue
        if order == 1:
            score[offset::p] += 1
        else:
            score[offset::p] += 32
            step = p * order
            offset = (good - first) % step
            if offset < size:
                score[offset::step] -= 31
    indices = np.flatnonzero((score > 0) & (score < 32)).astype(U)
    m = (indices + U(first)) * U(4)
    passed_minus = m[residues(m, m - U(1)) == U(1)]
    passed_plus = passed_minus[residues(passed_minus, passed_minus + U(1)) == U(1)]
    hits = [int(x) for x in passed_plus if last_residue(int(x)) == 1]
    return len(m), passed_minus, passed_plus, hits

def run():
    rules = make_rules(math.isqrt(max(hi, 10000)))
    # Compare the sets at BOTH intermediate stages and at final acceptance.
    # The final reference uses the literal unreduced integers for all m,
    # including odd m and m=2 mod 4. At m=1, zero does not divide one.
    _, minus, plus, hits = scan_block(1, 10000 // 4 + 1, rules)
    reference = [[], [], []]
    for m in range(1, 10001):
        numerator = (1 << m) - 1
        if m % 4 == 0 and numerator % (m - 1) == 0:
            reference[0].append(m)
            if numerator % (m + 1) == 0:
                reference[1].append(m)
        divisor = m**4 - 1
        if divisor and numerator % divisor == 0:
            reference[2].append(m)
    actual = [minus.tolist(), plus.tolist(), hits]
    if actual != reference or hits != [16, 256]:
        return {'summary': 'Small-range validation failed.', 'status': 'VALIDATION_FAILED', 'actual': actual, 'reference': reference}

    # Exercise fixed-width arithmetic near the upper endpoint as well.
    probes = np.array([999999996, 1000000000], dtype=U)
    for moduli in (probes - U(1), probes + U(1)):
        expected = [pow(2, int(x), int(q)) for x, q in zip(probes, moduli)]
        if residues(probes, moduli).tolist() != expected:
            return {'summary': 'Large-modulus validation failed for a linear factor.', 'status': 'VALIDATION_FAILED'}
    for x in probes.tolist():
        if last_residue(x) != pow(2, x, x*x + 1):
            return {'summary': 'Large-modulus validation failed for the quadratic factor.', 'status': 'VALIDATION_FAILED'}

    first = lo // 4 + 1
    end = hi // 4 + 1
    counts = dict(multiples_of_four=0, after_prime_sieve=0, passed_m_minus_1=0, also_passed_m_plus_1=0)
    solutions = []
    while first < end and time.monotonic() - started < 108:
        stop = min(first + (1 << 20), end)
        sieved, minus, plus, hits = scan_block(first, stop, rules)
        counts['multiples_of_four'] += stop - first
        counts['after_prime_sieve'] += sieved
        counts['passed_m_minus_1'] += len(minus)
        counts['also_passed_m_plus_1'] += len(plus)
        solutions.extend(hits)
        first = stop
    complete = first == end
    through = hi if complete else min(hi, 4*first - 1)
    if counts['multiples_of_four'] != through // 4 - lo // 4:
        return {'summary': 'Coverage accounting failed.', 'status': 'VALIDATION_FAILED'}
    status = 'NONEMPTY' if solutions else ('EMPTY' if complete else 'PARTIAL')
    return {'summary': f'{status}. Exhaustively checked {lo} < m <= {through} and found {len(solutions)} solutions there.', 'status': status, 'complete': complete, 'requested_bounds_open_closed': [lo, hi], 'checked_bounds_open_closed': [lo, through], 'unexamined_bounds_open_closed': None if complete else [through, hi], 'counts': counts, 'solutions': solutions, 'validation': {'literal_bounds_closed': [1, 10000], 'literal_solutions': reference[2], 'intermediate_stages_match': True, 'large_arithmetic_probes': probes.tolist()}, 'author_support': 'proved_here', 'justification': 'Exact enumeration on the reported checked interval using the stated necessary filters and all three pairwise coprime factors.'}

with open('result.json', 'w') as out:
    json.dump(run(), out)
