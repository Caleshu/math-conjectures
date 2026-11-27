import itertools,sys
L=int(sys.argv[1]); N=int(sys.argv[2])
def occ(w,x): return sum(1 for i in range(len(x)-L+1) if x[i:i+L]==w)
def corr(a,b): return sum(2**k for k in range(1,L) if a[L-k:]==b[:k])
words=[''.join(p) for p in itertools.product('01',repeat=L)]
bad=0;cnt=0
for a in words:
  for b in words:
    if a==b or not corr(a,a)>corr(b,b): continue
    cs={k for k in range(1,L) if a[L-k:]==a[:k]}^{k for k in range(1,L) if b[L-k:]==b[:k]}
    n0=2*L-max(cs)
    for n in range(N+1):
      aw=bw=0
      for x in itertools.product('01',repeat=n):
        x=''.join(x); d=occ(a,x)-occ(b,x)
        aw+=d>0; bw+=d<0
      cnt+=1
      if not (2*bw<2**n): bad+=1
      if n>=n0 and not aw<bw: bad+=1; print("i",a,b,n)
      if n<n0 and aw!=bw: print("eq",a,b,n)
print(cnt,bad)
