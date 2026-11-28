# MathResearchLab experiment 46824c3d-e969-4097-8e52-31ff9a4ce125
# Exact position-specific feasibility for $a=2342512342321$
# sha256(code) = 9093fe33a7d9e83f970d6ad5e417a6a336181c3d54998f4b7dab012760025787
# parameters: {"solver_seconds": 70}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import time
from collections import Counter, defaultdict
from functools import cache
from ortools.sat.python import cp_model

start = time.monotonic()
deadline = start + 95.0
E = (1, 2, 3, 4, 5, 6)

@cache
def length(x):
    return sum(u > v for i, u in enumerate(x) for v in x[i+1:])

@cache
def swap(x, s):
    return x[:s] + (x[s+1], x[s]) + x[s+2:]

def product(a):
    x = E
    for s in a:
        x = swap(x, s)
    return x

@cache
def monomial(y):
    # Coefficients of the product of (1+T_s) in the standard Hecke basis.
    # Use a canonical reduced expression, independent of the mask input word.
    rev = []
    x = y
    while x != E:
        s = next(i for i in range(5) if x[i] > x[i+1])
        rev.append(s)
        x = swap(x, s)
    row = Counter({(E, 0): 1})
    for s in reversed(rev):
        nxt = Counter()
        for (x, k), c in row.items():
            t = swap(x, s)
            j = k + int(length(t) < length(x))
            nxt[x, j] += c
            nxt[t, j] += c
        row = nxt
    return row

