# MathResearchLab experiment 357d810a-1cf9-454f-9442-88aff3f2182e
# Unrestricted pair search at the four opposite-index obstruction parameters
# sha256(code) = 299bab46e0dedc8fb117fb9934cad69e598435e13229b6e7edc42c680e4cf5f5
# parameters: {"r_values": [27, 52, 77, 102], "z": -2, "third_index_limit": 20000, "seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ["MRL_PARAMS"]))

from math import isqrt
from time import monotonic

started = monotonic()
import numpy as np


def pyramidal(k, n):
    return n * (n + 1) * (k * n + 3 - k) // 6


def pairs(k, z, c):
    # Write X=ka+1, Y=kb+1, Z=kc+1, s=X+Y, d=X-Y.
    g = k*k - 3*k + 3
    Z = k*c + 1
    D = 6*k*k*z - 3*(g-1) - (Z**3 - g*Z)
    # D is -4 modulo k. This rules out D=0 for every requested k.
    assert D % k == (-4) % k and D != 0
    magnitude = abs(D)
    if magnitude > (1 << 63) - 1:
        raise ValueError('Divisibility vector exceeds signed 64-bit range')

    # 4D = s*(s*s + 3*d*d - 4*g). Opposite signs force |s| <= sqrt(4g).
    # For equal signs, |s| > sqrt(4g) + cubert(4|D|) is impossible.
    short = isqrt(4*g)
    cube_upper = 1 << (((4*magnitude).bit_length() + 2) // 3)
    long = short + 1 + cube_upper
    lo, hi = (-short, long) if D > 0 else (-long, short)
    first = lo + (2-lo) % k
    candidates = np.arange(first, hi+1, k, dtype=np.int64)
    # Every candidate is 2 modulo k, hence nonzero. Only divisibility uses NumPy.
    divisors = candidates[np.remainder(magnitude, candidates) == 0]
    for item in divisors:
        s = int(item)
        three_d_squared = 4*(D//s) - s*s + 4*g
        if three_d_squared < 0 or three_d_squared % 3:
            continue
        d_squared = three_d_squared // 3
        d = isqrt(d_squared)
        if d*d != d_squared:
            continue
        if (s-d-2) % (2*k) or (s+d-2) % (2*k):
            continue
        a = (s-d-2) // (2*k)
        b = (s+d-2) // (2*k)
        assert pyramidal(k,a) + pyramidal(k,b) + pyramidal(k,c) == z
        yield a, b


def sanity(k):
    # Compare recovered pairs with direct enumeration, including empty fibers.
    radius = 4
    checks = 0
    for c in (-4, 0, 3):
        expected = {}
        for a in range(-radius, radius+1):
            for b in range(a, radius+1):
                z = sum(pyramidal(k,n) for n in (a,b,c))
                expected.setdefault(z, set()).add((a,b))
        for z in sorted(set(expected) | set(range(-5,6))):
            recovered = {(a,b) for a,b in pairs(k,z,c) if -radius <= a <= b <= radius}
            assert recovered == expected.get(z, set()), (k,z,c,recovered)
            checks += 1
    assert (1,1) in set(pairs(k, 8-10*k, -4))
    return checks


def third_indices(limit):
    yield 0
    for h in range(1, limit+1):
        yield -h
        yield h


def search(r, z, limit, deadline):
    k = r-2
    lo = hi = None
    count = 0
    for c in third_indices(limit):
        if count and monotonic() >= deadline:
            break
        witness = next(pairs(k,z,c), None)
        if witness is not None:
            a,b = witness
            values = [pyramidal(k,n) for n in (a,b,c)]
            assert sum(values) == z
            return {'r':r, 'z':z, 'outcome':'hit', 'triple':[a,b,c], 'summand_values':values, 'sum':sum(values)}
        lo = c if lo is None else min(lo,c)
        hi = c if hi is None else max(hi,c)
        count += 1
    assert count == hi-lo+1
    return {'r':r, 'z':z, 'outcome':'miss_in_exhausted_interval', 'third_index_interval_inclusive':[lo,hi], 'third_indices_exhausted':count, 'stop_reason':'index_limit' if count == 2*limit+1 else 'time_budget'}


rs = params['r_values']
z = params['z']
limit = params['third_index_limit']
assert rs == [27,52,77,102] and z == -2 and 0 <= limit <= 20000
checks = {str(r):sanity(r-2) for r in rs}
end = started + min(params['seconds'], 95)
rows = []
for i,r in enumerate(rs):
    now = monotonic()
    deadline = now + max(0, end-now)/(len(rs)-i)
    rows.append(search(r,z,limit,deadline))

lines = []
for row in rows:
    if row['outcome'] == 'hit':
        lines.append(f"r={row['r']} gives {row['triple']} with summands {row['summand_values']}")
    else:
        lo,hi = row['third_index_interval_inclusive']
        lines.append(f"r={row['r']} has no triple for {lo} <= c <= {hi}, inclusive, with unrestricted a,b")

result = {
    'summary': '. '.join(lines) + '.',
    'findings': rows,
    'sanity': {'passed':True, 'bounded_pair_set_comparisons_by_r':checks, 'known_triple':[1,1,-4]},
    'author_support':'proved_here',
    'justification': 'Let $k=r-2$, $g=k^2-3k+3$, and $f(X)=X^3-gX$. Expansion gives $f(kn+1)=6k^2P_r(n)+1-g$. Thus for fixed $c$, the required equation is $f(X)+f(Y)=D$ with $X=ka+1$, $Y=kb+1$ and $D$ as in the code. Since $D$ is congruent to $-4$ modulo $k$ and $k$ is one of $25,50,75,100$, $D$ is nonzero. Put $s=X+Y$ and $d=Y-X$. Expansion gives $4D=s(s^2+3d^2-4g)$. Also $s$ divides $D$ because $f(X)+f(Y)=(X+Y)(X^2-XY+Y^2-g)$. If $D/s<0$, then $s^2<4g$. If $D/s>0$ and $t=|s|$ exceeds $\\sqrt{4g}+\\sqrt[3]{4|D|}$, then $t(t^2-4g)\\ge(t-\\sqrt{4g})^3>4|D|$, contradicting the identity. The scanned interval therefore includes every possible $s$, and $s$ must be congruent to $2$ modulo $k$. For each retained divisor the square test and the two congruences recover exactly the integral indices via $a=(s-d-2)/(2k)$ and $b=(s+d-2)/(2k)$. Taking $d\\ge0$ orders the pair. Third indices are visited in contiguous prefixes, and a miss counts a third index only after its entire divisor test finishes.'
}
with open('result.json','w') as output:
    json.dump(result, output, indent=2)
