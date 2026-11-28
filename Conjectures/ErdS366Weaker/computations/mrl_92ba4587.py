# MathResearchLab experiment 92ba4587-0c1f-481a-abb9-f2ff3680fc6f
# Certify the 48 Thue tails using one unit and one rational angle certificate per field
# sha256(code) = e8cc04a8481c1bdb6f3d0eb53836bd3416ebfff6d84370f48947ba07e0c93f8f
# parameters: {"seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import math, sys, time
from fractions import Fraction as F
from sympy import Matrix, integer_nthroot
from sympy.matrices.normalforms import hermite_normal_form

start = time.monotonic()
deadline = start + min(95, params['seconds'])
sys.set_int_max_str_digits(0)
H = 10**60
bits = 512
S = 1 << bits
one = (1, 0, 0)

def factors(n):
    out = {}
    p = 2
    while p*p <= n:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        out[n] = 1
    return out

def field(A, B):
    ex = factors(A)
    ey = factors(B)
    e = f = 1
    for p in ex.keys() | ey.keys():
        k = (2*ex.get(p, 0) + ey.get(p, 0)) % 3
        if k == 1:
            e *= p
        if k == 2:
            f *= p
    # Interchanging the two pure radicals preserves the field.
    return tuple(sorted((e, f)))

def coefficients(C):
    out = []
    for b in range(1, math.isqrt(math.isqrt(C))+1):
        if any(k > 1 for k in factors(b).values()):
            continue
        c = 1
        while b**4*c**5 <= C:
            if math.gcd(b,c) == 1 and all(k == 1 for k in factors(c).values()):
                out.append(b**4*c**5)
            c += 1
    return sorted(out)

# Basis 1,t,s with t^3=e*f^2, s^3=e^2*f, t*s=e*f.
def mul(x,y,e,f):
    a,b,c = x
    d,g,j = y
    return (a*d+e*f*(b*j+c*g), a*g+b*d+e*c*j, a*j+c*d+f*b*g)

def adj(x,e,f):
    a,b,c = x
    return (a*a-e*f*b*c, e*c*c-a*b, f*b*b-a*c)

def norm(x,e,f):
    a,b,c = x
    return a**3+e*f*f*b**3+e*e*f*c**3-3*e*f*a*b*c

