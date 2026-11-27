# MathResearchLab experiment dba32a57-3adf-4b35-9fa1-cd2bb8312b6d
# Exact lookup from historical registry rows
# sha256(code) = 7d5cb5d4babff61d1dd6e683964097319f0456f25d14033bc3cf1a9ffdffec58
# parameters: {"historical_rows": []}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))

TARGET = (4, 4, 4, 8, 16, 32, 60)
REPORTED_SIZE = 28387

# Each row has a key and optionally its original zero-based rank in the
# full lexicographic ordering of distinct keys. Unranked rows also work.
def lookup(rows, target, size):
    keys = set()
    ranked = {}
    for row in rows:
        key = tuple(row['key'])
        if (len(key) != 7 or any(type(x) is not int or x <= 0 or x % 2 for x in key)
                or sum(key) != 128 or tuple(sorted(key)) != key):
            raise ValueError('Expected an exact sorted Q7 histogram')
        keys.add(key)
        if row.get('rank') is not None:
            rank = row['rank']
            if type(rank) is not int or not 0 <= rank < size:
                raise ValueError('Invalid full-registry rank')
            if rank in ranked and ranked[rank] != key:
                raise ValueError('Conflicting keys at one rank')
            ranked[rank] = key
    ordered = sorted(ranked.items())
    if len(keys) > size or any(a[1] >= b[1] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('Rows conflict with the stated registry ordering or size')
    if target in keys:
        return 'present', {'matching_key': target}
    for (i, a), (j, b) in zip(ordered, ordered[1:]):
        if j == i + 1 and a < target < b:
            return 'absent', {'consecutive_rows': [[i, a], [j, b]]}
    if ordered:
        i, a = ordered[0]
        j, b = ordered[-1]
        if i == 0 and target < a:
            return 'absent', {'first_row': [i, a]}
        if j == size - 1 and b < target:
            return 'absent', {'last_row_at_reported_size': [j, b]}
    if len(keys) == size:
        return 'absent', {'distinct_keys_scanned': size, 'assumed_registry_size': size}
    return 'unresolved', {'distinct_keys_examined': len(keys), 'ranked_keys_examined': len(ranked)}

# Exercise the distinction between consecutive source ranks and consecutive
# entries in an excerpt. These fixtures never enter the historical lookup.
lo = [4, 4, 4, 8, 16, 30, 62]
hi = [4, 4, 4, 8, 16, 34, 58]
assert lookup([{'key': TARGET}], TARGET, 5)[0] == 'present'
assert lookup([{'rank': 1, 'key': lo}, {'rank': 2, 'key': hi}], TARGET, 5)[0] == 'absent'
assert lookup([{'rank': 1, 'key': lo}, {'rank': 3, 'key': hi}], TARGET, 5)[0] == 'unresolved'

rows = params['historical_rows']
status, evidence = lookup(rows, TARGET, REPORTED_SIZE)
result = {'summary': {'present': 'A supplied historical row matches the target.', 'absent': 'The supplied historical evidence excludes the target under the stated registry premises.', 'unresolved': 'The supplied historical rows do not decide membership.'}[status], 'registry': 'E-5eebf3', 'target': TARGET, 'status': status, 'historical_rows_supplied': len(rows), 'evidence': evidence}
with open('result.json', 'w') as out:
    json.dump(result, out)
