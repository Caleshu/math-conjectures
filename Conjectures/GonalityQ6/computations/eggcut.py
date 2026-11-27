import itertools
n=6; N=64
nbr=[[v^(1<<k) for k in range(n)] for v in range(N)]
def bd(U):
    U=set(U); return sum(1 for u in U for w in nbr[u] if w not in U)
# (a) Harper's edge-isoperimetric bound: min boundary of an m-set in Q6 is 6m - 2*h(m), h(m)=sum popcount(i), i<m
h=lambda m: sum(bin(i).count('1') for i in range(m))
mb={m:6*m-2*h(m) for m in range(1,33)}
print("min boundary by size:", mb)
print("min over sizes 11..32:", min(mb[m] for m in range(11,33)), " | size 10:", mb[10])
# (b) supersets of N[0] with at most 10 vertices
C=[0]+nbr[0]; rest=[v for v in range(N) if v not in C]
best=min(bd(C+list(extra)) for r in range(4) for extra in itertools.combinations(rest,r))
print("min boundary of any U with N[v] ⊆ U, |U|<=10:", best)
