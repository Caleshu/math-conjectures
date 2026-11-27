import re,glob,sys
kuca={4:lambda b:[4,2*b,4*b+4,12*b-4],6:lambda b:[6,2*b,4*b+6],8:lambda b:[8,2*b,4*b+8,8*b+8,24*b-8],
10:lambda b:[10,2*b,4*b+10,8*b+10],12:lambda b:[12,2*b,4*b+12,8*b+12,12*b+12,20*b+12,28*b-12,38*b+48],
14:lambda b:[14,2*b,4*b+14,8*b+14,12*b+14,22*b+14,30*b-14],16:lambda b:[16,2*b,4*b+16,8*b+16,12*b+16,16*b+16,24*b+16,32*b+16,44*b-16,44*b+16]}
def load(d):
    res={}
    for f in glob.glob(d+'/*.txt'):
        a,b=map(int,re.findall(r'(\d+)_(\d+)',f)[0]); s=open(f).read()
        m=re.search(r'even terms <= \d+:([\d ]+)',s); ev=list(map(int,m.group(1).split())) if m else None
        st='PROVED' if 'PROVED' in s else ('inconclusive' if 'inconclusive' in s else ('FAIL' if 'FAIL' in s else ('running/timeout' )))
        P=re.search(r'period P=(\d+)',s); res[(a,b)]=(ev,st,int(P.group(1)) if P else None, '...' in s)
    return res
V=load('V')
print("V(a,b): proved / total; mismatches with Kuca Conj 4.1:")
for a in sorted(set(k[0] for k in V)):
    ks=sorted(b for (aa,b) in V if aa==a); pr=[b for b in ks if V[(a,b)][1]=='PROVED']
    mism=[b for b in ks if V[(a,b)][0] is not None and not V[(a,b)][3] and sorted(V[(a,b)][0])!=sorted(kuca[a](b))]
    inc=[(b,V[(a,b)][1]) for b in ks if V[(a,b)][1]!='PROVED']
    print(f" a={a}: proved {len(pr)}/{len(ks)} b={pr}; not proved: {inc}; even set != Kuca formula: {mism}")
U=load('U')
print("U(a,b):")
for a in sorted(set(k[0] for k in U)):
    ks=sorted(b for (aa,b) in U if aa==a); pr=[b for b in ks if U[(a,b)][1]=='PROVED']
    inc=[(b,U[(a,b)][1]) for b in ks if U[(a,b)][1]!='PROVED']
    print(f" a={a}: proved {len(pr)}/{len(ks)} b={pr}; not proved: {inc}")
    for b in pr[:40]: print(f"    U({a},{b}) evens {U[(a,b)][0]} P={U[(a,b)][2]}")
