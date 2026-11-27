# MathResearchLab experiment 87586532-475d-44e4-912d-0ab910ee7b7a
# Sieved compiled exhaustive search for P3 reverse direction up to m ~ 4.29e9
# sha256(code) = 28a1a0a2eab16953843050868b33257cfd8516fc0eb0a0156c1e72715f6647e9
# parameters: {"m_max": 4294968296, "time_budget_s": 85, "sieve_bound": 262144, "sq_max": 10000000, "near_miss_bound": 1000000000, "chunk": 50000000, "brute_max": 2000000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, sys, time, subprocess, shutil, random, math
from concurrent.futures import ThreadPoolExecutor

T0 = time.time()
params = json.load(open(os.environ["MRL_PARAMS"]))
M_MAX = int(params.get("m_max", 4294968296))
BUDGET = float(params.get("time_budget_s", 85))
P = int(params.get("sieve_bound", 262144))
SQ_MAX = int(params.get("sq_max", 10**7))
NM_BOUND = int(params.get("near_miss_bound", 10**9))
CHUNK = int(params.get("chunk", 50_000_000))
BRUTE_MAX = int(params.get("brute_max", 2_000_000))
DEADLINE = T0 + BUDGET
if CHUNK % 2: CHUNK += 1

result = {"params": params, "notes": []}
def save():
    with open("result.json", "w") as f:
        json.dump(result, f, indent=1, default=str)

C_SRC = r'''
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
typedef unsigned __int128 u128;
typedef uint64_t u64;
typedef uint32_t u32;
static double now_s(void){struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return (double)t.tv_sec+1e-9*(double)t.tv_nsec;}
static inline u64 mont_mul(u64 a,u64 b,u64 n,u64 ninv){u128 T=(u128)a*b; u64 q=(u64)T*ninv; u128 t=(T+(u128)q*n)>>64; u64 r=(u64)t; return r>=n?r-n:r;}
/* returns 1 iff 2^e == 1 mod n ; n odd, 1<n<2^62, e>=1 */
static int pow2_is_one(u64 n,u64 e){
  u64 inv=n; for(int i=0;i<6;i++) inv*=2-n*inv;
  u64 ninv=(u64)0-inv; u64 one=((u64)0-n)%n;
  u64 x=one<<1; if(x>=n) x-=n;
  int top=63-__builtin_clzll(e);
  for(int b=top-1;b>=0;b--){ x=mont_mul(x,x,n,ninv); if((e>>b)&1ULL){ x<<=1; if(x>=n) x-=n; } }
  return x==one;}
static u64 powmod_plain(u64 b,u64 e,u64 n){u64 r=1%n; b%=n; while(e){ if(e&1ULL) r=(u64)(((u128)r*b)%n); b=(u64)(((u128)b*b)%n); e>>=1;} return r;}
static u32 *D,*O; static int ND=0;
static void setup(u32 P){
  u32 *spf=(u32*)calloc((size_t)P+1,sizeof(u32));
  for(u32 i=2;i<=P;i++) if(!spf[i]) for(u64 j=i;j<=P;j+=i) if(!spf[j]) spf[j]=i;
  D=(u32*)malloc((size_t)P*sizeof(u32)); O=(u32*)malloc((size_t)P*sizeof(u32));
  for(u32 q=3;q<=P;q+=2){ if(spf[q]!=q) continue;
    for(u64 d=q; d<=P; d*=q){
      u64 phi=d/q*(q-1); u64 o=phi; u32 t=q-1;
      while(t>1){ u32 f=spf[t]; while(o%f==0 && powmod_plain(2,o/f,d)==1) o/=f; while(t%f==0) t/=f; }
      if(d>q){ while(o%q==0 && powmod_plain(2,o/q,d)==1) o/=q; }
      if(o<=2) continue;
      D[ND]=(u32)d; O[ND]=(u32)o; ND++;
    }
  }
  free(spf);
}
int main(int argc,char**argv){
  if(argc<4) return 1;
  const char*mode=argv[1];
  u64 lo=strtoull(argv[2],0,10), hi=strtoull(argv[3],0,10);
  if(!strcmp(mode,"brute")){
    if(lo%2) lo++; if(lo<6) lo=6;
    for(u64 m=lo;m<=hi;m+=2) if(powmod_plain(2,m,m-1)==1) printf("S %llu\n",(unsigned long long)m);
    printf("DONE %llu 0\n",(unsigned long long)(hi-(hi%2))); return 0;}
  if(!strcmp(mode,"sq")){
    if(lo%2) lo++; if(lo<2) lo=2;
    for(u64 m=lo;m<=hi;m+=2){ u64 n=m*m+1; if(pow2_is_one(n,m)) printf("Q %llu\n",(unsigned long long)m);} 
    printf("DONE %llu 0\n",(unsigned long long)(hi-(hi%2))); return 0;}
  if(!strcmp(mode,"sieve")){
    double budget=atof(argv[4]); u32 PP=(u32)strtoul(argv[5],0,10);
    double t0=now_s(); setup(PP);
    if(lo%2) lo++; if(lo<6) lo=6;
    const u64 B=1ULL<<21; unsigned char*alive=(unsigned char*)malloc(B);
    u64 surv=0, reached=lo-2;
    for(u64 blo=lo; blo<=hi; blo+=2*B){
      if(now_s()-t0>budget) break;
      u64 cnt=(hi-blo)/2+1; if(cnt>B) cnt=B;
      memset(alive,1,cnt);
      for(int k=0;k<ND;k++){ u64 d=D[k], o=O[k], md=2*d;
        u64 off=(d+1+md-(blo%md))%md; u64 idx=off>>1; if(idx>=cnt) continue;
        u64 r=(blo+off)%o, s=md%o;
        for(;idx<cnt;idx+=d){ if(r) alive[idx]=0; r+=s; if(r>=o) r-=o; }
      }
      for(u64 i=0;i<cnt;i++) if(alive[i]){ u64 m=blo+2*i; surv++; if(pow2_is_one(m-1,m)) printf("S %llu\n",(unsigned long long)m); }
      reached=blo+2*(cnt-1);
    }
    printf("INFO %d\n",ND);
    printf("DONE %llu %llu\n",(unsigned long long)reached,(unsigned long long)surv); return 0;}
  return 1;
}
'''

