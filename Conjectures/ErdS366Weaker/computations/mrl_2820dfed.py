# MathResearchLab experiment 2820dfed-a87a-4924-9613-7021e8beb3d0
# Check both signs of the cubic equation through multiplier height $10^{60}$
# sha256(code) = bb7ace0d2c4293f4234fd59a469d7112f6fdef465b47f1eee0a4e92718e0db7a
# parameters: {"coefficient_limit": 100000, "height": 1000000000000000000000000000000000000000000000000000000000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

body = r'''import json, os
import math
import time

params = json.load(open(os.environ['MRL_PARAMS']))
limit = int(params['coefficient_limit'])
height = int(params['height'])
deadline = time.monotonic() + 95


def check_time():
    if time.monotonic() >= deadline:
        raise TimeoutError('soft time limit reached')


def squarefree(n):
    return all(n % (d * d) for d in range(2, math.isqrt(n) + 1))


def coefficients(bound):
    values = []
    for b in range(1, math.isqrt(math.isqrt(bound)) + 1):
        if squarefree(b):
            c = 1
            while b ** 4 * c ** 5 <= bound:
                if squarefree(c) and math.gcd(b, c) == 1:
                    values.append(b ** 4 * c ** 5)
                c += 1
    if len(values) != len(set(values)):
        raise ArithmeticError('duplicate coefficient')
    return sorted(values)


def cube_root_floor(n):
    low = 0
    high = 1 << ((n.bit_length() + 2) // 3)
    while low + 1 < high:
        mid = (low + high) // 2
        if mid ** 3 <= n:
            low = mid
        else:
            high = mid
    return low


def search_pair(a, b, h):
    scale = 16 * h * h
    target = b * scale ** 3
    z = cube_root_floor(target // a)
    if not a * z ** 3 <= target < a * (z + 1) ** 3:
        raise ArithmeticError('cube-root bracket failed')
    numerator, denominator = z, scale
    p_old, p = 0, 1
    q_old, q = 1, 0
    row = {'A': a, 'B': b, 'method': 'continued_fraction', 'convergents_within_denominator_bound': 0, 'substitutions': 0, 'witnesses': []}
    while denominator:
        quotient, remainder = divmod(numerator, denominator)
        numerator, denominator = denominator, remainder
        p_old, p = p, quotient * p + p_old
        q_old, q = q, quotient * q + q_old
        if q > h:
            row.update(termination='denominator_exceeds_height', first_excluded_denominator=q)
            return row
        row['convergents_within_denominator_bound'] += 1
        if 1 <= p <= h:
            difference = a * p ** 3 - b * q ** 3
            row['substitutions'] += 1
            if abs(difference) == 1:
                row['witnesses'].append([p, q, difference])
    row['termination'] = 'rational_expansion_exhausted'
    return row


rows = []
record = {'parameters': params, 'status': 'started', 'distinct_pair_records': rows, 'sanity': {}, 'coverage_argument': {'author_support': 'proved_here', 'justification': 'Equal coefficients cannot work because distinct positive cubes differ by at least $7$. A common factor of the coefficients divides the difference. For $A<B$, any solution has $x/y$ reduced, since a common divisor of $x,y$ has its cube dividing $1$. It also has $x\u2265 y$: if $x<y$ then $By^3-Ax^3\u2265 y^3-x^3>1$. Put $t=x/y$ and $u=(B/A)^{1/3}>1$. Factoring the difference of cubes gives $|t-u|=1/[Ay^3(t^2+tu+u^2)]<1/(3y^3)$. For $Q=16H^2$ and $z=\u230a Qu\u230b$, the rational $z/Q$ is within $1/Q$ of $u$. Thus $|t-z/Q|<(1/3+1/16)/y^2<1/(2y^2)$ whenever $y\u2264 H$. By Legendre\u2019s continued fraction criterion, the reduced fraction $t$ is a convergent of $z/Q$, including the case of equality $t=z/Q$. The Euclidean algorithm enumerates these convergents exactly with nondecreasing positive denominators. Substitution checks both signs, and swapping the two coefficients just swaps the multipliers and reverses the sign.'}}
try:
    if limit < 1 or height < 1:
        raise ValueError('invalid bounds')
    sanity_height = 15
    sanity_pairs = 0
    signs_seen = set()
    for a in range(1, 45):
        check_time()
        for b in range(a + 1, 46):
            brute = {(x, y, a * x ** 3 - b * y ** 3) for x in range(1, sanity_height + 1) for y in range(1, sanity_height + 1) if abs(a * x ** 3 - b * y ** 3) == 1}
            actual = search_pair(a, b, sanity_height)['witnesses']
            if sorted(brute) != sorted(map(tuple, actual)):
                raise ArithmeticError('brute-force mismatch at %d,%d' % (a, b))
            signs_seen.update(w[2] for w in brute)
            sanity_pairs += 1
    if signs_seen != {-1, 1}:
        raise ArithmeticError('both signs required in positive controls')
    record['sanity'] = {'brute_force_pairs_matched': sanity_pairs, 'max_coefficient': 45, 'height': sanity_height, 'signs_seen': sorted(signs_seen)}
    values = coefficients(limit)
    record['coefficients'] = values
    record['equal_pairs_excluded_by_cube_gap'] = [[v, v] for v in values]
    expected = len(values) * (len(values) - 1) // 2
    record['expected_distinct_pairs'] = expected
    for i, a in enumerate(values):
        for b in values[i + 1:]:
            check_time()
            divisor = math.gcd(a, b)
            if divisor > 1:
                rows.append({'A': a, 'B': b, 'method': 'common_divisor', 'divisor': divisor, 'witnesses': []})
            else:
                rows.append(search_pair(a, b, height))
    if [(r['A'], r['B']) for r in rows] != [(a, b) for a in values for b in values if a < b] or len(rows) != expected:
        raise ArithmeticError('production pair coverage mismatch')
    record['status'] = 'complete'
    record['summary'] = 'Covered %d equal pairs and all %d distinct pairs through multiplier height %d. Found %d witnesses.' % (len(values), expected, height, sum(len(r['witnesses']) for r in rows))
except TimeoutError as error:
    record.update(status='partial', summary=str(error) + '. Only finished pair records count toward coverage.')
except Exception as error:
    record.update(status='failed', summary=type(error).__name__ + ': ' + str(error))
record['finished_distinct_pairs'] = len(rows)
record['continued_fraction_pairs'] = sum(r['method'] == 'continued_fraction' for r in rows)
record['common_divisor_pairs'] = sum(r['method'] == 'common_divisor' for r in rows)
record['program'] = 'body = r' + chr(39) * 3 + body + chr(39) * 3 + '\nexec(body)\n'
with open('result.json', 'w') as output:
    json.dump(record, output)
'''
exec(body)
