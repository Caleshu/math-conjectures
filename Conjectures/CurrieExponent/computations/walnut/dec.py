import sys, itertools
def load(f):
    L=open(f).read().split('\n'); st={}; acc={}; cur=None
    for l in L[1:]:
        l=l.strip()
        if not l: continue
        if '->' in l:
            a,b=l.split('->'); st[cur][tuple(map(int,a.split()))]=int(b)
        else:
            s,o=l.split(); cur=int(s); acc[cur]=int(o); st[cur]={}
    return st,acc
U=[1,2,3]
while len(U)<40: U.append(2*U[-1]-U[-2]+U[-3])
st,acc=load(sys.argv[1]); K=int(sys.argv[2])
res=[]
def go(s,depth,vals):
    if depth==K:
        if acc[s]: res.append(tuple(vals))
        return
    for d,t in st[s].items():
        w=U[K-1-depth]
        go(t,depth+1,[v+di*w for v,di in zip(vals,d)])
go(0,0,[0]*len(next(iter(st[0]))))
res=sorted(set(res),key=lambda x:x[1])
best={}
for n,p in res: best[p]=max(best.get(p,0),n)
for p in sorted(best): print(p,best[p],round(best[p]/p,5))
