# MathResearchLab experiment 4610da85-6f4b-410c-8c1e-edb5df9c0512
# Verify both signs through the multiplier cutoff
# sha256(code) = efab1d5734a064f6d82783257e4efcec20546485317224a63b4be06230d551ec
# parameters: {"coefficient_max": 100000, "cutoff_exponent": 60}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from math import gcd, isqrt
params = json.load(open(os.environ['MRL_PARAMS']))
C = params['coefficient_max']
H = 10 ** params['cutoff_exponent']

def icbrt(n):
    if n == 0:
        return 0
    a = 1 << ((n.bit_length() + 2) // 3)
    while True:
        b = (2*a + n//(a*a))//3
        if b >= a:
            return a
        a = b

def squarefree(n):
    return all(n % (p*p) for p in range(2, isqrt(n)+1))

def coefficients():
    out = []
    for b in range(1, isqrt(isqrt(C))+1):
        if not squarefree(b):
            continue
        c = 1
        while b**4*c**5 <= C:
            if squarefree(c) and gcd(b,c) == 1:
                out.append(b**4*c**5)
            c += 1
    assert len(out) == len(set(out))
    return sorted(out)

def solve(A,B,h):
    D = 16*h*h
    u = icbrt(B*D**3//A)
    assert A*u**3 <= B*D**3 < A*(u+1)**3
    v = D
    p0,p1,q0,q1 = 0,1,1,0
    hits = []
    while v:
        a, rem = divmod(u,v)
        u,v = v,rem
        p0,p1 = p1,a*p1+p0
        q0,q1 = q1,a*q1+q0
        if q1 > h:
            break
        f = A*p1**3-B*q1**3
        if 1 <= p1 <= h and abs(f) == 1:
            hits.append([p1,q1,f])
    return hits

for A in range(1,9):
    for B in range(A+1,15):
        direct = [[x,y,A*x**3-B*y**3] for y in range(1,26) for x in range(1,26) if abs(A*x**3-B*y**3)==1]
        assert solve(A,B,25) == direct
assert [2,1,1] in solve(1,7,25) and [2,1,-1] in solve(1,9,25)
coeff = coefficients()
hits = []
pairs = 0
for i,A in enumerate(coeff):
    for B in coeff[i+1:]:
        if gcd(A,B) == 1:
            pairs += 1
            hits.extend([A,B,x,y,f] for x,y,f in solve(A,B,H))
result = {'summary':'Exhausted the bounded range by exact continued fractions and substitution.', 'status':'FEASIBLE' if hits else 'INFEASIBLE', 'author_support':'proved_here', 'justification':'The rational approximation and Legendre criterion in the experiment description cover every eligible reduced fraction.', 'coefficients':coeff, 'coprime_pairs':pairs, 'inclusive_multiplier_cutoff':str(H), 'witnesses_A_B_x_y_signed_difference':hits, 'sanity':'Direct enumeration on small inputs agreed, including known solutions of both signs.'}
with open('result.json','w') as f:
    json.dump(result,f)
