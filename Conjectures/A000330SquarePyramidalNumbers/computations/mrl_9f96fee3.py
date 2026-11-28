# MathResearchLab experiment 9f96fee3-3f25-4cee-b532-ed5962e1e61f
# Search beyond the cutoff by fixing the sum of two indices
# sha256(code) = f44231a3d1618dbe673810504da3a19d8d992cbfe8aeee0389d0f34927c09645
# parameters: {"small_index_bound": 20000, "pair_sum_bound": 128, "third_index_bound": 20000000, "seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import isqrt
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
H = int(params['small_index_bound'])
K = int(params['pair_sum_bound'])
L = int(params['third_index_bound'])
assert 0 <= H < L and 0 <= K <= 128
started = monotonic()
deadline = started + min(100.0, float(params['seconds']))

def P(n):
    return (25*n**3 + 3*n*n - 22*n) // 6

def f(x):
    return x**3 - 553*x

wheel = 25*7*11
squares = {i*i % wheel for i in range(wheel)}
p_table = [P(i) % wheel for i in range(wheel)]

def exact_pair(t, c, target):
    s = 25*t+2
    quotient, remainder = divmod(8*(P(c)+P(t)-target), s)
    if remainder or quotient > t*t:
        return None
    disc = t*t-quotient
    d = isqrt(disc)
    if d*d != disc or (t-d) % 2:
        return None
    a, b = (t+d)//2, (t-d)//2
    assert P(a)+P(b)+P(c) == target
    return a, b

def sieve(t, target):
    s = 25*t+2
    modulus = abs(s)
    C = 3750*target - 1656
    roots = [i for i in range(modulus) if (C-f(25*i+1)) % modulus == 0]
    constant = s*s*t*t - 8*s*(P(t)-target)
    allowed = [(constant-8*s*v) % wheel in squares for v in p_table]
    return modulus, roots, allowed

# Plant triples in the full sieve and reconstruction, including indices beyond H.
planted = [(0, 0, 0), (1, 1, -4), (H+13, -H-12, -H-7), (H+17, -H-20, H+2)]
for a, b, c in planted:
    t = a+b
    target = P(a)+P(b)+P(c)
    modulus, roots, allowed = sieve(t, target)
    assert c % modulus in roots and allowed[c % wheel]
    assert exact_pair(t, c, target) == (max(a,b), min(a,b))

completed_t = []
active_t = None
witness = None
exact_tests = 0
class BudgetExpired(Exception):
    pass

try:
    for t in sorted(range(-K, K+1), key=abs):
        active_t = t
        if monotonic() >= deadline:
            raise BudgetExpired
        modulus, roots, allowed = sieve(t, -2)
        stride = modulus*wheel
        if any(allowed):
            for root in roots:
                for j in range(wheel):
                    if j % 64 == 0 and monotonic() >= deadline:
                        raise BudgetExpired
                    residue = root + modulus*j
                    if not allowed[residue % wheel]:
                        continue
                    for lo, hi in ((-L, -H-1), (H+1, L)):
                        first = lo + (residue-lo) % stride
                        for c in range(first, hi+1, stride):
                            exact_tests += 1
                            if exact_tests % 8192 == 0 and monotonic() >= deadline:
                                raise BudgetExpired
                            pair = exact_pair(t, c, -2)
                            if pair is not None and min(map(abs, pair)) > H:
                                witness = [pair[0], pair[1], c]
                                break
                        if witness is not None:
                            break
                    if witness is not None:
                        break
                if witness is not None:
                    break
        if witness is not None:
            break
        completed_t.append(t)
        active_t = None
except BudgetExpired:
    pass

complete = len(completed_t) == 2*K+1
if witness is not None:
    summary = 'Verified exterior witness. Together with a complete small-index exclusion this refutes the lemma.'
elif complete:
    summary = 'The specified pair-sum and third-index region is exhausted without an exterior witness.'
else:
    summary = 'Partial exterior search. Only the listed completed pair sums are fully excluded in the specified third-index range.'
result = {'summary': summary, 'r': 27, 'target': -2, 'strict_lower_bound_on_all_absolute_indices': H, 'pair_sum_bound': K, 'third_index_bound': L, 'completed_pair_sums': completed_t, 'interrupted_or_successful_pair_sum': active_t, 'region_exhausted': complete, 'exact_candidates_tested': exact_tests, 'witness': witness, 'planted_triples_validated': len(planted), 'seconds': monotonic()-started}
with open('result.json', 'w') as out:
    json.dump(result, out)