import sys
from itertools import permutations
exec(open(sys.argv[1]).read().split("def comp")[0])
def fix(base,n):
    w="0" if base[0][0]=="0" else "2"
    while len(w)<n: w=''.join(base[int(c)] for c in w)
    return w[:n]
G=fix(g,400000); Gp=fix(gR,400000)
def facs(w,n,start=1000): return {w[i:i+n] for i in range(start,len(w)-n-1000)}
def crit(w,maxp=3000,N=60000):
    best=0
    for p in range(1,maxp):
        run=0
        for i in range(p,N):
            if w[i]==w[i-p]:
                run+=1
                if (run+p)/p>best: best=(run+p)/p;bp=p
            else: run=0
    return best,bp
for name,fig,base in (("Fig1",F1,g),("Fig2",F2,gR)):
    src=G if name=="Fig1" else Gp
    for h in fig:
        w=''.join(h[int(c)] for c in src[:60000])
        cx=[len(facs(w,n)) - (2*n+1) for n in (5,10,20,40,80)]
        same=[]
        for tag,ref in (("G",G),("G'",Gp)):
            for pi in permutations("012"):
                r=ref.translate(str.maketrans("012",''.join(pi)))
                if facs(w,30)==facs(r,30,): same.append(tag+''.join(pi))
        print(name,h[0][:12],"cx-dev",cx,"same",same,"crit",crit(w,1500,30000))
print("mu",2+1/(1.7548776662466927**2-1))
