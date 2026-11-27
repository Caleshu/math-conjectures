# MathResearchLab experiment 92a7b722-80cd-4b2a-8750-d06ac2e9c5a0
# Equi-independence number alpha_=(Q_m) for m<=7 and the implied counting bound
# sha256(code) = 05b78f3ec0fff5f8e96abf8e5071d50e9d8edb5b0df987d58177c77f760478d7
# parameters: {"m_list": [1, 2, 3, 4, 5, 6, 7], "tl_small": 15.0, "tl_big": 60.0}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from ortools.sat.python import cp_model
params = json.load(open(os.environ['MRL_PARAMS']))
m_list = params.get('m_list', [1,2,3,4,5,6,7])
tl_small = params.get('tl_small', 15.0)
tl_big = params.get('tl_big', 60.0)
T0 = time.time()

def popc(x): return bin(x).count('1')

def nbrs(m, v): return [v ^ (1 << i) for i in range(m)]

def verify(m, S):
    S = set(S)
    indep = all((u not in S) for v in S for u in nbrs(m, v))
    ev = sum(1 for v in S if popc(v) % 2 == 0)
    od = len(S) - ev
    return indep and ev == od

def brute(m):
    N = 1 << m
    nm = [sum(1 << u for u in nbrs(m, v)) for v in range(N)]
    par = [popc(v) % 2 for v in range(N)]
    best = 0; wit = 0
    for S in range(1 << N):
        c = popc(S)
        if c <= best or c % 2: continue
        ok = True; ev = 0; x = S
        while x:
            low = x & -x; v = low.bit_length() - 1; x ^= low
            if nm[v] & S: ok = False; break
            if par[v] == 0: ev += 1
        if ok and 2 * ev == c:
            best = c; wit = S
    return best, [v for v in range(N) if wit >> v & 1]

def cpsat(m, tl, fix0=True):
    N = 1 << m
    mdl = cp_model.CpModel()
    x = [mdl.NewBoolVar(f'x{v}') for v in range(N)]
    for v in range(N):
        for i in range(m):
            u = v ^ (1 << i)
            if u > v: mdl.Add(x[u] + x[v] <= 1)
    ev = [x[v] for v in range(N) if popc(v) % 2 == 0]
    od = [x[v] for v in range(N) if popc(v) % 2 == 1]
    mdl.Add(sum(ev) == sum(od))
    if fix0:
        # WLOG 0 in S: translations preserve adjacency and map balanced sets to balanced sets.
        mdl.Add(x[0] == 1)
    mdl.Maximize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_workers = 8
    st = s.Solve(mdl)
    res = {'status': s.StatusName(st), 'wall': round(s.WallTime(), 2)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        S = [v for v in range(N) if s.Value(x[v])]
        res.update(objective=len(S), bound=int(s.BestObjectiveBound()), witness=S, witness_valid=verify(m, S))
    else:
        res.update(objective=None, bound=None)
    return res

out = {'per_m': {}}
for m in m_list:
    rem = 115 - (time.time() - T0)
    if rem < 3:
        out['per_m'][m] = {'status': 'SKIPPED_TIME'}; continue
    tl = min(tl_small if m <= 6 else tl_big, rem - 2)
    r = {}
    # fix0 is valid only if the optimum is > 0; for m<=2 run without it.
    r['cpsat'] = cpsat(m, tl, fix0=(m >= 3))
    if m <= 4:
        b, w = brute(m)
        r['brute'] = b; r['brute_witness_valid'] = verify(m, w) if b > 0 else True
        r['agree'] = (r['cpsat'].get('objective') == b) and r['cpsat']['status'] == 'OPTIMAL'
    out['per_m'][m] = r

# implied counting bound
bound_tab = {}
for m, r in out['per_m'].items():
    c = r.get('cpsat', {})
    if c.get('status') == 'OPTIMAL':
        a = c['objective']; n = m + 1
        bound_tab[n] = {'alpha_eq_Q_{n-1}': a, '2^n': 2 ** n, 'n*alpha': n * a, 'counting_rules_out_squarefree': 2 ** n > n * a}
    elif c.get('objective') is not None:
        n = m + 1
        bound_tab[n] = {'alpha_lower': c['objective'], 'alpha_upper': c['bound'], '2^n': 2 ** n,
                        'rules_out_if_upper': 2 ** n > n * c['bound'], 'fails_if_lower': 2 ** n <= n * c['objective']}
out['counting_bound'] = bound_tab
# compact summary
parts = []
for m, r in out['per_m'].items():
    c = r.get('cpsat', {})
    parts.append(f"m={m}: {c.get('status')} obj={c.get('objective')} bound={c.get('bound')}" + (f" brute={r['brute']}" if 'brute' in r else ''))
out['summary'] = 'alpha_=(Q_m): ' + '; '.join(parts) + ' | counting bound 2^n>n*alpha_=(Q_{n-1}): ' + json.dumps({n: v.get('counting_rules_out_squarefree', v.get('rules_out_if_upper')) for n, v in bound_tab.items()})
out['total_time'] = round(time.time() - T0, 1)
json.dump(out, open('result.json', 'w'), indent=1)
