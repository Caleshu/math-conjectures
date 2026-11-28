# MathResearchLab experiment f6182628-b9b9-4acd-a508-a0391adb6b10
# Exhaustive divisibility check through $10^7$
# sha256(code) = 0dc6391ce91c0a3af7f07c021a91b73106fcbf0ceb714fa9905bccaeb53eff40
# parameters: {"m_max": 10000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time

params = json.load(open(os.environ["MRL_PARAMS"]))
limit = params['m_max']
assert limit == 10_000_000

def passes(m):
    if m % 2:
        return False
    if m > 2 and pow(2, m, m - 1) != 1:
        return False
    return pow(2, m, m**4 - 1) == 1

# Compare against literal integer division on a range containing two predicted hits.
for m in range(2, 257):
    assert passes(m) == ((2**m - 1) % (m**4 - 1) == 0)
assert passes(16) and passes(256) and passes(65536)

hits = []
checked_through = 0
deadline = time.monotonic() + 90
block = 100_000
for lo in range(1, limit + 1, block):
    if time.monotonic() >= deadline:
        break
    hi = min(lo + block - 1, limit)
    for m in range(lo + lo % 2, hi + 1, 2):
        if passes(m):
            hits.append(m)
    checked_through = hi

complete = checked_through == limit
result = {
    'summary': f'Exhaustively checked positive m through {checked_through} of {limit}. Found {len(hits)} hits.',
    'complete': complete,
    'checked_through': checked_through,
    'hits': hits,
    'matches_prediction': hits == [16, 256, 65536] if complete else None
}
with open('result.json', 'w') as out:
    json.dump(result, out)
