# Checks, exactly as written in the README proof, that for every m >= 2j+4, j >= 1, and every
# a in [2, m-1], the case's inequality gives e(H) <= T := C(m-1,2)+j+1.  (a in {0,1}: path argument.)
from math import comb
def case_bound(m, j, a):
    f = m - 1 - a; L = j + 1 + a; T = comb(m - 1, 2) + j + 1
    if a <= j - 1:                       # Case I: core bound (f >= j holds here)
        assert f >= j
        s = j + 1
        core = 0 if a == 2 else comb(a, 2) - a
        e = comb(f, 2) + (a * s + (L - a)) + (L + core)
        return "I", e, T
    s = min(f, j + 1)                    # Case II: half-degree-sum bound
    eFL = (a * s + (L - a)) if f >= 1 else 0
    e2 = (j + 1) * L + eFL               # = 2 e(F,Lo) + 2 e(Lo) upper bound numerator
    return "II", comb(f, 2) + e2 / 2, T
bad = 0; checked = 0
for m in range(6, 501):
    for j in range(1, (m - 4) // 2 + 1):
        for a in range(2, m):
            c, e, T = case_bound(m, j, a); checked += 1
            if e > T: bad += 1; print("FAIL", m, j, a, c, e, T)
print("checked", checked, "cases; failures:", bad)
