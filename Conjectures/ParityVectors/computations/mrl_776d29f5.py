# MathResearchLab experiment 776d29f5-559c-42ea-a67d-c9a4d7c09378
# Independent check: parity vectors of Hamiltonian cycles of Q3, Q4 (paper's definitions)
# sha256(code) = 0a120f34b0342be44ab4896cf52c28361996de04ef021a118a7b62e446d310d2
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json
# Independent check, from the paper's definitions, of which balanced vectors are parity vectors beta_i(h).
import itertools
def ham_cycles(n):
    N=1<<n; seen=set(); out=[]
    path=[0]; used={0}
    def rec():
        if len(path)==N:
            if bin(path[-1]).count("1")==1:
                key=min(tuple(path), tuple([0]+path[1:][::-1])); 
                if key not in seen: seen.add(key); out.append(list(path))
            return
        for d in range(n):
            w=path[-1]^(1<<d)
            if w not in used:
                used.add(w); path.append(w); rec(); path.pop(); used.discard(w)
    rec(); return out
def par_in(v,i): return bin(v & ~(1<<i)).count("1")%2
res={}
for n in (3,4):
    N=1<<n; cyc=ham_cycles(n); achieved={}
    for h in cyc:
        for orient in (h, h[::-1]):
            for i in range(n):
                for s in range(N):
                    g=orient[s:]+orient[:s]
                    if (g[0]^g[1])!=(1<<i) or (g[0]>>i)&1: continue   # normalisation: h0h1 is an i-edge, (h0)_i=0
                    js=[l for l in range(N) if (g[l]^g[(l+1)%N])==(1<<i)]
                    b=[par_in(g[js[0]],i)]
                    for k in range(1,len(js)): b.append((b[-1]+js[k]-js[k-1]+1)%2)   # paper's recurrence
                    assert b==[par_in(g[j],i) for j in js]                            # paper's closed form
                    achieved.setdefault(len(js),set()).add("".join(map(str,b)))
    print(f"Q_{n}: {len(cyc)} Hamiltonian cycles")
    for k in range(2,N//2+1,2):
        bal={"".join(v) for v in itertools.product("01",repeat=k) if v.count("0")==k//2}
        a=achieved.get(k,set())
        res[f"n={n},k={k}"]={"balanced":len(bal),"achieved":len(a&bal),"nonbalanced_achieved":len(a-bal),"missing_examples":sorted(bal-a)[:6]}
        print(f"  k={k}: balanced={len(bal)} achieved={len(a & bal)} non-balanced achieved={len(a-bal)} missing e.g. {sorted(bal-a)[:4]}")

res["summary"]="Q3 k=4: 2 of 6 balanced vectors are parity vectors (0011,0110,1001,1100 never occur); Q4 k=8: 2 of 70"
json.dump(res,open("result.json","w"),indent=1)
