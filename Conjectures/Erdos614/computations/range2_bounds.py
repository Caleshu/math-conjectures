# Coverage test for candidate proof strategies in range 2.  Hard case: delta(H)>=2, n=m+J, M=m-1,
# F = {deg >= J+2}, f=|F|, a=M-f, L = rest (|L|=J+1+a, degrees in [2,J+1]).
# Closure idea: B = 2-bootstrap closure of F inside L (|B| = beta <= a by gluing),
# R = L \ B (each R-vertex has <= 1 neighbour in F u B), |R| = J+1+a-beta.
# 2-sets inside R have size <= a-beta or > m  (glue with F and a prefix of B).
from math import comb
def T(m,J): return comb(m-1,2)+J+1
def closure_bound(m,J,a,beta):
    M=m-1; f=M-a; R=J+1+a-beta; t=a-beta
    if R > m: return None          # core of R might exceed m: peeling bound unavailable
    eR = max(R-1, comb(t,2)+R-t) if R>0 else 0
    return comb(f,2) + beta*(J+1) + R + eR
def caseII(m,J,a):
    M=m-1; f=M-a; L=J+1+a; s=min(f,J+1)
    return comb(f,2) + (a*s + L - a + (J+1)*L)//2 if f>=1 else (L*(J+1))//2
def covered(m,J,a):
    if a in (0,1) and J<=m-4: return True        # forest-path argument
    t=T(m,J)
    if caseII(m,J,a) <= t: return True
    for beta in range(0,a+1):
        cb=closure_bound(m,J,a,beta)
        if cb is None or cb > t: return False
    return True
for m in (12,20,40,80):
    best=None
    for J in range(1,m-3):
        bad=[a for a in range(0,m) if not covered(m,J,a)]
        if bad and best is None: best=J-1
        if J in ((m-4)//2+1, (m-4)//2+3, m-4) or (bad and best==J-1):
            print(f"m={m} J={J}: uncovered a={bad[:12]}{'...' if len(bad)>12 else ''}")
    print(f"m={m}: all J <= {best} covered  (old proof: J <= {(m-4)//2}; conjecture: J <= {m-4})")

print("\n--- with recursion on the 2-core of R when it exceeds m ---")
def eR_bound(m,J,a,beta):
    M=m-1; R=J+1+a-beta; t=a-beta
    best = max(R-1, comb(t,2)+R-t) if R>0 else 0          # core of size <= t
    for c in range(m+1, R+1):                               # core of size c > m (inside L: degrees <= J+1)
        rec = min(comb(M,2)+(c-m)+1, (c*(J+1))//2)
        best = max(best, rec + (R-c))
    return best
def covered2(m,J,a):
    if a in (0,1) and J<=m-4: return True
    t=T(m,J)
    if caseII(m,J,a) <= t: return True
    M=m-1; f=M-a
    for beta in range(0,a+1):
        R=J+1+a-beta
        if comb(f,2) + beta*(J+1) + R + eR_bound(m,J,a,beta) > t: return False
    return True
for m in (12,20,40,80):
    best=None
    for J in range(1,m-3):
        bad=[a for a in range(0,m) if not covered2(m,J,a)]
        if bad and best is None:
            best=J-1; print(f"m={m} J={J}: first uncovered a={bad[:10]}")
    print(f"m={m}: all J <= {best} covered (old {(m-4)//2}, conjecture {m-4})")
