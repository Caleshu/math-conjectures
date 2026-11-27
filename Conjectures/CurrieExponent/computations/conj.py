from itertools import permutations
F1=[("1210202","12102","1210202102"),("1210202102","1210202","121020210202"),
    ("021201212","0212012","021201212012"),("21021102211021102","2102110221102","2102110221102110221102")]
F2=[("10212","0212","0210212"),("2120210","20210","202120210"),("121201210","1201210","120121201210"),
    ("1201212010","1212010","121201212010"),("1212010","12010","1201212010"),("221102210","21102210","2110221102210")]
g=["01","2","02"]; gR=["10","2","20"]
def comp(f,h): return [ ''.join(f[int(c)] for c in h[i]) for i in range(3)]
def powers(base,K):
    f=["0","1","2"]; out=[]
    for k in range(1,K+1):
        f=comp(f,base) if False else [''.join(base[int(c)] for c in w) for w in f]  # f = base∘f? use iterate
        out.append((k,f))
    return out
def pows(base,K):
    f=list(base); res=[(1,f)]
    for k in range(2,K+1):
        f=[''.join(base[int(c)] for c in w) for w in f]; res.append((k,f))
    return res
def conj(h,f):
    # find p with p+h(x) == f(x)+p  (h = p^{-1} f p, i.e. h(w)= p^{-1} f(w) p)  or f(x)+p == p + h(x) reversed roles
    if [len(a) for a in h]!=[len(a) for a in f]: return None
    L=max(len(a) for a in h)
    for n in range(0,3*L):
        # p determined: p+h(x)=f(x)+p => p is prefix of f(x)^inf
        for side in ("L","R"):
            ok=True; ps=set()
            for x in range(3):
                a,b=(f[x],h[x]) if side=="L" else (h[x],f[x])
                p=(a*(n//len(a)+2))[:n]
                if p+b!=a+p: ok=False;break
                ps.add(p)
            if ok and len(ps)==1: return side,ps.pop()
    return None
for name,fig,base in (("Fig1",F1,g),("Fig2",F2,gR)):
    for h in fig:
        found=None
        for k,f in pows(base,25):
            for pi in permutations("012"):
                pf=[w.translate(str.maketrans("012",''.join(pi))) for w in f]
                c=conj(list(h),pf)
                if c: found=(k,''.join(pi),c);break
            if found:break
        print(name,h,found)
