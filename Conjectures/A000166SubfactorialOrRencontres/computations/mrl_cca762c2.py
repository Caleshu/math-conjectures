# MathResearchLab experiment cca762c2-f102-428e-88ec-016ad3abd2e3
# Check the single residue shared by the target class
# sha256(code) = ab76f65ac00436a2eed64840c969617ec79c45fc22404b9d33dbda9e4dc5bb11
# parameters: {"offset": 57}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))

offset = params['offset']
assert offset == 57
residue = 1
checkpoints = {}
for j in range(1, offset + 1):
    residue = (j * residue + (-1) ** j) % 103
    if j == 4:
        assert residue == 9  # D_4 = 9 checks the sign and indexing.
    if j % 10 == 0 or j >= 51:
        checkpoints[str(j)] = residue

sixth_power = pow(residue, 6, 103)
excludes = residue != 0 and sixth_power != 1
result = {
    'summary': 'The residue excludes a seventeenth power.' if excludes else 'The residue test is inconclusive.',
    'offset': offset,
    'modulus': 103,
    'checkpoints': checkpoints,
    'residue': residue,
    'sixth_power_mod_103': sixth_power,
    'matches_supplied_certificate': (residue, sixth_power) == (22, 79),
    'excludes_seventeenth_power': excludes
}
with open('result.json', 'w') as out:
    json.dump(result, out)
