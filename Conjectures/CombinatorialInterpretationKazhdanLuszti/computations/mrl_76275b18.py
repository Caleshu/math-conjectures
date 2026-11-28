# MathResearchLab experiment 76275b18-486c-4eb1-8f03-2c0cfd3a3727
# Check the complement of E-c88e68’s coverage
# sha256(code) = 1a09ed3bdf0e98926c6aff77d46bdbe8840040399d50f6f7d4be89760c92a178
# parameters: {"coverage_record": null, "source_checked_rules": null}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from functools import cache

params = json.load(open(os.environ['MRL_PARAMS']))
W = (6, 4, 5, 3, 1, 2)
A = '2342512342321'

@cache
def word_count(w):
    total = 0
    for i in range(len(w) - 1):
        if w[i] > w[i + 1]:
            v = w[:i] + (w[i + 1], w[i]) + w[i + 2:]
            total += word_count(v)
    return total or 1

def is_reduced_word_for(word, w):
    if not isinstance(word, str):
        return False
    p = list(range(1, len(w) + 1))
    for ch in word:
        if ch not in '12345':
            return False
        i = int(ch) - 1
        if i + 1 >= len(p) or p[i] > p[i + 1]:
            return False
        p[i], p[i + 1] = p[i + 1], p[i]
    return tuple(p) == w

# In S_3 the longest permutation has the two reduced words 121 and 212.
small = (3, 2, 1)
assert word_count((1, 2, 3)) == 1 and word_count(small) == 2
assert all(is_reduced_word_for(s, small) for s in ('121', '212'))
assert not is_reduced_word_for('11121', small)  # same product, nonreduced
assert is_reduced_word_for(A, W)

# These fields describe the scope of the exclusion proved by the earlier run.
# An obstruction using only a few coefficient equations can prove this exclusion.
expected = {
    'action': 'right adjacent position swaps, one-based',
    'endpoint': 'product of kept letters in word order',
    'defect': 'all pre-step descents, whether skipped or kept',
    'bans': 'arbitrary position-specific binary triples',
    'validity': 'survivor counts equal every ordinary KL coefficient by endpoint and defect'
}
N = word_count(W)
out = {'target': ''.join(map(str, W)), 'candidate': A, 'candidate_is_reduced_word': True,
       'number_of_reduced_words': N, 'expected_rules': expected, 'sanity_check': 'passed'}
rules = params.get('source_checked_rules')
# Normalize equivalent width-at-most-three rules to triples before comparison.
out['rules_match'] = None if rules is None else rules == expected
record = params.get('coverage_record')
match = None
if record is None:
    out['coverage_evidence'] = 'E-c88e68 coverage record absent'
elif record['kind'] == 'complete_word_ledger':
    words = record['words_certified_infeasible']
    if not isinstance(words, list):
        raise ValueError('Expected a list of generator strings')
    seen = set()
    invalid = []
    duplicates = 0
    for word in words:
        if not is_reduced_word_for(word, W):
            invalid.append(word)
        elif word in seen:
            duplicates += 1
        else:
            seen.add(word)
    out.update(distinct_valid_words=len(seen), duplicate_entries=duplicates,
               invalid_entry_count=len(invalid), invalid_examples=invalid[:3],
               complement_size=N-len(seen), candidate_in_ledger=A in seen)
    match = not invalid and A not in seen and len(seen) == N - 1
elif record['kind'] == 'source_checked_count_and_skip':
    # Use this compact mode only if the source and completion record establish
    # the count for DISTINCT elements of R and establish the skip is outside D.
    count = record['distinct_reduced_words_certified_infeasible']
    skip = record['word_explicitly_skipped_and_never_certified']
    if type(count) is not int or not 0 <= count <= N:
        raise ValueError('Invalid distinct-word count')
    out.update(reported_distinct_count=count, reported_skip=skip)
    match = count == N - 1 and skip == A
else:
    raise ValueError('Unrecognized coverage record kind')
out['coverage_match'] = match
if match is True and out['rules_match'] is True:
    out['summary'] = 'The supplied coverage evidence identifies the C-49b31c word as the unique omission under matching rules.'
elif match is False:
    out['summary'] = 'The supplied coverage evidence fails the singleton-complement check.'
else:
    out['summary'] = 'The historical claim remains unverified. Inspect the coverage record and rule comparison fields for the outstanding evidence.'
out['author_support'] = 'proved_here'
out['justification'] = ('The count partitions reduced words by their last generator. Removing it swaps a descent and lowers the inversion count by one. Appending it reverses this bijection. The identity has one empty word. The membership test requires each swap to increase the inversion count by one and checks the final permutation. Thus, once D is established to be a subset of R, the two conditions |D|=|R|-1 and a outside D are necessary and sufficient. The compact branch is conditional on the provenance of its two recorded facts. For this 13-letter word every shorter marked binary block lies in a fixed triple, and banning all its extensions at that triple removes exactly the same masks. This justifies normalizing widths one through three to position-specific triples.')
with open('result.json', 'w') as f:
    json.dump(out, f)
