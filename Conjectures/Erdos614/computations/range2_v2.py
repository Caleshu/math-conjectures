# Sound version: recursion on the core C of R only when |C| - m < J (i.e. f + beta >= 1).
from math import comb
import sys
def T(m,J): return comb(m-1,2)+J+1
def caseII(m,J,a):
    M=m-1; f=M-a; L=J+1+a; s=min(f,J+1)
    return comb(f,2) + (a*s + L - a + (J+1)*L)//2 if f>=1 else (L*(J+1))//2
def eR(m,J,a,beta):
    M=m-1; f=M-a; R=J+1+a-beta; t=a-beta
    best = max(R-1, comb(t,2)+R-t) if R>0 else 0
    if R >= m+1:
        if f+beta >= 1:
            A = comb(M,2)-m+1
            # max over c in [m+1,R] of min(A+c, c(J+1)//2) + R - c ; nondecreasing in c -> c=R
            c=R; best=max(best, min(comb(M,2)+(c-m)+1, (c*(J+1))//2) + R - c)
        else:
            best=max(best, (R*(J+1))//2)
    return best
def covered(m,J,a):
    if a in (0,1) and J<=m-4: return True
    t=T(m,J)
    if caseII(m,J,a) <= t: return True
    f=m-1-a
    return all(comb(f,2)+beta*(J+1)+(J+1+a-beta)+eR(m,J,a,beta) <= t for beta in range(a+1))
def frontier(m):
    for J in range(1,m-3):
        if any(not covered(m,J,a) for a in range(m)): return J-1
    return m-4
for m in [int(x) for x in sys.argv[1:]]:
    Jm=frontier(m); print(f"m={m}: proven-by-this-scheme J <= {Jm}  (J/m = {Jm/m:.3f}; old {(m-4)//2}, conj {m-4})")
