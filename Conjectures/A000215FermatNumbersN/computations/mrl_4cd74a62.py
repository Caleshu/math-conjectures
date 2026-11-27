# MathResearchLab experiment 4cd74a62-6128-4d49-93d4-d5ce2f8a9481
# Independent pure-Python cross-check of all P3 stages up to m = 1e7
# sha256(code) = b329f5d6350dc2797db5bae3aced339375e93bb355208a81a9a6c166b3e33f96
# parameters: {"m_max": 10000000, "sq_max": 10000000, "sq_all_max": 1000000, "time_budget_s": 100}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
T0 = time.time()
params = json.load(open(os.environ["MRL_PARAMS"]))
M3 = int(params.get("m_max", 10**7))
SQ = int(params.get("sq_max", 10**7))
SQALL = int(params.get("sq_all_max", 10**6))
B = float(params.get("time_budget_s", 100))
res = {"params": params}
def save():
    with open("result.json", "w") as f: json.dump(res, f, indent=1)
S3 = []
c = {"even": 0, "f1_strong": 0, "f1_weak": 0, "f12_strong": 0, "f12_weak": 0}
reached = 4
for m in range(6, M3 + 1, 2):
    if (m & 0x3FFFE) == 0 and time.time() - T0 > 0.45 * B: break
    c["even"] += 1
    a4 = (m % 4 == 0); a5 = (m % 5 == 0); g2 = (m % 9 not in (1, 8))
    if a4: c["f1_strong"] += 1
    if a4 or a5: c["f1_weak"] += 1
    if a4 and g2: c["f12_strong"] += 1
    if (a4 or a5) and g2: c["f12_weak"] += 1
    if pow(2, m, m - 1) == 1: S3.append(m)
    reached = m
res["stage3_range"] = [6, reached]
st4 = {m: pow(2, m, m + 1) == 1 for m in S3}
st5 = {m: pow(2, m, m * m + 1) == 1 for m in S3}
full = {m: pow(2, m, m**4 - 1) == 1 for m in S3}
def pipe(f1):
    s3 = [m for m in S3 if f1(m) and m % 9 not in (1, 8)]
    s4 = [m for m in s3 if st4[m]]
    s5 = [m for m in s4 if st5[m]]
    return [len(s3), len(s4), s5]
S34 = [m for m in S3 if st4[m]]
S345 = [m for m in S34 if st5[m]]
res["filter_counts_direct"] = c
res["strong_pipeline_s3_s4_s5"] = pipe(lambda m: m % 4 == 0)
res["weak_pipeline_s3_s4_s5"] = pipe(lambda m: m % 4 == 0 or m % 5 == 0)
res["unfiltered"] = {"stage3": len(S3), "stage34": len(S34), "final": S345, "full_direct": [m for m in S3 if full[m]]}
res["near_misses_stage34"] = S34
res["stage3_list"] = S3
r6 = [m for m in S3 if m <= 999999]
res["m_le_999999"] = [len(r6), sum(1 for m in r6 if st4[m]), [m for m in r6 if st4[m] and st5[m]]]
res["sanity"] = {"16,256,65536 final": all(x in S345 for x in (16, 256, 65536)) if reached >= 65536 else "n/a", "36 near miss not final": (36 in S34 and 36 not in S345)}
res["counterexamples"] = [m for m in S345 if not (m & (m - 1) == 0 and ((m.bit_length() - 1) & (m.bit_length() - 2)) == 0)]
save()
Q = []; qreached = 0
for m in range(2, SQ + 1, 2):
    if (m & 0x3FFFE) == 0 and time.time() - T0 > 0.85 * B: break
    if pow(2, m, m * m + 1) == 1: Q.append(m)
    qreached = m
Qodd = []; oreached = 0
for m in range(1, SQALL + 1, 2):
    if (m & 0x3FFFE) == 1 and time.time() - T0 > 0.97 * B: break
    if pow(2, m, m * m + 1) == 1: Qodd.append(m)
    oreached = m
res["sq_even"] = {"range": [2, qreached], "solutions": Q, "all_4|m": all(m % 4 == 0 for m in Q)}
res["sq_odd"] = {"range": [1, oreached], "solutions": Qodd}
res["elapsed_s"] = round(time.time() - T0, 2)
res["summary"] = (f"Pure Python, even m in [6,{reached}]: stage3={len(S3)}, stage3&4={len(S34)}, final={S345}, counterexamples={res['counterexamples']}; "
    f"m<=999999 counts {res['m_le_999999']}; strong pipeline {res['strong_pipeline_s3_s4_s5']}; filter counts {c}; "
    f"m^2+1|2^m-1 even m<={qreached}: {Q}; odd m<={oreached}: {Qodd}.")
save()
print(res["summary"])
