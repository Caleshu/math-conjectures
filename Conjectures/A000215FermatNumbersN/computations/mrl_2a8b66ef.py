# MathResearchLab experiment 2a8b66ef-a1da-4bee-889d-5be65d487ebb
# Exact primality decisions and small-factor certificates for Fermat numbers
# sha256(code) = 8b07776e6a03be67a4d7e1048d1e89ea677b30c4ab83ce84922f24c93f0bed9a
# parameters: {"prime_max": 13, "factor_max": 64, "k_max": 16384, "candidate_divisors": {"7": [59649589127497217], "8": [1238926361552897], "13": [2710954639361]}}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
prime_max = params['prime_max']
factor_max = params['factor_max']
k_max = params['k_max']
assert 5 <= prime_max <= 14 and prime_max <= factor_max <= 128 and k_max >= 1
started = monotonic()
deadline = started + 75


def pepin(n):
    length = 1 << n
    fermat = (1 << length) + 1
    if n == 0:
        return True, None
    residue = pow(3, 1 << (length - 1), fermat)
    return residue == fermat - 1, hex(residue)


def trial_prime(value):
    return all(value % d for d in range(2, isqrt(value) + 1))


def below_bound(q, n):
    exponent = max(0, (1 << n) // 2 - n - 2)
    return (q // 3).bit_length() <= exponent


def proper_divisor(q, n):
    length = 1 << n
    return q > 1 and q.bit_length() <= length and pow(2, length, q) == q - 1


for n in range(6):
    value = (1 << (1 << n)) + 1
    assert pepin(n)[0] == trial_prime(value)
for n in range(9):
    bound = 3 << max(0, (1 << n) // 2 - n - 2)
    assert below_bound(bound - 1, n) and not below_bound(bound, n)
assert proper_divisor(641, 5) and not proper_divisor(643, 5)

primality = []
for n in range(prime_max + 1):
    if monotonic() >= deadline:
        break
    prime, residue = pepin(n)
    primality.append({'n': n, 'prime': prime, 'pepin_residue_hex': residue})

factor_rows = []
hints = params['candidate_divisors']
for n in range(5, factor_max + 1):
    if monotonic() >= deadline:
        break
    stride = 1 << (n + 2)
    last_k = 0
    minimum = None
    witness = None
    for k in range(1, k_max + 1):
        if k % 256 == 0 and monotonic() >= deadline:
            break
        last_k = k
        q = stride * k + 1
        if proper_divisor(q, n):
            minimum = q
            if below_bound(q, n):
                witness = q
            break
    checked_hints = []
    if minimum is None:
        for q in hints.get(str(n), []):
            divides = proper_divisor(q, n)
            checked_hints.append({'q': q, 'proper_divisor': divides})
            if divides and below_bound(q, n):
                witness = q
                break
    if witness is not None or minimum is not None:
        if n < len(primality):
            assert not primality[n]['prime']
    if minimum is not None:
        bound_status = 'verified' if witness is not None else 'counterexample'
    else:
        bound_status = 'verified' if witness is not None else 'unresolved'
    factor_rows.append({'n': n, 'consecutive_k_checked': last_k, 'min_prime_factor_if_proved': minimum, 'checked_hints': checked_hints, 'divisor_below_bound': witness, 'bound_status': bound_status, 'scan_finished': minimum is not None or last_k == k_max})

complete = len(primality) == prime_max + 1 and len(factor_rows) == factor_max - 4 and all(row['scan_finished'] for row in factor_rows)
result = {
    'summary': f"Decided primality for {len(primality)} indices and certified the strict bound for {sum(r['bound_status'] == 'verified' for r in factor_rows)} indices. See per-index coverage.",
    'requested_work_complete': complete,
    'sanity_checks_passed': True,
    'primality': primality,
    'factors': factor_rows,
    'method_claims': [
        {'claim': 'The Pepin decision is exact.', 'author_support': 'proved_here', 'justification': 'For $n=0$, $F_0=3$. For $n\\ge1$, $F_n\\equiv5\\pmod{12}$. If prime, quadratic reciprocity gives $(3/F_n)=-1$, so Euler’s criterion gives residue $-1$. Conversely, that residue implies for each prime $p\\mid F_n$ that the order of $3$ modulo $p$ divides $F_n-1$ and does not divide $(F_n-1)/2$. Since $F_n-1$ is a power of two, this order is $F_n-1$, forcing $p\\ge F_n$.'},
        {'claim': 'The first proper divisor in the consecutive scan is the least prime factor.', 'author_support': 'proved_here', 'justification': 'For $n\\ge2$ and prime $p\\mid F_n$, $2^{2^n}\\equiv-1\\pmod p$, so the order of $2$ is $2^{n+1}$. Hence $p\\equiv1\\pmod8$. The supplementary law for $2$ and Euler’s criterion then imply that the order divides $(p-1)/2$. Thus $2^{n+2}\\mid p-1$, so the scan includes the least prime factor before any larger divisor. Any separately verified proper divisor below the bound also bounds the least prime factor from above.'}
    ]
}
with open('result.json', 'w') as output:
    json.dump(result, output)
