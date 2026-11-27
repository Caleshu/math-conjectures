# MathResearchLab experiment 6b0a2eef-a0e4-49ba-bb78-58ecf947fd05
# Look up one histogram in the fixed E-5eebf3 register
# sha256(code) = bd0a8573cf8d03c412f61c15c4fdf508ec9d20c71de52664b5ef937f42c12fc1
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))

from itertools import accumulate

TARGET = (4, 4, 4, 8, 16, 32, 60)
REGISTER_SIZE = 28387

def admissible(key):
    return (len(key) == 7
            and all(type(x) is int and x % 2 == 0 for x in key)
            and tuple(sorted(key)) == tuple(key)
            and sum(key) == 128
            and all(total >= 2 ** k for k, total in enumerate(accumulate(key), 1)))

def lookup(rows, expected_size):
    seen = set()
    hit = None
    for index, row in enumerate(rows):
        if not isinstance(row, list) or not admissible(row):
            raise ValueError(f'Invalid sorted registration key at zero-based row {index}')
        key = tuple(row)
        seen.add(key)
        if key == TARGET and hit is None:
            hit = index
    if len(seen) > expected_size:
        raise ValueError('Distinct key count exceeds the reported register size')
    in_residual = False if hit is not None else (True if len(seen) == expected_size else None)
    return in_residual, hit, len(seen)

# Exercise a hit, a complete miss, and an incomplete miss with duplicate rows.
other = [2, 4, 4, 8, 16, 32, 62]
assert lookup([other, list(TARGET)], 2) == (False, 1, 2)
assert lookup([other], 1) == (True, None, 1)
assert lookup([other, other], 2) == (None, None, 1)
assert admissible(TARGET) and not admissible([2, 2, 2, 16, 16, 32, 58])

result = {'target': list(TARGET), 'prefix_sums': list(accumulate(TARGET)), 'target_in_U': True, 'reported_register_size': REGISTER_SIZE, 'target_in_fixed_residual': None, 'remaining_after_adding_target_given_reported_counts': None, 'sanity_checks_passed': True}
rows = params.get('registered_keys')
if rows is None:
    result.update(status='MISSING_INPUT', summary='No fixed registration keys supplied. Membership is undecided.')
else:
    try:
        if not isinstance(rows, list):
            raise ValueError('registered_keys must be an array of sorted keys')
        member, hit, count = lookup(rows, REGISTER_SIZE)
        result.update(distinct_keys_supplied=count, first_matching_row_zero_based=hit, target_in_fixed_residual=member)
        if member is None:
            result.update(status='INCOMPLETE', summary='No match in the supplied portion of the register. Membership is undecided.')
        else:
            result.update(status='DECIDED', remaining_after_adding_target_given_reported_counts=69-int(member), summary=('Absent from the complete fixed register. The target belongs to its residual.' if member else 'Matching fixed registration key found. The target was already covered.'))
    except ValueError as exc:
        result.update(status='INVALID_INPUT', summary=str(exc))

with open('result.json', 'w') as out:
    json.dump(result, out)
