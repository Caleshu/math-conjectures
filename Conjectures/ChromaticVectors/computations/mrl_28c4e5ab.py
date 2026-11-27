# MathResearchLab experiment 28c4e5ab-3395-40cf-a56e-1b3e690d68b8
# Certify words against the fixed seven-dimensional residual
# sha256(code) = 398a7b3b1936ac4ecee6c4befb77d46f5b688424e37f3f9d25b8ededf977aa4d
# parameters: {"audit": null, "new_words": [], "budget_seconds": 90}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time

started = time.monotonic()
params = json.load(open(os.environ['MRL_PARAMS']))


def universe():
    def extend(prefix, left, lower):
        slots = 7 - len(prefix)
        if slots == 1:
            if left >= lower:
                yield tuple(prefix + [left])
            return
        for x in range(lower, left // slots + 1, 2):
            if 128 - left + x >= 2 ** (len(prefix) + 1):
                yield from extend(prefix + [x], left - x, x)
    return set(extend([], 128, 2))


def histogram(word, n):
    size = 1 << n
    if not isinstance(word, str) or len(word) != size:
        return None
    counts = [0] * n
    seen = set()
    v = 0
    for digit in word:
        i = ord(digit) - ord('0')
        if not 0 <= i < n or v in seen:
            return None
        seen.add(v)
        counts[i] += 1
        v ^= 1 << i
    return tuple(sorted(counts)) if v == 0 else None


def prism_word():
    # In the cyclic reflected Gray order g of Q_6, g(1) and g(62)
    # differ in bit 5, and g(0) and g(31) differ in bit 4.
    # Traverse the four indicated intervals in order. At each internal
    # vertex switch layers. At an interval endpoint take the given chord.
    def gray(i):
        return i ^ (i >> 1)
    digits = []
    for i, end, chord in [(0, 1, 5), (62, 0, 4), (31, 62, 5), (1, 31, 4)]:
        while i != end:
            j = (i + 1) % 64
            difference = gray(i) ^ gray(j)
            assert difference.bit_count() == 1
            digits.append(str(difference.bit_length() - 1))
            i = j
            if i != end:
                digits.append('6')
        digits.append(str(chord))
    return ''.join(digits)


def solve(target, seconds, seed):
    from ortools.sat.python import cp_model
    n = len(target)
    size = 1 << n
    model = cp_model.CpModel()
    arcs = [[model.new_bool_var(f'a_{v}_{i}') for i in range(n)] for v in range(size)]
    model.add_circuit([(v, v ^ (1 << i), arcs[v][i]) for v in range(size) for i in range(n)])
    for i, count in enumerate(target):
        model.add(sum(row[i] for row in arcs) == count)
    # Translate the tail of a used edge in the most frequent dimension to zero.
    model.add(arcs[0][target.index(max(target))] == 1)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = seed
    solver.parameters.max_time_in_seconds = seconds
    status = solver.solve(model)
    name = solver.status_name(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return name, None
    digits = []
    v = 0
    for _ in range(size):
        i, = [i for i, arc in enumerate(arcs[v]) if solver.value(arc)]
        digits.append(str(i))
        v ^= 1 << i
    word = ''.join(digits)
    assert histogram(word, n) == tuple(sorted(target))
    assert tuple(word.count(str(i)) for i in range(n)) == target
    return name, word


def run():
    assert histogram('0101', 2) == (2, 2)
    assert histogram('0011', 2) is None  # closed, right counts, repeated vertex
    special = prism_word()
    key = histogram(special, 7)
    assert key == (4, 4, 4, 8, 16, 32, 60)
    U = universe()
    out = {'universe_count': len(U), 'prism_candidate': {'target': key, 'word': special}, 'new_certificates': [], 'remaining': None, 'coverage_equal': None, 'solver_runs': []}
    if len(U) != 28456:
        raise ValueError('Independent universe enumeration disagrees with the reported scope')
    audit = params.get('audit')
    if audit is None:
        out['summary'] = 'Fixed audit identities absent. The candidate passed the word check. Residual membership and set equality are undetermined for the reported 69 targets.'
        return out
    kind = audit['kind']
    rows = audit['rows']
    if kind == 'words':
        keys = {histogram(w, 7) for w in rows}
    elif kind in ('covered', 'missing'):
        if any(not isinstance(r, list) or len(r) != 7 or any(type(x) is not int for x in r) for r in rows):
            raise ValueError('Expected sorted integer septuples from the fixed audit')
        keys = {tuple(r) for r in rows}
    else:
        raise ValueError('audit.kind must be words, covered or missing')
    if not keys <= U:
        raise ValueError('Invalid word or out-of-scope histogram in audit input')
    residual = keys if kind == 'missing' else U - keys
    if len(residual) != 69 or len(U - residual) != 28387:
        raise ValueError('Distinct audit identities disagree with E-5eebf3 counts')
    out['audit_input_kind'] = kind
    found = {}
    invalid = []
    for index, word in enumerate(params.get('new_words', [])):
        h = histogram(word, 7)
        if h is None:
            invalid.append(index)
        elif h in residual:
            found.setdefault(h, word)
    out['invalid_new_word_indices'] = invalid
    if key in residual:
        found.setdefault(key, special)

    deadline = started + min(100.0, max(0.0, float(params.get('budget_seconds', 90))))
    todo = sorted(residual - found.keys())
    if todo and time.monotonic() + 2 < deadline:
        status, sanity_word = solve((2, 2), 1.0, 1)
        out['solver_sanity_status'] = status
        if sanity_word is None:
            out['search_issue'] = 'Solver did not recover the square. Search skipped.'
        else:
            attempt = 0
            while todo and time.monotonic() + 1 < deadline:
                retry = []
                for j, target in enumerate(todo):
                    left = deadline - time.monotonic()
                    if left < 1:
                        break
                    seconds = min(5.0, left - 0.5, max(0.2, left / (len(todo) - j) - 0.03))
                    attempt += 1
                    status, word = solve(target, seconds, attempt + 1)
                    out['solver_runs'].append({'target': target, 'status': status})
                    if word is not None:
                        h = histogram(word, 7)
                        assert h == target and h in residual
                        found[h] = word
                    elif status == 'UNKNOWN':
                        retry.append(target)
                    elif status != 'INFEASIBLE':
                        out['search_issue'] = status
                        retry.clear()
                        break
                todo = retry
    # Rebuild the acceptance set from the actual output strings.
    certs = [{'target': t, 'word': found[t]} for t in sorted(found)]
    verified = {histogram(row['word'], 7) for row in certs}
    assert verified == set(found) and verified <= residual
    out.update(new_certificates=certs, remaining=sorted(residual - verified), coverage_equal=(verified == residual))
    out['summary'] = f'{len(verified)} of 69 fixed-residual targets have checked words. {len(residual - verified)} still lack certificates in this run.'
    return out


try:
    result = run()
except (KeyError, ValueError, TypeError, AssertionError) as exc:
    result = {'summary': 'Input validation or an internal check failed.', 'error': type(exc).__name__ + ': ' + str(exc), 'coverage_equal': None}
with open('result.json', 'w') as output:
    json.dump(result, output)
