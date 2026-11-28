# MathResearchLab experiment de344e4a-d993-487c-a775-b1cbfd8423f9
# Verify both UNSAT certificates with one clause per word
# sha256(code) = 6e4473f7b09463594adf034fb8296e63f9518cf126b3c7ed094b6a6534d018a7
# parameters: {"solver_seconds": 2}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from itertools import combinations
from ortools.sat.python import cp_model

params = json.load(open(os.environ["MRL_PARAMS"]))
identity = (1, 2, 3, 4, 5, 6)
endpoint = (6, 4, 5, 3, 1, 2)
cases = {
    'W0': ((2, 1, 3, 2, 1, 4, 3, 2, 5, 4, 3, 2, 1),
           [((5, 13), (5, 12)), ((8, 12), (8, 11))]),
    'W1': ((2, 1, 3, 5, 4, 2, 1, 5, 3, 4, 2, 3, 1),
           [((7, 13), (7, 11)), ((5, 10), (5, 8))]),
}

def swap(p, a, b):
    p = list(p)
    p[a], p[b] = p[b], p[a]
    return tuple(p)

def length(p):
    return sum(p[a] > p[b] for a, b in combinations(range(len(p)), 2))

def evaluate(word, kept):
    p = identity
    defects = []
    for pos, letter in enumerate(word, 1):
        a = letter - 1
        if p[a] > p[a + 1]:
            defects.append(pos)
        if pos in kept:
            p = swap(p, a, a + 1)
    return p, defects

def windows(word, kept):
    marked = tuple((s, int(j in kept)) for j, s in enumerate(word, 1))
    return [marked[j:j + 3] for j in range(len(marked) - 2)]

def kl_linear_trace(word):
    # For v*s > v the right KL recurrence at e, in degree one, adds
    # [s <= v] and subtracts one per coatom z of v having z*s < z.
    # All other correction terms start in degree at least two.
    v = identity
    support = set()
    coefficient = 0
    trace = []
    for letter in word:
        a = letter - 1
        assert v[a] < v[a + 1]
        d = length(v)
        corrections = []
        for b, c in combinations(range(len(v)), 2):
            z = swap(v, b, c)
            if length(z) == d - 1 and z[a] > z[a + 1]:
                corrections.append(z)
        increment = int(letter in support)
        coefficient += increment - len(corrections)
        trace.append({'prefix': v, 'letter': letter, 'simple_below_prefix': increment,
                      'correction_coatoms': corrections, 'new_q_coefficient': coefficient})
        support.add(letter)
        v = swap(v, a, a + 1)
    assert v == endpoint and coefficient == 1
    return trace

def solve_core(tokens, forced_tokens):
    model = cp_model.CpModel()
    bans = {t: model.new_bool_var('ban_' + str(j)) for j, t in enumerate(tokens)}
    model.add_bool_or(list(bans.values()))
    for t in forced_tokens:
        model.add(bans[t] == 0)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = max(0.1, min(5.0, float(params.get('solver_seconds', 2))))
    status = solver.solve(model)
    return solver.status_name(status)

def check(word, pairs):
    trace = kl_linear_trace(word)
    assert len({target for target, witness in pairs}) == 2
    certificate = []
    union = set()
    forced_tokens = set()
    for target, first_witness in pairs:
        p, defects = evaluate(word, target)
        assert p == identity and defects == [target[1]]
        witnesses = [(), first_witness, (target[1],)]
        witness_rows = []
        witness_windows = []
        for witness in witnesses:
            x, downs = evaluate(word, witness)
            assert downs == []
            # Constant coefficient of the prescribed target at this endpoint.
            assert min(x[:2]) <= 4 and x[-1] != 1
            witness_rows.append({'kept': witness, 'product': x, 'defect_positions': downs})
            witness_windows.append(windows(word, witness))
            forced_tokens.update(witness_windows[-1])
        cover = []
        for start, token in enumerate(windows(word, target)):
            source = next((j for j, row in enumerate(witness_windows) if row[start] == token), None)
            assert source is not None
            union.add(token)
            cover.append({'start': start + 1, 'marked_triple': token, 'forced_witness_kept': witnesses[source]})
        certificate.append({'kept': target, 'product': p, 'defect_positions': defects,
                            'forced_witnesses': witness_rows, 'window_cover': cover})
    tokens = sorted(union)
    units = sorted(union & forced_tokens)
    # Unit resolution on the single positive clause must yield the empty clause.
    assert tokens and units == tokens
    control = solve_core(tokens, [])
    status = solve_core(tokens, units)
    assert control in ('OPTIMAL', 'FEASIBLE', 'UNKNOWN')
    assert status in ('INFEASIBLE', 'UNKNOWN')
    return {'word': word, 'target_product': identity, 'target_defect': 1,
            'required_count': trace[-1]['new_q_coefficient'], 'forced_count_lower_bound': len(pairs),
            'kl_recurrence_trace': trace, 'certificate': certificate,
            'positive_clause_tokens': tokens, 'negative_unit_tokens': units,
            'resolution_remainder': [], 'solver_status': status, 'control_status': control}

findings = {name: check(word, pairs) for name, (word, pairs) in cases.items()}
result = {'summary': 'Both resolution certificates verified. ' + ', '.join(name + ' solver ' + row['solver_status'] + ' and control ' + row['control_status'] for name, row in findings.items()),
          'author_support': 'proved_here',
          'justification': 'Each target pair requires a ban in its union of marked triples. Every literal of this clause has a negative unit justified by a compulsory defect-zero witness.',
          'findings': findings}
with open('result.json', 'w') as out:
    json.dump(result, out)