def compile_c():
    with open("p3search.c", "w") as f: f.write(C_SRC)
    log = []
    for cc in ["cc", "gcc", "clang"]:
        if not shutil.which(cc): continue
        for flags in (["-O3", "-march=native"], ["-O2"]):
            try:
                p = subprocess.run([cc] + flags + ["-o", "p3search", "p3search.c"], capture_output=True, text=True, timeout=60)
                log.append([cc, flags, p.returncode, p.stderr[:300]])
                if p.returncode == 0 and os.path.exists("p3search"):
                    return os.path.abspath("p3search"), log
            except Exception as e:
                log.append([cc, flags, repr(e)])
    return None, log

def parse(out):
    S, Q, done, info = [], [], None, None
    for line in out.splitlines():
        t = line.split()
        if not t: continue
        if t[0] == "S": S.append(int(t[1]))
        elif t[0] == "Q": Q.append(int(t[1]))
        elif t[0] == "DONE": done = (int(t[1]), int(t[2]))
        elif t[0] == "INFO": info = int(t[1])
    return S, Q, done, info

def ncpu():
    try: return max(1, min(16, len(os.sched_getaffinity(0))))
    except Exception: return max(1, min(16, os.cpu_count() or 1))

def F(x, pred, period=180):
    if x < 0: return 0
    q, r = divmod(x + 1, period)
    full = sum(1 for j in range(period) if pred(j))
    return q * full + sum(1 for j in range(r) if pred(j))
def cnt(a, b, pred): return F(b, pred) - F(a - 1, pred)
ev = lambda m: m % 2 == 0
f1s = lambda m: m % 4 == 0
f1w = lambda m: m % 2 == 0 and (m % 4 == 0 or m % 5 == 0)
f2 = lambda m: m % 9 not in (1, 8)
def is_fermat_m(m):
    if m < 16 or m & (m - 1): return False
    e = m.bit_length() - 1
    return e >= 4 and (e & (e - 1)) == 0

exe, clog = compile_c()
result["compile_log"] = clog
result["compiled"] = exe is not None
K = ncpu(); result["workers"] = K
S3 = []; cov = 5; extra_pieces = []; sq_list = []; sq_cov = 1; chunk_info = []