def divide(x,n):
    assert n and all(v % n == 0 for v in x)
    return tuple(v//n for v in x)

def cubefloor(n):
    r = int(integer_nthroot(n,3)[0])
    assert r**3 <= n < (r+1)**3
    return r

def units(e,f):
    # J=beta^(-1) Z[1,t,s] has basis columns of L/N, N=|Norm(beta)|.
    # Repetition of this exact fractional ideal gives a unit quotient.
    L = Matrix.eye(3)
    N, beta = 1, one
    seen = {}
    scale = 1 << 28
    t = cubefloor(e*f*f*scale**3)
    s = cubefloor(e*e*f*scale**3)
    while True:
        key = (N,tuple(L))
        if key in seen:
            old = seen[key]
            unit = divide(mul(beta,adj(old,e,f),e,f),norm(old,e,f))
            if norm(unit,e,f) == -1:
                unit = tuple(-v for v in unit)
            assert norm(unit,e,f) == 1
            if unit != one:
                yield unit
            return
        seen[key] = beta
        cols = [tuple(map(int,L[:,i])) for i in range(3)]
        weight = max(8, 24*math.isqrt(1+e*f//N))
        rows = [[weight*(a*scale+b*t+c*s), 2*a*scale-b*t-c*s, b*t-c*s] for a,b,c in cols]
        _, transform = Matrix(rows).lll_transform()
        reduced = transform * L.T
        choices = []
        for i in range(3):
            g = tuple(map(int,reduced[i,:]))
            a,b,c = g
            real = abs(a*scale+b*t+c*s)
            if 4*real < 3*N*scale:
                choices.append((abs(norm(g,e,f)),real,g))
        if not choices:
            return
        ng,_,g = min(choices)
        assert ng and ng % (N*N) == 0
        next_N = ng//(N*N)
        ag = adj(g,e,f)
        new_cols = [divide(mul(ag,col,e,f),N*N) for col in cols]
        L = hermite_normal_form(Matrix(new_cols).T)
        beta = divide(mul(beta,g,e,f),N)
        assert abs(norm(beta,e,f)) == next_N
        N = next_N
        yield None

def scaled_atan(y):
    # For |y/S| <= 1/2, floor-rounded powers have error <2 grid units
    # by geometric contraction. Each Taylor term costs <3 grid units.
    assert 2*abs(y) <= S
    w = abs(y)
    power, total = w, 0
    for j in range(bits):
        term = power//(2*j+1)
        total += term if j % 2 == 0 else -term
        power = power*w*w//(S*S)
        if not power:
            break
    return total if y >= 0 else -total

def atan_at(z):
    # atan(z)=atan(1/2)+atan((2z-1)/(2+z)); atan is 1-Lipschitz.
    z = F(z)
    w = (2*z-1)/(2+z)
    k = (w*S).__floor__()
    center = scaled_atan(S//2)+scaled_atan(k)
    error = 8*bits+8
    return F(center-error,S),F(center+error,S)

pi_center = 16*scaled_atan(S//5)-4*scaled_atan(S//239)
pi_lo = F(pi_center-100*bits,S)
pi_hi = F(pi_center+100*bits,S)
assert 3 < pi_lo < pi_hi < 4

def interval_abs(lo,hi):
    return (0 if lo <= 0 <= hi else min(abs(lo),abs(hi)),max(abs(lo),abs(hi)))

def scaled_term(k,z):
    return min(k*z,k*(z+1)), max(k*z,k*(z+1))

def certificate(unit,e,f):
    t = cubefloor(e*f*f*S**3)
    s = cubefloor(e*e*f*S**3)
    g = math.isqrt(3*S*S)
    for eta in (unit,adj(unit,e,f)):
        a,b,c = eta
        assert norm(eta,e,f) == 1
        bl,bh = scaled_term(b,t)
        cl,ch = scaled_term(c,s)
        # Magnitudes of twice the real and imaginary parts, scaled by S.
        rl,rh = interval_abs(2*a*S-bh-ch,2*a*S-bl-cl)
        il,ih = interval_abs(bl-ch,bh-cl)
        il,ih = F(il*g,S),F(ih*(g+1),S)
        if rl*rl+il*il <= 4*S*S:
            continue
        # |eta'|>1 and Norm(eta)=1 certify 0<eta<1.
        zl = F(min(rl,il),max(rh,ih))
        zh = min(F(1),F(min(rh,ih),max(rl,il)))
        lo = 2*atan_at(zl)[0]/pi_hi
        hi = 2*atan_at(zh)[1]/pi_lo
        lo = F((lo*S).__floor__(),S)
        hi = F((hi*S).__ceil__(),S)
        assert lo <= hi
        M = 1+abs(a)+abs(b)*e*f*f+abs(c)*e*e*f
        h = M.bit_length()
        Q = 10**38*(h+1)**2
        rat = ((lo+hi)/2).limit_denominator(10**90)
        p,q = rat.numerator,rat.denominator
        if q > Q and 2*Q*q*max(abs(lo-rat),abs(hi-rat)) < 1 and 40*h*q < H**3:
            return {'basis_e_f':[e,f],'eta_coefficients':list(eta),'norm':1,'M':M,'h':h,'unit_exponent_upper':Q,'unit_index_upper':10*h,'angle_interval_numerators':[int(lo*S),int(hi*S)],'angle_interval_denominator':S,'p':p,'q':q}
    return None

def inverse(A,B,X,Y):
    assert A*X**3-B*Y**3 == 1
    x,y = abs(X),abs(Y)
    difference = A*x**3-B*y**3
    assert abs(difference) == 1
    if X*Y > 0:
        assert difference == (1 if X > 0 else -1)
    return {'X':X,'Y':Y,'x':x,'y':y,'difference':difference,'positive_pair':X*Y>0,'in_tail':X*Y>0 and max(x,y)>H}

# Known equation with a genuine non-axis solution, plus both signed maps.
assert inverse(1,7,2,1)['difference'] == 1
assert inverse(1,9,-2,-1)['difference'] == -1
assert not inverse(1,7,1,0)['positive_pair']
e,f = 7,1
eta = (2,-1,0)
assert mul(eta,adj(eta,e,f),e,f) == one
u = mul(mul(eta,eta,e,f),eta,e,f)
assert u[0] == 1 and norm(u,e,f) == 1
assert certificate(eta,e,f) is not None

C = coefficients(10**5)
mods = {m:{pow(i,3,m) for i in range(m)} for m in (7,9,13)}
pairs = [(A,B) for A in C for B in C if A<B and math.gcd(A,B)==1]
survivors = [(A,B) for A,B in pairs if all(any((A*i-B*j-1)%m==0 for i in residues for j in residues) for m,residues in mods.items())]
assert len(C)==23 and len(pairs)==152 and len(survivors)==48
fields = sorted({field(A,B) for A,B in survivors})
active = {k:units(*k) for k in fields}
certs, reasons = {},{}
steps = dict.fromkeys(fields,0)
while active and time.monotonic() < deadline:
    for k in list(active):
        if time.monotonic() >= deadline:
            break
        try:
            candidate = next(active[k])
            steps[k] += 1
            if candidate is not None:
                cert = certificate(candidate,*k)
                if cert is not None:
                    certs[k] = cert
                else:
                    reasons[k] = 'unit found; angle separation not certified'
                del active[k]
        except StopIteration:
            reasons[k] = 'unit discovery ended without a nontrivial unit'
            del active[k]
        except Exception as exc:
            reasons[k] = type(exc).__name__+' '+str(exc)[:200]
            del active[k]

records = []
for A,B in survivors:
    k = field(A,B)
    tag = str(k[0])+','+str(k[1])
    known = [(1,0)] if A==1 else []
    maps = [inverse(A,B,X,Y) for X,Y in known]
    ok = k in certs
    records.append({'A':A,'B':B,'field_certificate_key':tag,'tail_status':'INFEASIBLE' if ok else 'UNKNOWN','complete_signed_list':known if ok else None,'known_signed_entries':known,'inverse_map_checks':maps,'tail_witnesses':[] if ok else None,'remaining_gap':None if ok else reasons.get(k,'unit search time budget'),'unit_search_steps':steps[k]})
solved = sum(r['tail_status']=='INFEASIBLE' for r in records)
result = {'summary':f'Tail exclusion certified for {solved} of 48 signed equations. Each complete list also uses the supplied inclusive bounded result E-4610da.','status':'INFEASIBLE' if solved==48 else 'UNKNOWN','author_support':'proved_here','justification':'For each successful record, exact norm, conjugate magnitude, dyadic angle enclosure, rational separation and tail inequalities instantiate the stated argument using the explicit Baker–Wüstholz theorem. UNKNOWN records make no exclusion.','sanity':'Checked a non-axis solution, both signed inverse maps, axis rejection, pure cubic arithmetic, and a tail angle certificate for the field of the cube root of 7.','coefficient_max':100000,'exclusive_tail_cutoff':H,'certificates':{str(e)+','+str(f):v for (e,f),v in certs.items()},'equations':records}
with open('result.json','w') as out:
    json.dump(result,out)
