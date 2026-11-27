# MathResearchLab experiment 2b7f0da2-2944-4eac-af57-21ceeabf949f
# Check of an explicit equi-independent set of size 20 in Q6
# sha256(code) = 154962f16ecba9df90e8bd481818ce3cc81115223dbab5987fee5c99445f6c65
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 60, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 485, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json
W=[0,7,11,13,14,19,21,22,24,31,33,34,36,40,47,48,55,57,58,60]
S=set(W)
indep=all(bin(a^b).count("1")!=1 for a in S for b in S)
even=sum(bin(v).count("1")%2==0 for v in S)
res={"size":len(S),"in_Q6":all(0<=v<64 for v in S),"independent":indep,"even":even,"odd":len(S)-even,"bound_2^(n-2)":16}
res["summary"]=f"Witness of size {len(S)} in Q6: independent={indep}, parity classes {even}/{len(S)-even}; exceeds 2^(6-2)=16"
json.dump(res,open("result.json","w"),indent=1)