if exe is not None:
    # ---- validation: sieve vs brute on [6, BRUTE_MAX]
    ob = subprocess.run([exe, "brute", "6", str(BRUTE_MAX)], capture_output=True, text=True, timeout=60).stdout
    os_ = subprocess.run([exe, "sieve", "6", str(BRUTE_MAX), "60", str(P)], capture_output=True, text=True, timeout=60).stdout
    Sb, _, db, _ = parse(ob); Ss, _, ds, nd = parse(os_)
    result["validation_sieve_vs_brute"] = {"range": [6, BRUTE_MAX], "brute_count": len(Sb), "sieve_count": len(Ss), "identical": Sb == Ss, "sieve_table_entries": nd, "brute_done": db, "sieve_done": ds}
    save()
    # ---- squares search m^2+1 | 2^m-1, even m in [2, SQ_MAX]
    pieces = []; step = (SQ_MAX // K) + 2
    lo = 2
    while lo <= SQ_MAX:
        hi = min(SQ_MAX, lo + step); pieces.append((lo, hi)); lo = hi + 1
    def sqwork(pc):
        o = subprocess.run([exe, "sq", str(pc[0]), str(pc[1])], capture_output=True, text=True, timeout=60).stdout
        return parse(o)
    with ThreadPoolExecutor(max_workers=K) as ex:
        outs = list(ex.map(sqwork, pieces))
    ok = all(o[2] is not None for o in outs)
    for o in outs: sq_list += o[1]
    sq_list.sort(); sq_cov = SQ_MAX if ok else None
    # python validation of sq for m <= 200000
    pyq = [m for m in range(2, min(SQ_MAX, 200000) + 1, 2) if pow(2, m, m * m + 1) == 1]
    result["validation_sq"] = {"python_list_upto_2e5": pyq, "c_list_upto_2e5": [m for m in sq_list if m <= 200000], "match": pyq == [m for m in sq_list if m <= 200000], "all_reported_reverified": all(pow(2, m, m * m + 1) == 1 for m in sq_list)}
    save()
    # ---- main sieve run
    chunks = []; lo = 6
    while lo <= M_MAX:
        hi = min(M_MAX, lo + CHUNK - 1); chunks.append((lo, hi)); lo = hi + 1
        if lo % 2: lo += 1
    def work(ch):
        lo, hi = ch
        rem = DEADLINE - time.time()
        if rem < 2: return {"lo": lo, "hi": hi, "status": "not_run", "S": []}
        try:
            o = subprocess.run([exe, "sieve", str(lo), str(hi), "%.2f" % (rem - 1), str(P)], capture_output=True, text=True, timeout=rem + 15).stdout
        except subprocess.TimeoutExpired:
            return {"lo": lo, "hi": hi, "status": "timeout", "S": []}
        S, _, d, _ = parse(o)
        if d is None: return {"lo": lo, "hi": hi, "status": "error", "S": S}
        last_even = hi - (hi % 2)
        st = "complete" if d[0] >= last_even else "partial"
        return {"lo": lo, "hi": hi, "status": st, "reached": d[0], "sieve_survivors": d[1], "S": S}
    t_main = time.time()
    with ThreadPoolExecutor(max_workers=K) as ex:
        res = list(ex.map(work, chunks))
    result["main_run_seconds"] = round(time.time() - t_main, 2)
    res.sort(key=lambda r: r["lo"])
    broken = False; sieve_surv = 0
    for r in res:
        if not broken and r["status"] == "complete":
            cov = r["hi"]; S3 += r["S"]; sieve_surv += r["sieve_survivors"]
        elif not broken:
            broken = True
            if r["status"] == "partial":
                cov = r["reached"]; S3 += [m for m in r["S"] if m <= cov]; sieve_surv += r["sieve_survivors"]
        else:
            if r["status"] in ("complete", "partial"):
                extra_pieces.append({"lo": r["lo"], "reached": r.get("reached"), "S": r["S"]})
    result["chunk_status_counts"] = {s: sum(1 for r in res if r["status"] == s) for s in set(r["status"] for r in res)}
    result["sieve_survivors_tested_by_modexp"] = sieve_surv
else:
    result["notes"].append("No C compiler: pure-Python fallback (no sieve), much smaller range.")
    m = 6
    while m <= M_MAX:
        if (m & 0xFFFE) == 0 and time.time() > T0 + BUDGET * 0.6: break
        if pow(2, m, m - 1) == 1: S3.append(m)
        cov = m; m += 2
    m = 2
    while m <= SQ_MAX:
        if (m & 0xFFFE) == 0 and time.time() > T0 + BUDGET: break
        if pow(2, m, m * m + 1) == 1: sq_list.append(m)
        sq_cov = m; m += 2

S3 = sorted(set(S3))
if cov % 2: cov -= 1
result["covered_range_m"] = [6, cov]
result["covered_range_n"] = [7, cov + 1]
# re-verify stage-3 hits and spot-check removed values
re_ok = all(pow(2, m, m - 1) == 1 for m in S3)
random.seed(12345); S3set = set(S3); bad = []; nsample = 0
if cov >= 6:
    for _ in range(50000):
        m = random.randrange(6, cov + 1); m -= m % 2
        if m < 6 or m in S3set: continue
        nsample += 1
        if pow(2, m, m - 1) == 1: bad.append(m)
result["reverify_stage3_hits"] = re_ok
result["random_negative_spotcheck"] = {"n_checked": nsample, "false_negatives": bad[:20]}

st4 = {m: pow(2, m, m + 1) == 1 for m in S3}
st5 = {m: pow(2, m, m * m + 1) == 1 for m in S3}
full = {m: pow(2, m, m**4 - 1) == 1 for m in S3}
def pipeline(f1):
    a = 6; b = cov
    n_even = cnt(a, b, ev)
    n1 = cnt(a, b, lambda x: ev(x) and f1(x))
    n12 = cnt(a, b, lambda x: ev(x) and f1(x) and f2(x))
    s3 = [m for m in S3 if f1(m) and f2(m)]
    s4 = [m for m in s3 if st4[m]]
    s5 = [m for m in s4 if st5[m]]
    return {"even": n_even, "after_filter1": n1, "after_filter2": n12, "after_stage3": len(s3), "after_stage4": len(s4), "after_stage5": len(s5), "final": s5}
result["pipeline_strong_4|m"] = pipeline(f1s)
result["pipeline_weak_4|m_or_5|m"] = pipeline(lambda x: x % 4 == 0 or x % 5 == 0)
S34 = [m for m in S3 if st4[m]]
S345 = [m for m in S34 if st5[m]]
result["unfiltered"] = {"even": cnt(6, cov, ev), "stage3": len(S3), "stage3and4": len(S34), "stage3and4and5": S345,
    "full_condition_direct": [m for m in S3 if full[m]], "consistency_full_eq_345": [m for m in S3 if full[m]] == S345}
result["counterexamples_P3_reverse"] = [m for m in S345 if not is_fermat_m(m)]
result["positive_controls"] = {str(m): (m in S345) if m <= cov else "not_covered" for m in [16, 256, 65536, 2**32]}
result["theory_checks"] = {
    "all_S34_satisfy_mod9_filter": all(f2(m) for m in S34),
    "all_S34_satisfy_mod5_rule": all(not (m % 5 in (1, 4) and m % 4 == 2) for m in S34),
    "all_S3_satisfy_not_1_mod_9": all(m % 9 != 1 for m in S3),
    "all_final_4|m": all(m % 4 == 0 for m in S345),
    "m36_in_S34_not_S5": (36 in S34) and (36 not in S345)}
r6 = [m for m in S3 if m <= 999999]
result["compare_E_e72d1f_m_le_999999"] = {"stage3": len(r6), "stage34": sum(1 for m in r6 if st4[m]), "final": [m for m in r6 if st4[m] and st5[m]], "expected": [121, 35, [16, 256, 65536]]}
# near misses with factorizations
nm = []
try:
    import sympy
    have_sympy = True
except Exception:
    have_sympy = False
for m in S34:
    rec = {"m": m, "n": m + 1, "le_1e9": m <= NM_BOUND, "stage5": st5[m], "2^m mod (m^2+1)": pow(2, m, m * m + 1)}
    if have_sympy and time.time() < T0 + BUDGET + 20:
        rec["factor_m"] = {str(k): v for k, v in sympy.factorint(m).items()}
        rec["factor_m2p1"] = {str(k): v for k, v in sympy.factorint(m * m + 1).items()}
    nm.append(rec)
result["near_misses_stage3and4"] = nm
result["near_misses_le_1e9"] = [m for m in S34 if m <= NM_BOUND]
result["stage3_list"] = S3 if len(S3) <= 6000 else (S3[:3000] + ["..."] + S3[-100:])
result["extra_pieces_beyond_gap"] = [{"lo": e["lo"], "reached": e["reached"], "S34": [m for m in e["S"] if pow(2, m, m + 1) == 1], "full": [m for m in e["S"] if pow(2, m, m**4 - 1) == 1]} for e in extra_pieces]
result["sq_solutions"] = {"range_even_m": [2, sq_cov], "odd_m_impossible": "m odd => m^2+1 even, 2^m-1 odd", "list": sq_list, "all_4|m": all(m % 4 == 0 for m in sq_list)}
result["elapsed_s"] = round(time.time() - T0, 2)
ps = result["pipeline_strong_4|m"]
result["summary"] = (f"compiled={exe is not None}; exhaustive over even m in [6,{cov}] (n<= {cov+1}). Strong pipeline counts even/f1/f2/s3/s4/s5 = "
    f"{ps['even']}/{ps['after_filter1']}/{ps['after_filter2']}/{ps['after_stage3']}/{ps['after_stage4']}/{ps['after_stage5']}; final={ps['final']}. "
    f"Unfiltered: stage3={len(S3)}, stage3&4={len(S34)}, all={S345}. Counterexamples={result['counterexamples_P3_reverse']}. "
    f"sieve==brute on [6,{BRUTE_MAX}]: {result.get('validation_sieve_vs_brute',{}).get('identical')}. m^2+1|2^m-1 for m<= {sq_cov}: {sq_list}.")
save()
print(result["summary"])
