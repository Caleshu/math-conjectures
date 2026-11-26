# For which (m, j) does the counting part of the proof close?
# Hard case: delta(H)>=2, n=m+j, F = {deg >= j+2}, f=|F|<=m-1, a=m-1-f, Lo = rest, |Lo| = j+1+a,
# every Lo vertex has degree in [2, j+1]; gamma = #Lo vertices with >=2 F-neighbours <= a.
# a in {0,1}: closed by the path argument for every j <= m-4.
# For a >= 2 we need one of the bounds below to be <= T := C(m-1,2)+j+1.
from math import comb
def bounds(m, j, a):
    f = m - 1 - a; L = j + 1 + a; n = m + j
    g = min(a, L) if f >= 2 else 0          # max number of good vertices
    s = min(f, j + 1)                        # max F-degree of a good vertex
    out = {}
    out["C0"] = (f * (n - 1) + L * (j + 1)) // 2                  # degree sum
    out["C3"] = comb(f, 2) + ((j + 1) * L + g * s + (L - g)) // 2  # e(F,Lo)+e(Lo) <= (sum_Lo deg + e(F,Lo))/2
    if f >= j:                                                     # then |Lo| <= m, so 2-core of H[Lo] has <= a vertices
        out["C1"] = comb(f, 2) + g * s + (L - g) + L + max(0, comb(a, 2) - a)
    return out
def ok(m, j):
    T = comb(m - 1, 2) + j + 1
    return all(min(bounds(m, j, a).values()) <= T for a in range(2, m))
if __name__ == "__main__":
    for m in [8, 10, 12, 16, 20, 30, 50, 100, 200, 400, 1000]:
        J = 0
        while J + 1 <= m - 4 and ok(m, J + 1): J += 1
        mono = all(ok(m, jj) for jj in range(1, J + 1))
        print(f"m={m:5d}  proof closes for all 1<=j<={J:4d} (j/m={J/m:.3f}, monotone={mono});  conjecture: j<={m-4}")