def kl_column(w):
    # Triangular bar-invariant elimination, independent of the earlier KL recurrence.
    f = monomial(w).copy()
    domain = {x for x, k in f}
    for x in sorted(domain - {w}, key=length, reverse=True):
        gap = length(w) - length(x)
        for k in range(gap, (gap + 1)//2 - 1, -1):
            c = f[x, k]
            if c:
                shifts = {k, gap-k}
                for (u, j), b in monomial(x).items():
                    for t in shifts:
                        f[u, j+t] -= c*b
    K = {key: c for key, c in f.items() if c}
    assert K.get((w, 0)) == 1 and all(K.get((x, 0)) == 1 for x in domain)
    assert all(c > 0 and ((x == w and k == 0) or 2*k < length(w)-length(x)) for (x, k), c in K.items())
    return K

def masks(a):
    states = [(E, 0)]
    for s in a:
        skip, keep = [], []
        for x, k in states:
            d = k + int(x[s] > x[s+1])
            skip.append((x, d))
            keep.append((swap(x, s), d))
        states = skip + keep
    return states

def labels(m, L):
    return tuple(8*j + ((m >> j) & 7) for j in range(L-2))

def decode(i):
    j, p = divmod(i, 8)
    return {'start_one_based': j+1, 'bits_left_to_right': ''.join(str((p >> t) & 1) for t in range(3))}

def ids(sig):
    while sig:
        bit = sig & -sig
        yield bit.bit_length()-1
        sig -= bit

def decide(a, K, seconds, singleton_first):
    L = len(a)
    assert length(product(a)) == L and L >= 3
    rows = masks(a)
    windows = [labels(m, L) for m in range(len(rows))]
    zero = [m for m, (_, k) in enumerate(rows) if k == 0]
    assert Counter(rows[m] for m in zero) == {g: c for g, c in K.items() if g[1] == 0}
    assert all(K[rows[m]] == 1 for m in zero)
    forced = {i for m in zero for i in windows[m]}
    free = sorted(set(range(8*(L-2))) - forced)
    groups = defaultdict(Counter)
    for g, win in zip(rows, windows):
        if g[1]:
            sig = sum(1 << i for i in win if i not in forced)
            groups[g][sig] += 1
    keys = sorted(set(groups) | {g for g in K if g[1]})
    out = {'word': ''.join(str(s+1) for s in a), 'word_product': product(a), 'mask_count': len(rows), 'forced_defect_zero_mask_count': len(zero), 'forced_allowed_label_ids': sorted(forced), 'free_label_ids': free, 'id_convention': 'An ID is 8*j+p, with zero-based window start j. Bit t of p is the keep bit at j+t, t=0,1,2.'}

    def core_row(g):
        return {'product': g[0], 'defect': g[1], 'required': K.get(g, 0), 'terms': [{'free_label_ids': list(ids(sig)), 'multiplicity': n} for sig, n in sorted(groups[g].items())]}

    if singleton_first:
        favorite = ((1, 3, 4, 2, 5, 6), 1)
        for g in sorted(keys, key=lambda g: g != favorite):
            need = K.get(g, 0)
            terms = groups[g]
            reason = None
            if terms[0] > need:
                reason = 'The empty signature alone exceeds the required count.'
            elif sum(terms.values()) < need:
                reason = 'Even allowing every label gives too few masks.'
            elif need == 1:
                # If exactly one mask can survive, allow just its signature.
                # All signatures contained in that signature still survive.
                possible = any(n == 1 and not any(t != s and (t & s) == t for t in terms) for s, n in terms.items())
                if not possible:
                    reason = 'No inclusion-minimal signature has multiplicity one.'
            if reason:
                out.update(decision='UNSAT', method='exact one-class test', core=[core_row(g)], core_reason=reason)
                return out

    model = cp_model.CpModel()
    ban = {i: model.new_bool_var('ban_' + str(i)) for i in free}
    alive = {0: 1}
    guards = {}
    for g in keys:
        terms = groups[g]
        for s in terms:
            if s in alive:
                continue
            v = model.new_bool_var('survive_' + str(s))
            bs = [ban[i] for i in ids(s)]
            model.add_bool_or([v] + bs)
            for b in bs:
                model.add_implication(v, b.Not())
            alive[s] = v
        guard = model.new_bool_var('class_' + str(len(guards)))
        model.add(sum(n*alive[s] for s, n in terms.items()) == K.get(g, 0)).only_enforce_if(guard)
        model.add_assumption(guard)
        guards[guard.Index()] = g
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 1
    solver.parameters.max_time_in_seconds = max(0.001, min(seconds, deadline - time.monotonic()))
    status = solver.solve(model)
    out.update(solver_status=solver.status_name(status), method='joint class constraints')
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        chosen = {i for i in free if solver.value(ban[i])}
        # Replay individual masks using actual positions and triples, without signatures or solver variables.
        by_start = {j: {i % 8 for i in chosen if i//8 == j} for j in range(L-2)}
        survivors = [m for m in range(1 << L) if all(((m >> j) & 7) not in pats for j, pats in by_start.items())]
        counts = Counter(rows[m] for m in survivors)
        assert counts == K
        out.update(decision='SAT', forbidden_windows=[decode(i) for i in sorted(chosen)], survivor_count=len(survivors), replay_matches_entire_KL_column=True)
    elif status == cp_model.INFEASIBLE:
        core = [guards[i] for i in solver.sufficient_assumptions_for_infeasibility()]
        assert core
        out.update(decision='UNSAT', core=[core_row(g) for g in core], core_reason='These class equations are jointly infeasible relative to the forced allowed labels. Each term contributes its multiplicity exactly when every listed free label is allowed.')
    else:
        assert status == cp_model.UNKNOWN
        out.update(decision='undecided', remaining_gap='The joint solver did not decide feasibility within its time allowance.')
    return out

# Sanity checks exercise a nonconstant KL polynomial and the complete SAT/replay path.
small = kl_column((3, 4, 1, 2, 5, 6))
assert {k: c for (x, k), c in small.items() if x == E} == {0: 1, 1: 1}
toy = (0, 1, 0)
toy_K = kl_column(product(toy))
assert len(toy_K) == 6 and all(k == 0 and c == 1 for (x, k), c in toy_K.items())
san = decide(toy, toy_K, 3.0, False)
assert san['decision'] == 'SAT' and san['survivor_count'] == 6

a = tuple(int(c)-1 for c in '2342512342321')
w = (6, 4, 5, 3, 1, 2)
assert product(a) == w and length(w) == 13
K = kl_column(w)
out = decide(a, K, float(params.get('solver_seconds', 70)), True)
out['sanity_solver_status'] = san['solver_status']
out['KL_column_sums_by_degree'] = [sum(c for (x, d), c in K.items() if d == k) for k in range(1 + max(d for x, d in K))]
out['summary'] = {'SAT': 'A position-specific forbidden list exists for this word. Its replay matches every coefficient.', 'UNSAT': 'No position-specific forbidden list of width at most three exists for this word. The core is relative to the displayed forced allowed labels.', 'undecided': 'The position-specific decision remains open after the bounded solve.'}[out['decision']]
out['author_support'] = 'proved_here' if out['decision'] != 'undecided' else 'speculative'
out['justification'] = ('For the KL target, let B_y be the product of the factors 1+T_s along a reduced expression for y, in the Hecke convention T_s^2=(q-1)T_s+q. Right multiplication by 1+T_s contributes to both endpoints with weight 1 on an ascent and q on a descent, as implemented by monomial. The leading term is T_y and all other terms are strictly lower in Bruhat order by the subword property. The normalized product q^(-length(y)/2)B_y is bar-invariant because each normalized factor is. Starting at B_w, a subtraction at x with gap g preserves normalized bar invariance because the coefficient multiplier h satisfies h(q)=q^g h(1/q). It cancels degree k at x and changes only strictly lower endpoints besides x. The companion degree g-k is below the cutoff whenever it differs from k. Each monomial coefficient at u has degree at most length(y)-length(u): each descent contributes one to the degree and costs at least one unit of length relative to taking an ascent at every step. This bound persists under each shift. Descending elimination therefore gives the unique normalized bar-invariant KL element with leading coefficient one and the strict KL degree bounds. For the mask test, binary branching lists every mask once and counts each pre-step descent. All degree-zero masks must survive by the checked endpoint multiplicities. Consequently their labels must be allowed. Every shorter position-specific ban can be replaced by all matching extensions at a fixed triple containing its position. A mask survives precisely when every free label in its signature is allowed. Grouping equal signatures preserves multiplicities. For a single class requiring one survivor, allowing just the signature of that survivor retains exactly one if any assignment does. This is equivalent to an inclusion-minimal signature of multiplicity one. For the joint test each survival variable is equivalent in both directions to the absence of any ban in the signature, and each assumption guards exactly one required class count. Thus an infeasible assumption core suffices, and a feasible assignment is checked by direct replay.')
out['scope'] = 'Only a=2342512342321 in S_6, with separate bans at each position. An UNSAT result leaves the other words outside this check. A SAT result refutes the no-word assertion for this w.'
with open('result.json', 'w') as f:
    json.dump(out, f)
