import sys
def dec(s):
    n=ord(s[0])-63; bits=[]
    for ch in s[1:]:
        v=ord(ch)-63; bits+= [(v>>b)&1 for b in range(5,-1,-1)]
    E=[];t=0
    for j in range(1,n):
        for i in range(j):
            if bits[t]: E.append((i,j))
            t+=1
    return n,E
for s in sys.argv[1:]:
    n,E=dec(s); deg=[0]*n
    for a,b in E: deg[a]+=1;deg[b]+=1
    print(s,"n=",n,"e=",len(E),"deg=",sorted(deg,reverse=True)); print("  ",E)
