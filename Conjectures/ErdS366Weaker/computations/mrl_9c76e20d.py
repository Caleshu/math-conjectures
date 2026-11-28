# MathResearchLab experiment 9c76e20d-4d81-4a3a-9676-ed051566a5bb
# Certify the unbounded tail by a cubic-field unit and one rational approximation
# sha256(code) = d2f5127da0cb0ea01865d76a3937f086f61bcb5ffee64033b8ecc178f4d09763
# parameters: {"coefficient_max": 100000, "cutoff_exponent": 60, "seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from math import gcd, isqrt
from itertools import combinations
params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()
deadline = start + min(95, params['seconds'])
C = params['coefficient_max']
H = 10**params['cutoff_exponent']
S = 1 << 896
ERR = 100000

def root(n):
    if not n:
        return 0
    a = 1 << ((n.bit_length()+2)//3)
    while True:
        b = (2*a+n//(a*a))//3
        if b >= a:
            return a
        a = b

def sf(n):
    return all(n%(p*p) for p in range(2,isqrt(n)+1))

def field(A,B):
    n = A*A*B
    s = t = 1
    for p in range(2,isqrt(isqrt(max(C,16)))+2):
        e = 0
        while n%p == 0:
            n //= p
            e += 1
        if e%3 == 1:
            s *= p
        if e%3 == 2:
            t *= p
    assert n == 1
    return tuple(sorted((s,t)))

def obstruction(A,B):
    for m in (7,9,13,19,27,31,37,43,49,61,67,73,79,97,109,127,163):
        left = {A*i**3%m for i in range(m)}
        right = {B*i**3%m for i in range(m)}
        # Negating both variables interchanges the signs.
        if all((v+1)%m not in left for v in right):
            return m
    return 0

def atan_small(t):
    assert 0 <= 2*t <= S
    power = t
    total = i = 0
    while power:
        term = power//(2*i+1)
        total += term if i%2 == 0 else -term
        power = power*t*t//(S*S)
        i += 1
    return total

pi_fixed = 16*atan_small(S//5)-4*atan_small(S//239)

def certificate(s,t,E,h):
    # Basis 1, alpha, beta has alpha^2=t*beta, beta^2=s*alpha, alpha*beta=s*t.
    m = s*t
    def norm(v):
        a,b,c = v
        return a**3+s*t*t*b**3+s*s*t*c**3-3*m*a*b*c
    def adj(v):
        a,b,c = v
        return (a*a-m*b*c,s*c*c-a*b,t*b*b-a*c)
    assert norm(E) == 1
    a,b,c = E
    assert norm((a-1,b,c)) > 0
    L = 10+((m+1)*sum(map(abs,E))).bit_length()
    T = (10**23*L)**2
    a,b,c = adj(E)
    J = 32*S*(1+(m+1)*(abs(a)+abs(b)+abs(c)))
    alpha = root(s*t*t*J**3)
    beta = root(s*s*t*J**3)
    X = abs(2*a*J-b*alpha-c*beta)
    Y = abs((b*alpha-c*beta)*isqrt(3*J*J)//J)
    r = min(X,Y)*S//max(X,Y)
    if 2*r <= S:
        angle = atan_small(r)
    else:
        angle = pi_fixed//4-atan_small((S-r)*S//(S+r))
    P = 2*angle*S//pi_fixed
    u,v = P,S
    p0,p1,q0,q1 = 0,1,1,0
    while v:
        d,rem = divmod(u,v)
        u,v = v,rem
        p0,p1 = p1,d*p1+p0
        q0,q1 = q1,d*q1+q0
        if 100*L*q1 >= h**3:
            break
        error_num = abs(q1*P-p1*S)+q1*ERR
        if q1>T and 2*T*error_num<S:
            assert gcd(p1,q1)==1
            return {'field_s_t':[s,t], 'unit':list(E), 'L':L, 'T':str(T), 'angle_numerator':str(P), 'angle_scale_bits':896, 'angle_error_units':ERR, 'p':str(p1), 'q':str(q1), 'q_angle_error_numerator_bound':str(error_num)}
    return None

def find_unit(s,t,kmax,until):
    m = s*t
    M = 2*kmax+128
    scale = 1 << M
    alpha = root((s*t*t) << (3*M))
    beta = root((s*s*t) << (3*M))
    rows = [(1,0,0),(0,1,0),(0,0,1)]
    seen = {}
    def norm(v):
        a,b,c = v
        return a**3+s*t*t*b**3+s*s*t*c**3-3*m*a*b*c
    def adj(v):
        a,b,c = v
        return (a*a-m*b*c,s*c*c-a*b,t*b*b-a*c)
    def product(v,w):
        a,b,c = v
        d,e,f = w
        return (a*d+m*(b*f+c*e), a*e+b*d+s*c*f, a*f+c*d+t*b*e)
    def dot(v,w):
        return sum(a*b for a,b in zip(v,w))
    for k in range(0,kmax+1,5):
        if time.monotonic() >= until:
            break
        def embed(row):
            a,b,c = row
            return (a,b*(1+root(s*t*t)),c*(1+root(s*s*t)),(a*scale+b*alpha+c*beta)>>(M-k))
        # Reduce three lattice vectors to look for elements of repeated small norm.
        for step in range(48):
            rows.sort(key=lambda v: dot(embed(v),embed(v)))
            changed = False
            for j in (1,2):
                dirs = list(rows[:j])
                if j==2:
                    dirs.extend(tuple(x+sign*y for x,y in zip(rows[0],rows[1])) for sign in (-1,1))
                for w in dirs:
                    v = rows[j]
                    ev,ew = embed(v),embed(w)
                    den = dot(ew,ew)
                    n = (2*dot(ev,ew)+den)//(2*den)
                    if n:
                        new = tuple(x-n*y for x,y in zip(v,w))
                        en = embed(new)
                        if dot(en,en)<dot(ev,ev):
                            rows[j] = new
                            changed = True
            if not changed:
                break
        for row in rows:
            N = norm(row)
            v = row if N>0 else tuple(-x for x in row)
            N = abs(N)
            if N==0:
                continue
            for w in seen.get(N,()):
                if v==w:
                    break
                z = product(v,adj(w))
                if all(x%N==0 for x in z):
                    E = tuple(x//N for x in z)
                    if E!=(1,0,0) and norm(E)==1:
                        a,b,c = E
                        return E if norm((a-1,b,c))>0 else adj(E)
            else:
                seen.setdefault(N,[]).append(v)
    return None

# Known irreducible test field: 1+alpha+alpha^2 is the inverse of alpha-1 for alpha^3=2.
# In our sorted basis for (1,2), beta is the real cube root of 2.
assert certificate(1,2,(1,1,1),10**60) is not None
assert obstruction(1,7)==0 and obstruction(1,9)==0
assert root(8)**3==8 and root(27)**3==27
coeff = sorted({b**4*c**5 for b in range(1,isqrt(isqrt(C))+1) for c in range(1,isqrt(isqrt(C))+1) if b**4*c**5<=C and sf(b) and sf(c) and gcd(b,c)==1})
modular, factored, groups = [],[],{}
for A,B in combinations(coeff,2):
    if gcd(A,B)!=1:
        continue
    if root(A)**3==A and root(B)**3==B:
        factored.append([A,B])
        continue
    mod = obstruction(A,B)
    if mod:
        modular.append([A,B,mod])
    else:
        groups.setdefault(field(A,B),[]).append([A,B])
certs = []
remaining = dict(groups)
for steps,seconds in ((240,0.25),(1000,1.25),(2600,3.0)):
    for key in list(remaining):
        now = time.monotonic()
        if now >= deadline:
            break
        E = find_unit(*key,steps,min(deadline,now+seconds))
        if E is not None:
            cert = certificate(*key,E,H)
            if cert is not None:
                cert['pairs'] = remaining.pop(key)
                certs.append(cert)
unknown = sorted(pair for pairs in remaining.values() for pair in pairs)
count = sum(gcd(A,B)==1 for A,B in combinations(coeff,2))
assert count==len(factored)+len(modular)+sum(len(c['pairs']) for c in certs)+len(unknown)
result = {'summary':'Every listed exclusion has a factorization, modular obstruction, or checked cubic-field certificate. The unknown list is the exact outstanding coefficient scope above the cutoff.', 'status':'UNKNOWN' if unknown else 'INFEASIBLE', 'author_support':'proved_here', 'justification':'Apply the certificate test in the experiment description to each recorded field, or verify its listed factorization or modulus.', 'strict_multiplier_lower_bound':str(H), 'coefficients':coeff, 'pair_count':count, 'factorization_exclusions':factored, 'modular_A_B_modulus':modular, 'field_certificates':certs, 'unknown_pairs':unknown, 'sanity':'Known pure cubic unit passed the tail certificate. Soluble equations of both signs survived the modular sieve.'}
with open('result.json','w') as f:
    json.dump(result,f)
