# pairs p > M >= 1 with (p^2 - 1) | M^4  ->  digital anomaly (x,y,B) = (M^4 p^2/(p^2-1), M^2, pM), k = 2
from fractions import Fraction
def f4(N):  # least M with N | M^4
    M=1; n=N; d=2
    while d*d<=n:
        if n%d==0:
            e=0
            while n%d==0: n//=d; e+=1
            M*=d**(-(-e//4))
        d+=1
    if n>1: M*=n
    return M
sols=[]
for p in range(2,200000):
    m0=f4(p*p-1)
    if m0<p:
        for M in range(m0,p,m0):
            if (M**4)%(p*p-1)==0:
                B=p*M; y=M*M; x=M**4*p*p//(p*p-1)
                assert Fraction(x,y)==y+Fraction(x,B*B) and B<=x<B*B
                sols.append((B,y,x,p,M))
print(len(sols),"family solutions with p<200000; smallest p's:")
for s in sorted(sols,key=lambda t:t[3])[:30]: print("B=%d y=%d x=%d  p=%d M=%d"%s)
