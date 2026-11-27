# (C2): rank check of the rigid divisors forced by the N[v]-cut exception (v = 0 by symmetry).
import subprocess
N=64; nbr=[[v^(1<<k) for k in range(6)] for v in range(N)]
wt=lambda v: bin(v).count('1')
def reduce(D,q):
    D=D[:]
    while True:
        burnt=[False]*N; cnt=[0]*N; burnt[q]=True; st=[q]; nb=1
        while st:
            u=st.pop()
            for w in nbr[u]:
                if burnt[w]: continue
                cnt[w]+=1
                if cnt[w]>D[w]: burnt[w]=True; st.append(w); nb+=1
        if nb==N: return D
        t=min(D[u]//cnt[u] for u in range(N) if not burnt[u] and cnt[u]>0)
        for u in range(N):
            if not burnt[u]:
                D[u]-=t*cnt[u]
                for w in nbr[u]:
                    if burnt[w]: D[w]+=t
def unreachable(D): return [v for v in range(N) if D[v]==0 and reduce(D,v)[v]==0]
A=[5 if wt(v)==1 else 0 for v in range(N)]   # 5 chips on each neighbor of 0
B=[2 if wt(v)==2 else 0 for v in range(N)]   # 2 chips on each vertex at distance 2
for name,base in (("5*N(0)",A),("2*S2(0)",B)):
    print(name, "degree", sum(base), "unreachable:", len(unreachable(base)))
    worst=None; ok=0
    for u in range(N):
        D=base[:]; D[u]+=1; k=len(unreachable(D))
        if k==0: print("  POSITIVE RANK with extra chip at", u)
        else: ok+=1; worst=k if worst is None else min(worst,k)
    print(f"  degree 31: {ok}/64 have rank 0; fewest unreachable vertices = {worst}")
