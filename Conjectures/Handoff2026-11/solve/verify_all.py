import re
from fractions import Fraction
from sympy import factorint
def kappa(N,r):
    c=1
    for p,e in factorint(N).items(): c*=p**(-(-e//r))
    return c
# brute-force list of all m <= 10^5 (independent of the C sieve) to cross-check the count
ms=[m for m in range(2,100001) if kappa(m*m-1,4)<m]
print("independent count m<=1e5:",len(ms))
ok=0; Bs=[]
for m in ms:
    c=kappa(m*m-1,4); B=c*m; y=c*c; x=c**4*m*m//(m*m-1)
    assert c**4*m*m%(m*m-1)==0
    assert Fraction(x,y)==y+Fraction(x,B*B) and B<=x<B*B
    ok+=1; Bs.append(B)
print("verified anomalies:",ok)
old=[int(l.split('B=')[1]) for l in open('/home/claude/round2/k2.txt') if 'anomaly' in l]
fam=sorted(b for b in Bs if b<=200000)
print("family B<=200000:",fam)
print("all in exhaustive list:",set(fam)<=set(old), " exhaustive list size",len(old))
