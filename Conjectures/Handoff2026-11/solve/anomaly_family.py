# Infinite family of k=2 digital anomalies. Exact integer verification (Python big ints).
from fractions import Fraction
from sympy import factorint
def kappa4(N):
    c=1
    for p,e in factorint(N).items(): c*=p**(-(-e//4))
    return c
def check(x,y,B,k):
    ok = Fraction(x,y)==y+Fraction(x,B**k) and B**(k-1)<=x<B**k
    return ok
m=2; rows=[]
for r in range(0,7):
    N=m*m-1; c=kappa4(N)
    if c<m:
        B=c*m; y=c*c; x=c**4*m*m//(m*m-1)
        assert (c**4*m*m)%(m*m-1)==0
        print(f"r={r} m={m} c={c} B={B} y={y} x={x} digits(B)={len(str(B))} verified={check(x,y,B,2)}")
    else: print(f"r={r} m={m} c={c} (c>=m, no solution from this m)")
    m=2*m*m-1
