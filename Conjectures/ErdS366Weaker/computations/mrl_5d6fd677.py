# MathResearchLab experiment 5d6fd677-ecbd-450e-ae2e-b9f514316b73
# Audit the field roster and the uniform exponent inequality
# sha256(code) = 7ca0dfd1108e38db68aa0505c4b7553a83094ca91c385aeadb5f15fc055bb116
# parameters: {"groups": [[1, [[16, 1, 2], [32, 1, 2], [81, 1, 3], [243, 1, 3], [625, 1, 5], [3125, 1, 5], [1296, 1, 6], [7776, 1, 6], [2401, 1, 7], [16807, 1, 7], [2592, 2, 3], [3888, 2, 3], [10000, 1, 10], [100000, 1, 10], [14641, 1, 11], [20000, 2, 5], [50000, 2, 5], [28561, 1, 13], [38416, 1, 14], [50625, 1, 15], [76832, 2, 7], [83521, 1, 17]]], [16, [[83521, 2, 17]]], [32, [[625, 1, 10], [83521, 1, 34]]], [81, [[10000, 3, 10], [83521, 3, 17], [100000, 1, 30]]], [243, [[10000, 1, 30], [83521, 1, 51]]], [625, [[28561, 5, 13], [83521, 5, 17]]], [1296, [[83521, 6, 17]]], [2592, [[83521, 3, 34]]], [3125, [[83521, 1, 85]]], [3888, [[83521, 2, 51]]], [7776, [[83521, 1, 102]]], [10000, [[14641, 10, 11], [83521, 10, 17]]], [14641, [[83521, 11, 17], [100000, 1, 110]]], [16807, [[50000, 5, 14]]], [20000, [[83521, 5, 34]]], [28561, [[38416, 13, 14]]], [50000, [[83521, 2, 85]]], [50625, [[76832, 7, 30], [83521, 15, 17]]], [83521, [[100000, 1, 170]]]]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from fractions import Fraction
from math import factorial, gcd, prod
from itertools import permutations
from collections import Counter
import sympy as sp

params = json.load(open(os.environ["MRL_PARAMS"]))

def field_key(A, B):
    # A^2 B and B/A differ by the rational cube A^3.
    factors = sp.factorint(A*A*B)
    parts = [prod(int(p) for p, v in factors.items() if v % 3 == i) for i in (1, 2)]
    return sorted(parts)

def exp_lower(x, degree):
    return sum(Fraction(x**j, factorial(j)) for j in range(degree + 1))

# The symbolic norm below is for c0+c1*t+c2*t^2, with t^3=B/A.
A, B, X, Y = sp.symbols('A B X Y', nonzero=True)
t = sp.Symbol('t')
q = B/A
cubic = sp.Poly(A*(X-t*Y)**3, t, domain=sp.EX)
reduced = cubic.rem(sp.Poly(t**3-q, t, domain=sp.EX))
c0, c1, c2 = (reduced.nth(i) for i in range(3))
difference = A*X**3-B*Y**3
norm = c0**3+q*c1**3+q**2*c2**3-3*q*c0*c1*c2
trace_ok = sp.expand(3*c0-3*difference) == 0
norm_ok = sp.expand(norm-difference**3) == 0

# Two independent controls: a reducible input and a signed-unit example.
# For 2^3-7=1, theta=(2-cuberoot(7))^3=1-12*t+6*t^2.
example = {A:1, B:7, X:2, Y:1}
sanities = {'rational_cube': field_key(2,54) == [1,1],
            'mixed_residues': field_key(16,83521) == [2,17],
            'known_unit_coefficients': [v.subs(example) for v in (c0,c1,c2)] == [1,-12,6],
            'known_unit_norm': norm.subs(example) == 1}

rows = []
for A0, entries in params['groups']:
    for B0, e, f in entries:
        key = field_key(A0, B0)
        noncube = key != [1,1]
        rows.append({'A':A0, 'B':B0, 'expected_key':[e,f], 'derived_key':key,
                     'splitting_degree':6 if noncube else 2,
                     'ok':0 < A0 < B0 <= 10**5 and gcd(A0,B0) == 1 and noncube and key == [e,f]})

# Exponents of U in the three absolute values, measured in half-units.
twice_exponents = [2,-1,-1]
quotients = [twice_exponents[i]-twice_exponents[j] for i,j in permutations(range(3),2)]
height_multiplier = Fraction(sum(max(0,v) for v in quotients), 2*6)
C_upper = 18*factorial(3)*2**3*192**4*4
K = 10**17
slope_numerator = 8*10**13
checks = {'48_distinct_rows':len(rows) == len({(r['A'],r['B']) for r in rows}) == 48,
          'field_roster':all(r['ok'] for r in rows), 'trace_identity':trace_ok, 'norm_identity':norm_ok,
          'height_multiplier':height_multiplier == Fraction(1,2),
          'modified_height_using_pi_lt_4':max(height_multiplier,Fraction(4*5,6),Fraction(5,6)) < 4,
          'minus_one_height_using_pi_lt_4':Fraction(4,6) < 1,
          'log24_lt_4':exp_lower(4,4) > 24, 'log6_lt_2':exp_lower(2,3) > 6,
          'log2_lt_1':exp_lower(1,2) > 2, 'BW_constant':C_upper < 10**13,
          'log_argument_bound':4*K+8 < 2**59,
          'endpoint':20+slope_numerator*59 < K, 'derivative':slope_numerator < K+2}
passed = all(sanities.values()) and all(checks.values())
result = {'summary':'Finite audit passed, conditional on the stated theorem normalization.' if passed else 'Audit failed. Inspect the named checks and equation rows.',
          'sanity':sanities, 'checks':checks, 'rows':rows,
          'distinct_field_keys':sorted({tuple(r['derived_key']) for r in rows}),
          'twice_log_modulus_exponents':dict(Counter(quotients)), 'height_multiplier':str(height_multiplier),
          'constant_upper':C_upper, 'endpoint_rhs_upper':20+slope_numerator*59,
          'theorem_source_checked_by_program':False}
with open('result.json','w') as out:
    json.dump(result,out,indent=2)
