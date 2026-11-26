# v3: replace the recursion for a big core C of R (|C| = c > m, degrees <= D = J+1, no m-subset 2-set)
# by the "stuck descent" lemma:
#   e(C) <= (c-m-1)*D + max_{m < x <= c} [ min(C(x//2,2), (x//2)*D//2) + x ]
# (delete vertices with no degree-2 neighbour; stuck set X has >= |X|/2 degree-2 vertices).
from math import comb
import sys
def T(m,J): return comb(m-1,2)+J+1
def caseII(m,J,a):
    M=m-1; f=M-a; L=J+1+a; s=min(f,J+1)
    return comb(f,2) + (a*s + L - a + (J+1)*L)//2 if f>=1 else (L*(J+1))//2
def stuck(c,m,D):
    best=0
    for x in range(m+1,c+1):
        h=x//2   # at most x - ceil(x/2) = floor(x/2) vertices of degree > 2
        best=max(best, min(comb(h,2), (h*D)//2) + x)
    return (c-m-1)*D + best
def eR(m,J,a,beta):
    M=m-1; f=M-a; R=J+1+a-beta; t=a-beta; D=J+1
    best = max(R-1, comb(t,2)+R-t) if R>0 else 0
    for c in range(m+1,R+1):
        best=max(best, min(stuck(c,m,D), (c*D)//2) + R - c)
    return best
def covered(m,J,a):
    if a in (0,1) and J<=m-4: return True
    t=T(m,J)
    if caseII(m,J,a) <= t: return True
    f=m-1-a
    return all(comb(f,2)+b*(J+1)+(J+1+a-b)+eR(m,J,a,b) <= t for b in range(a+1))
def frontier(m):
    for J in range(1,m-3):
        if any(not covered(m,J,a) for a in range(m)): return J-1
    return m-4
if __name__=="__main__":
    for m in [int(x) for x in sys.argv[1:]]:
        Jm=frontier(m); print(f"m={m}: J <= {Jm} (J/m={Jm/m:.3f}; old {(m-4)//2}, conj {m-4})", flush=True)
