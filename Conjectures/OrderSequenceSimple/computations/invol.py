from math import prod
def Sp(m,q): return q**(m*m)*prod(q**(2*i)-1 for i in range(1,m+1))
def GL(m,q): return q**(m*(m-1)//2)*prod(q**i-1 for i in range(1,m+1))
def GU(m,q): return q**(m*(m-1)//2)*prod(q**i-(-1)**i for i in range(1,m+1))
def Oodd(m,q): return 2*q**(m*m)*prod(q**(2*i)-1 for i in range(1,m+1))      # O(2m+1,q)
def Oeven(m,q,e): return 2*q**(m*(m-1))*(q**m-e)*prod(q**(2*i)-1 for i in range(1,m)) if m>0 else 1  # O^e(2m,q)
def invPSp(n,q):
    a=sum(Sp(n,q)//(Sp(k,q)*Sp(n-k,q)) for k in range(1,n))
    b=Sp(n,q)//(GL(n,q) if q%4==1 else GU(n,q))
    return (a+b)//2
def invOmega(n,q):
    # involutions -1_W + 1_{W^perp}, W nondegenerate of dim 2k; in Omega iff disc(W) is a square
    tot=0
    for k in range(1,n+1):
        for e in (1,-1):
            # disc of type-e space of dim 2k is (-1)^k * (square if e=+1 else nonsquare)
            minus1_sq = (q%4==1)
            disc_sq = (e==1) == ((k%2==0) or minus1_sq)
            if disc_sq: tot+=Oodd(n,q)//(Oeven(k,q,e)*Oodd(n-k,q))
    return tot
for n,q in ((3,3),(3,5),(4,3)):
    print(f"n={n} q={q}  PSp invol={invPSp(n,q):,}  Omega invol={invOmega(n,q):,}")
print("\nDoes PSp(2n,q) have more involutions than Omega(2n+1,q)?")
for n in range(3,7):
    print(f"n={n}:", ' '.join(f"q={q}:{'yes' if invPSp(n,q)>invOmega(n,q) else 'no'}" for q in (3,5,7,9,11,13,17,19,23,25,27)))
