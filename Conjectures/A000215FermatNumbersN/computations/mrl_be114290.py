# MathResearchLab experiment be114290-acdc-4db5-adea-1400d82dea1d
# Certify the Fermat factor table
# sha256(code) = 9a0d5c30684001337b2f01ce3e1ad7418b822a69602bd635744e16e2e9da349a
# parameters: {"seconds": 100, "prefixes": [[], [], [], [], [], [641], [274177], [59649589127497217], [1238926361552897], [2424833, 7455602825647884208337395736200454918783366342657], [45592577, 6487031809, 4659775785220018543264560743076778192897], [319489, 974849, 167988556341760475137, 3560841906445833920513]], "extra_primality_targets": []}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import math
import multiprocessing as mp
import time
from functools import lru_cache
from sympy import ZZ, factorint, isprime, primerange, sqrt_mod

# A probable-prime test is only a search filter. A successful return from
# prove() needs trial division, the exact FLINT predicate, or a certificate.
small_product = math.prod(map(int, primerange(2, 40000)))

def strip_small(n):
    common = math.gcd(n, small_product)
    while common > 1:
        n //= common
        common = math.gcd(n, common)
    return n

def add(P, Q, A, n):
    if P is None:
        return Q
    if Q is None:
        return P
    x, y = P
    u, v = Q
    if x == u:
        if (y + v) % n == 0:
            return None
        if y != v:
            raise ValueError('inconsistent components')
        slope = (3*x*x + A) * pow(2*y, -1, n) % n
    else:
        slope = (v-y) * pow(u-x, -1, n) % n
    z = (slope*slope-x-u) % n
    return z, (slope*(x-z)-y) % n

def mul(k, P, A, n):
    R = None
    for bit in bin(k)[2:]:
        R = add(R, R, A, n)
        if bit == '1':
            R = add(R, P, A, n)
    return R

# These CM data only suggest curve orders. An incorrect suggestion cannot
# certify anything: the final point-order identity is tested directly.
cm = [(1,1728),(3,0),(2,8000),(7,-3375),(11,-32768),(19,-884736),
      (43,-884736000),(67,-147197952000),(163,-262537412640768000)]

