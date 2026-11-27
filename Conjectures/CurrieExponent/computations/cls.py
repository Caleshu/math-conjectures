import sys
from itertools import permutations
exec(open(sys.argv[1]).read().split("def comp")[0])
def fix(base,n):
    w="0" if base[0][0]=="0" else "2"
    while len(w)<n: w=''.join(base[int(c)] for c in w)
    return w[:n]
G=fix(g,300000); Gp=fix(gR,300000)
def facs(w,n): return frozenset(w[i:i+n] for i in range(2000,len(w)-n-2000))
words={}
for name,fig,src in (("F1",F1,G),("F2",F2,Gp)):
    for j,h in enumerate(fig):
        words[f"{name}.{j+1}"]=''.join(h[int(c)] for c in src[:40000])
n=25
canon={}
for k,w in words.items():
    forms=[]
    for rev in (False,True):
        ww=w[::-1] if rev else w
        for pi in permutations("012"):
            forms.append(facs(ww.translate(str.maketrans("012",''.join(pi))),n))
    canon[k]=forms
keys=list(words)
classes=[]
for k in keys:
    for c in classes:
        if facs(words[c[0]],n) in canon[k]: c.append(k);break
    else: classes.append([k])
print(classes)
