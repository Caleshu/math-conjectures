# MathResearchLab experiment 5d552f32-54c8-40b4-aa5a-4eebe672e869
# Exhaust the exact valuation class and test the two remaining factors
# sha256(code) = aa44b04ba03429d77dca40d2f2500cddcbe8a6268e9ff6ad6bf4666e9cfbe857
# parameters: {"seconds": 100, "prefixes": [[], [], [], [], [], [641], [274177], [59649589127497217], [1238926361552897], [2424833, 7455602825647884208337395736200454918783366342657], [45592577, 6487031809, 4659775785220018543264560743076778192897], [319489, 974849, 167988556341760475137, 3560841906445833920513]]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import math
import time
from sympy import ZZ, isprime, primerange

def products(entries):
    result = [1]
    for q in entries:
        result += [d*q for d in result]
    return result

def valuation_class(entries, a):
    modulus = 1 << (a+1)
    target = (1 << a)-1
    split = len(entries)//2
    buckets = {}
    for left in products(entries[:split]):
        buckets.setdefault(left % modulus, []).append(left)
    for right in products(entries[split:]):
        residue = target*pow(right,-1,modulus) % modulus
        for left in buckets.get(residue, ()):
            yield left*right

def passes_both(m):
    return pow(2,m,m+1)==1 and pow(2,m,m*m+1)==1

# Independently exercise valuation selection and the split modular test.
small = [3,5,17,257,65537]
for a in range(2,7):
    wanted = [d for d in products(small) if (d+1) % (2 << a) == 1 << a]
    assert sorted(valuation_class(small,a)) == sorted(wanted)
for m in range(6,301,2):
    direct = pow(2,m,m**4-1)==1
    assert direct == (pow(2,m,m-1)==1 and passes_both(m))
assert passes_both(16) and not passes_both(36)

assert len(params['prefixes'])==12
rows = []
seen = set()
table_error = None
for j, prefix in enumerate(params['prefixes']):
    f = (1 << (1 << j))+1
    tail, rem = divmod(f, math.prod(prefix))
    values = prefix+[tail]
    if rem or min(values)<=1 or math.prod(values)!=f or len(set(values))!=len(values) or not seen.isdisjoint(values):
        table_error = j
        break
    rows.append(values)
    seen.update(values)

limit = 4000
primes = list(map(int,primerange(3,limit+1)))
primorial = math.prod(primes)
deadline = time.monotonic()+min(105,params.get('seconds',100))
reports = []
for a in range(7,13):
    if a>len(rows) or time.monotonic()>=deadline:
        break
    entries = [q for row in rows[:a] for q in row]
    power = 1 << a
    M = (1 << power)-1
    assert math.prod(entries)==M
    # For p > limit, the order of 2 modulo each odd prime ell <= limit
    # is strictly below p. It divides 2^a*p iff it divides 2^a.
    bad = math.prod(ell for ell in primes if pow(2,power,ell)!=1)
    counts = dict(valuation_matches=0, below_threshold=0, composite_by_gcd=0,
                  small_modulus_failure=0, plus_one_failure=0, square_plus_one_failure=0,
                  composite_after_both=0, certified_counterexamples=0, pending_primality=0)
    report = {'a':a, 'factor_entries':entries, 'counts':counts, 'survivors':[], 'complete':False}
    reports.append(report)
    for D in valuation_class(entries,a):
        if time.monotonic()>=deadline:
            break
        m = D+1
        p = m >> a
        assert p % 2 and (p << a)==m
        counts['valuation_matches'] += 1
        if p < power//2:
            counts['below_threshold'] += 1
            continue
        g = math.gcd(p,primorial)
        if 1 < g < p:
            counts['composite_by_gcd'] += 1
            continue
        if p>limit and (math.gcd(m+1,bad)>1 or math.gcd(m*m+1,bad)>1):
            counts['small_modulus_failure'] += 1
            continue
        if pow(2,m,m+1)!=1:
            counts['plus_one_failure'] += 1
            continue
        if pow(2,m,m*m+1)!=1:
            counts['square_plus_one_failure'] += 1
            continue
        if not isprime(p):
            counts['composite_after_both'] += 1
            continue
        # A survivor gets an independent full-modulus check, including D.
        assert M%D==0 and pow(2,m,m**4-1)==1
        certified = False
        if p <= 10**10:
            certified = all(p%d for d in range(2,math.isqrt(p)+1))
        else:
            z = ZZ(p)
            if type(z).__module__.split('.')[0]=='flint' and hasattr(z,'is_prime'):
                # Large exact proofs belong to the time-bounded first program.
                if p.bit_length()<=128:
                    certified = bool(z.is_prime())
        key = 'certified_counterexamples' if certified else 'pending_primality'
        counts[key] += 1
        report['survivors'].append({'D':D,'p':p,'m':m,'classification':key,'full_remainder':1})
    else:
        report['complete'] = True
    assert counts['valuation_matches']==sum(v for k,v in counts.items() if k!='valuation_matches')
    if not report['complete']:
        break

excluded = [r['a'] for r in reports if r['complete'] and not r['survivors']]
refuted = [r['a'] for r in reports if r['counts']['certified_counterexamples']]
result = {'summary':'Completed exclusions conditional on the factor table: '+str(excluded)+'. Indices with certified counterexamples: '+str(refuted), 'excluded_conditional_on_table':excluded,'refuted':refuted,'first_invalid_factor_row':table_error,'reports':reports,'sanity_passed':True,'author_support':'proved_here','justification':'With certified distinct prime entries, each positive divisor is a unique subset product. Splitting the subset into left and right halves and inverting the odd right product selects exactly D congruent to 2^a-1 modulo 2^(a+1). Since D divides 2^(2^a)-1 and 2^a divides m, D divides 2^m-1. For even m the three odd factors m-1, m+1 and m^2+1 are pairwise coprime: each pair has gcd dividing 2. Their product is m^4-1. Thus the two remaining power tests are equivalent to the requested divisibility on this list. For the small-modulus rejection, an odd prime ell in the bad product has order dividing ell-1 and not dividing 2^a. If p is prime and p exceeds ell-1, this order cannot divide 2^a*p. If p is composite the candidate is already ineligible.'}
with open('result.json','w') as out:
    json.dump(result,out)
