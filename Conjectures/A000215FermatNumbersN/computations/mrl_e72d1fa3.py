# MathResearchLab experiment e72d1fa3-f8dd-4c34-966f-fd7234065d9b
# Exhaustive divisibility test on an interval and a family with bounded odd part
# sha256(code) = f793f7ba4bfb1c89fb624063ce5e08fb8644da6bf113bf2d7f251d57d0d0f607
# parameters: {"n_max": 1000000, "a_max": 256, "odd_part_max": 255}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
n_max = params['n_max']
a_max = params['a_max']
u_max = params['odd_part_max']
assert n_max >= 17 and 4 <= a_max <= 512 and u_max >= 1
deadline = monotonic() + 75


def predicted(m):
    if m & (m - 1):
        return False
    a = m.bit_length() - 1
    return a >= 4 and (a & (a - 1)) == 0


def stage(m):
    if m % 2:
        return 0
    if pow(2, m, m - 1) != 1:
        return 1
    if pow(2, m, m + 1) != 1:
        return 2
    if pow(2, m, m * m + 1) != 1:
        return 3
    return 4


def direct(m):
    return pow(2, m, m**4 - 1) == 1


for m in range(5, 2049):
    assert (stage(m) == 4) == direct(m)
assert direct(16) and not direct(8)
for a in range(3, a_max + 1):
    m = 1 << a
    assert direct(m) == predicted(m)


def new_record():
    return {'tested': 0, 'passed_even': 0, 'passed_m_minus_1': 0, 'also_passed_m_plus_1': 0, 'solutions_n': [], 'counterexamples': []}


def examine(m, record):
    depth = stage(m)
    record['tested'] += 1
    record['passed_even'] += int(depth >= 1)
    record['passed_m_minus_1'] += int(depth >= 2)
    record['also_passed_m_plus_1'] += int(depth >= 3)
    actual = depth == 4
    expected = predicted(m)
    if actual:
        assert direct(m)
        record['solutions_n'].append(m + 1)
    if actual != expected:
        assert direct(m) == actual
        record['counterexamples'].append({'n': m + 1, 'divides': actual, 'fermat_form': expected, 'residue_mod_full_divisor': pow(2, m, m**4 - 1)})


interval = new_record()
last_n = 5
for n in range(6, n_max + 1):
    if n % 1024 == 0 and monotonic() >= deadline:
        break
    examine(n - 1, interval)
    last_n = n

family = new_record()
last_pair = None
family_complete = True
for a in range(1, a_max + 1):
    for u in range(1, u_max + 1, 2):
        if monotonic() >= deadline:
            family_complete = False
            break
        m = u << a
        if m + 1 > n_max:
            examine(m, family)
        last_pair = [a, u]
    if not family_complete:
        break

result = {
    'summary': f"The consecutive search reached n={last_n}. The additional family contributed {family['tested']} tests. There were {len(interval['counterexamples']) + len(family['counterexamples'])} mismatches in the cases examined.",
    'sanity_checks_passed': True,
    'interval_complete': last_n == n_max,
    'interval_last_n': last_n,
    'interval': interval,
    'additional_family_complete': family_complete,
    'additional_family_last_pair_a_u': last_pair,
    'additional_family': family,
    'method_claim': {'claim': 'The successive tests exactly decide the divisibility for every examined input.', 'author_support': 'proved_here', 'justification': 'Put $m=n-1\\ge5$. For odd $m$, the divisor is even and $2^m-1$ is odd. For even $m$, the factors $m-1,m+1,m^2+1$ are odd and pairwise coprime: any shared prime would divide $2$, by subtraction or by substituting $m\\equiv\\pm1$ into $m^2+1$. Their product is $m^4-1$, so all three modular tests together are equivalent to the original divisibility.'}
}
with open('result.json', 'w') as output:
    json.dump(result, output)