def traces(n, d):
    root = sqrt_mod(-d, n)
    if root is None:
        return {0}
    root = int(root)
    values = set()
    for modulus in (n, 4*n):
        for sign in (1, -1):
            base = sign*root % n
            for start in range(base, modulus, n):
                if (start*start+d) % modulus:
                    continue
                u, v = modulus, start
                while v*v > modulus:
                    u, v = v, u % v
                rem = modulus-v*v
                w = math.isqrt(rem//d)
                if d*w*w != rem:
                    continue
                scale = 2 if modulus == n else 1
                t, b = scale*v, scale*w
                values.add(t)
                if d == 1:
                    values.add(b)
                if d == 3:
                    values.update([abs(t+3*b)//2, abs(t-3*b)//2])
    return values | {-t for t in values}

@lru_cache(None)
def prove(n):
    if n < 10000:
        if n >= 2 and all(n % d for d in range(2, math.isqrt(n)+1)):
            return {'n': n, 'method': 'trial_division'}
        return None
    if not isprime(n):
        return None
    z = ZZ(n)
    if type(z).__module__.split('.')[0] == 'flint' and hasattr(z, 'is_prime'):
        if z.is_prime():
            return {'n': n, 'method': 'FLINT fmpz_is_prime (exact)'}
        return None

    # Pocklington. Even if factorint returns an incomplete factorization,
    # only recursively proved factors enter the certified product.
    tail = strip_small(n-1)
    if n.bit_length() <= 64:
        candidates = list(map(int, factorint(n-1)))
    else:
        candidates = list(map(int, factorint((n-1)//tail)))
        if tail > 1 and isprime(tail):
            candidates.append(tail)
    F = 1
    witnesses = []
    for q in sorted(set(candidates), reverse=True):
        if not 1 < q < n or (n-1) % q:
            continue
        sub = prove(q)
        if sub is None:
            continue
        for b in range(2, 32):
            if pow(b,n-1,n) == 1 and math.gcd(pow(b,(n-1)//q,n)-1,n) == 1:
                power = q
                while (n-1) % (power*q) == 0:
                    power *= q
                F *= power
                witnesses.append({'q': q, 'power': power, 'base': b, 'proof': sub})
                break
        if F*F > n:
            return {'n': n, 'method': 'Pocklington', 'F': F, 'witnesses': witnesses}

    # Elliptic fallback. A prime q > 2*floor(sqrt(n))+1 is sufficient
    # even with the elementary point count bound 2*r+1 over F_r.
    for d, j in cm:
        for t in sorted(traces(n,d)):
            order = n+1-t
            q = strip_small(order)
            if not 2*math.isqrt(n)+1 < q < n or not isprime(q):
                continue
            if j in (0,1728):
                curves = [(0,b) if j == 0 else (b,0) for b in range(1,8)]
            else:
                c = j*pow(1728-j,-1,n) % n
                curves = [(3*c,2*c)]
            for A0, B0 in curves:
                for x in range(1,9):
                    twist = (x**3+A0*x+B0) % n
                    A = A0*twist**2 % n
                    B = B0*pow(twist,3,n) % n
                    if math.gcd(6*(4*A**3+27*B*B),n) != 1:
                        continue
                    P = (x*twist % n, twist*twist % n)
                    try:
                        Q = mul(order//q,P,A,n)
                        if Q is None or (Q[1]**2-Q[0]**3-A*Q[0]-B) % n:
                            continue
                        if mul(q,Q,A,n) is not None:
                            continue
                    except ValueError:
                        continue
                    sub = prove(q)
                    if sub is not None:
                        return {'n': n, 'method': 'elliptic_point_order', 'A': A,
                                'B': B, 'Q': list(Q), 'q': q, 'proof': sub}
                    break
    return None

def worker(n, conn):
    try:
        proof = prove(n)
        conn.send({'status': 'certified' if proof else 'unresolved', 'proof': proof})
    except Exception as exc:
        conn.send({'status': 'unresolved', 'reason': repr(exc)})
    finally:
        conn.close()

if __name__ == '__main__':
    assert mul(2,(0,1),0,5) == (0,4) and mul(3,(0,1),0,5) is None
    assert prove(65537) is not None and prove(65535) is None
    deadline = time.monotonic() + min(105, params.get('seconds',100))
    rows = []
    checks = {}
    seen = set()
    assert len(params['prefixes']) == 12
    for j, prefix in enumerate(params['prefixes']):
        f = (1 << (1 << j)) + 1
        tail, rem = divmod(f, math.prod(prefix))
        entries = prefix+[tail]
        ok = rem == 0 and min(entries)>1 and math.prod(entries)==f
        ok = ok and len(set(entries))==len(entries) and seen.isdisjoint(entries)
        rows.append({'j': j, 'factors': entries, 'product_and_distinctness_ok': ok})
        if ok:
            seen.update(entries)
    targets = sorted(seen | set(params.get('extra_primality_targets', [])))
    weights = [1+(n.bit_length()/160)**3 for n in targets]
    ctx = mp.get_context('fork')
    for i, n in enumerate(targets):
        remaining = deadline-time.monotonic()
        if remaining < 0.15:
            checks[str(n)] = {'status':'unresolved','reason':'overall time limit'}
            continue
        budget = min(remaining, max(0.7, remaining*weights[i]/sum(weights[i:])))
        rx, tx = ctx.Pipe(duplex=False)
        job = ctx.Process(target=worker, args=(n,tx))
        job.start()
        tx.close()
        try:
            if rx.poll(budget):
                checks[str(n)] = rx.recv()
            else:
                checks[str(n)] = {'status':'unresolved','reason':'per-factor time limit'}
        except EOFError:
            checks[str(n)] = {'status':'unresolved','reason':'worker exited'}
        finally:
            if job.is_alive():
                job.kill()
            job.join()
            rx.close()
    for row in rows:
        row['certified'] = row['product_and_distinctness_ok'] and all(checks[str(q)]['status']=='certified' for q in row['factors'])
    ready = [a for a in range(7,13) if all(r['certified'] for r in rows[:a])]
    result = {'summary':'Factorization certificates complete for divisor searches at a = '+str(ready), 'ready_indices':ready, 'rows':rows, 'primality_checks':checks, 'sanity_passed':True, 'author_support':'proved_here', 'justification':'For each Pocklington witness and each prime r dividing n, the order of the base modulo r divides n-1 and contains the full displayed q-power. Thus F divides r-1. F squared greater than n rules out any prime divisor at most sqrt(n). For an elliptic witness the discriminant is a unit and every division in the group operations uses a unit. The finite point Q reduces modulo every prime divisor r to a point of certified prime order q. There are at most 2r+1 points, including infinity, since each x has at most two y values. The checked size of q rules out r at most sqrt(n). A certified row also requires the exact product identity.'}
    with open('result.json','w') as out:
        json.dump(result,out)
