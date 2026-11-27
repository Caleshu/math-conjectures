# MathResearchLab experiment 270c59ed-7a04-4553-8eb5-d3c4dcb93473
# Congruence obstructions for every polygon parameter
# sha256(code) = 31d5ab5814b620fd8d9f4bebd734d80e1648936e13d78a0622716be7f7db8d6e
# parameters: {"modulus_max": 100}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from time import monotonic

params = json.load(open(os.environ['MRL_PARAMS']))
M = params['modulus_max']
assert M >= 2
deadline = monotonic() + 85

def triple_image(residues, m):
    full = (1 << m) - 1
    bits = 1  # Only zero is reachable before adding a summand.
    for _ in range(3):
        expanded = 0
        for v in residues:
            expanded |= ((bits << v) & full) | (bits >> (m - v))
        bits = expanded
    return bits

# Cubes modulo nine give a known non-full image, exercising both missing residues.
cubes = {n ** 3 % 9 for n in range(9)}
cube_image = triple_image(cubes, 9)
assert [t for t in range(9) if not ((cube_image >> t) & 1)] == [4, 5]
rows = []
obstructions = []
for m in range(2, M + 1):
    if monotonic() >= deadline:
        break
    # Build the two coefficients by addition, checking the closed form separately.
    cubic, triangular = 0, 0
    coeffs = []
    for n in range(6 * m):
        assert cubic == (n + 1) * n * (n - 1) // 6
        assert triangular == n * (n + 1) // 2
        coeffs.append((cubic % m, triangular % m))
        cubic += triangular
        triangular += n + 1
    assert cubic % m == triangular % m == 0
    min_size = m
    worst_d = 0
    obstructed = 0
    for d in range(m):
        residues = {(d * a + b) % m for a, b in coeffs}
        image = triple_image(residues, m)
        if m <= 10:
            naive = {(x + y + z) % m for x in residues for y in residues for z in residues}
            assert image == sum(1 << v for v in naive)
        size = image.bit_count()
        if size < min_size:
            min_size, worst_d = size, d
        if size < m:
            obstructed += 1
            missing = [t for t in range(m) if not ((image >> t) & 1)]
            r_example = 2 + (d if d else m)
            obstructions.append({'m': m, 'r_minus_2_mod_m': d, 'missing_z_mod_m': missing, 'counterexample': {'r': r_example, 'z': missing[0]}})
    rows.append({'m': m, 'parameter_classes_checked': m, 'obstructed_classes': obstructed, 'smallest_triple_image_size': min_size, 'attaining_r_minus_2_mod_m': worst_d})

result = {'summary': f'Checked every parameter class for {len(rows)} consecutive moduli starting at 2. Found {len(obstructions)} obstructed modulus-parameter pairs.', 'parameters': params, 'completed_all': len(rows) == M - 1, 'sanity_checks': 'Checked the cube obstruction modulo nine, the two coefficient recurrences against the closed forms, and bitset addition against explicit triples through modulus ten where tested.', 'by_modulus': rows, 'obstructions': obstructions}
with open('result.json', 'w') as out:
    json.dump(result, out)
