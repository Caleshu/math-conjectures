# MathResearchLab experiment d1f17c70-e2d7-453d-ac0b-cd69543a61a9
# Independent check of square-free Hamiltonian cycles of Q8, Q9, Q10
# sha256(code) = e71d8cbbb2038abcf2458a2447e957514b09c7915dd676ba0bbff51fea8f0383
# parameters: {"cycles": {"Q8": ["00000000", "00001000", "00001001", "00001011", "00011011", "00010011", "10010011", "10010001", "10110001", "10111001", "00111001", "00101001", "00100001", "10100001", "10100011", "10000011", "10001011", "10001111", "11001111", "11011111", "11011101", "10011101", "10010101", "00010101", "00010111", "00110111", "01110111", "01100111", "01101111", "11101111", "11101110", "11001110", "11001100", "11011100", "11111100", "11111000", "10111000", "10111010", "10111011", "10011011", "11011011", "01011011", "01011010", "01111010", "01111000", "01111001", "01110001", "01100001", "01100000", "01100100", "01100110", "11100110", "10100110", "10100100", "10100101", "10110101", "11110101", "11110001", "11110000", "11100000", "10100000", "10101000", "00101000", "01101000", "01001000", "01001100", "01000100", "01010100", "00010100", "00010000", "00010001", "00000001", "01000001", "01000101", "01000111", "11000111", "11000110", "11010110", "11011110", "11011010", "11011000", "01011000", "01010000", "01110000", "00110000", "10110000", "10110100", "10010100", "10010110", "00010110", "00011110", "00111110", "00111111", "00111011", "01111011", "01101011", "01101001", "01101101", "01001101", "00001101", "10001101", "10001100", "10101100", "10111100", "10111101", "10111111", "10101111", "10100111", "00100111", "00100110", "00000110", "01000110", "01000010", "01000000", "11000000", "11001000", "10001000", "10001010", "10101010", "10101110", "00101110", "01101110", "01101010", "01100010", "01110010", "01110011", "11110011", "10110011", "10110111", "10110110", "10111110", "11111110", "01111110", "01110110", "01010110", "01010111", "01010011", "01010001", "11010001", "11011001", "11111001", "11111011", "11111111", "11110111", "11010111", "10010111", "10000111", "10000101", "10000001", "10000000", "10010000", "11010000", "11010100", "11010101", "11000101", "11001101", "11001001", "01001001", "01011001", "00011001", "00011101", "00111101", "00110101", "00110001", "00110011", "
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 300, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 2405, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/MathResearchLab/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

"""Independent check of claimed square-free Hamiltonian cycles of Q_n, written from the definition.
Input: params["cycles"] = {name: [binary vertex strings, cyclic order]}.
A cycle has an inscribed square iff two of its edges are opposite edges of a 4-cycle of Q_n:
both edges in the same direction i, and their endpoint pairs differ in exactly one other coordinate j != i.
Squares are counted by brute force over all edge pairs (no shortcuts shared with any other checker)."""
import json, os
from itertools import combinations
params = json.load(open(os.environ["MRL_PARAMS"]))
out = {}
for name, seq in params["cycles"].items():
    n = len(seq[0]); N = len(seq); r = {"n": n, "vertices": N}
    v = [int(s, 2) for s in seq]
    r["all_strings_length_n"] = all(len(s) == n and set(s) <= {"0", "1"} for s in seq)
    r["length_is_2^n"] = N == 2 ** n
    r["all_distinct"] = len(set(v)) == N
    edges = []
    ok_adj = True
    for k in range(N):
        a, b = v[k], v[(k + 1) % N]
        d = a ^ b
        if d == 0 or d & (d - 1):
            ok_adj = False
        edges.append((a, b))
    r["consecutive_differ_in_one_bit"] = ok_adj
    r["hamiltonian_cycle"] = r["length_is_2^n"] and r["all_distinct"] and ok_adj and r["all_strings_length_n"]
    squares = 0; example = None
    for (a, b), (c, d) in combinations(edges, 2):
        if (a ^ b) != (c ^ d):
            continue  # different directions
        x = min(a, b) ^ min(c, d)  # the two edges as unordered pairs, compared at their "0" end in direction i
        if x and not (x & (x - 1)):
            squares += 1
            example = example or [format(t, f"0{n}b") for t in (a, b, c, d)]
    r["inscribed_squares"] = squares
    r["first_square"] = example
    r["square_free_hamiltonian_cycle"] = r["hamiltonian_cycle"] and squares == 0
    out[name] = r
json.dump(out, open("result.json", "w"), indent=1)
print(json.dumps({k: (v["hamiltonian_cycle"], v["inscribed_squares"]) for k, v in out.items()}))
