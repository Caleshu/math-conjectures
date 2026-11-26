# Checks the exact case split used in the Lean proof (degree-sum form).
# Hard case: |U| = m+J, J>=1, 2J+4<=m, all deg_U >= 2; F = {deg_U >= J+2}, f=|F|, a=m-1-f, |L|=J+1+a.
# gamma <= a good vertices (>=2 F-nbrs), each L-vertex has <= s := min(f, J+1) F-nbrs.
#  a = 0           : contradiction (glue all of L)
#  1 <= a <= J     : B_I  = f(f-1) + 2(gamma*s + L - gamma) + max(2(L-1), a(a-1)+2(L-a))   [needs f >= J]
#  a >= J+1        : B_II = f(f-1) + (gamma*s + L - gamma) + (J+1)L
# target: D(U) <= T2 := (m-1)(m-2) + 2J + 2
bad = 0; n = 0
for m in range(6, 71):
    for J in range(1, (m - 4) // 2 + 1):
        T2 = (m - 1) * (m - 2) + 2 * J + 2
        for a in range(1, m):
            f = m - 1 - a; L = J + 1 + a; smax = min(f, J + 1)
            for g in range(0, a + 1):
                for s in range(0, smax + 1):
                    X = g * s + (L - g)
                    if a <= J:
                        assert f >= J
                        B = f * (f - 1) + 2 * X + max(2 * (L - 1), a * (a - 1) + 2 * (L - a))
                    else:
                        B = f * (f - 1) + X + (J + 1) * L
                    n += 1
                    if B > T2: bad += 1; print("FAIL", m, J, a, g, s, B, T2) if bad < 10 else None
print("cases", n, "failures", bad)
