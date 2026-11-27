import sys
exec(open('dec.py').read().split('U=[1,2,3]')[0])
U=[1,2,3]
while len(U)<40: U.append(2*U[-1]-U[-2]+U[-3])
st,acc=load(sys.argv[1]); K=int(sys.argv[2])
out=[]
def go(s,d,ds):
    if d==K:
        if acc[s]: out.append(ds)
        return
    for dd,t in st[s].items(): go(t,d+1,ds+[dd])
go(0,0,[])
best={}
for ds in out:
    n=sum(x[0]*U[K-1-j] for j,x in enumerate(ds)); p=sum(x[1]*U[K-1-j] for j,x in enumerate(ds))
    if n>best.get(p,(0,))[0]: best[p]=(n,''.join(str(x[0]) for x in ds).lstrip('0'),''.join(str(x[1]) for x in ds).lstrip('0'))
for p in sorted(best): print(p,*best[p])
print('distinct p:',len(best),'pairs:',len(out))
