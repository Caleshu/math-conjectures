# MathResearchLab experiment fe7af131-26d6-4cb1-ba71-be3765d17b44
# Check the empty witness against the imported definition
# sha256(code) = 28be53f1e99be46ad9b617d37a341b7032ed56d08368f40d0dfc449735937715
# parameters: {"lean": "toolchain/bin/lean", "olean_roots": [".lake/build/lib/lean"]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import re
import subprocess
import time
from pathlib import Path

params = json.load(open(os.environ['MRL_PARAMS']))
root = Path.cwd().resolve()
deadline = time.monotonic() + 95
module = 'FormalConjectures.ErdosProblems.«151»'
number = 'Erdos151.cliqueTransversalNumber'
header = 'import ' + module + '\nopen Erdos151 SimpleGraph\nset_option autoImplicit false\nset_option pp.fullNames true\n'
result = {'scope': {'n': 1, 'graph': 'bottom', 'candidate': 'empty'}, 'status': 'NOT_CHECKED'}

def local(path):
    p = (root / path).resolve()
    if not p.is_relative_to(root):
        raise ValueError('All configured paths must be in the working directory')
    return p

def check(source):
    left = deadline - time.monotonic()
    if left < 1:
        raise TimeoutError('Local experiment time budget exhausted')
    run = subprocess.run([str(lean), '--stdin'], input=source, cwd=root, env=env,
                         capture_output=True, text=True, timeout=min(left, 24))
    return run.returncode, run.stdout + run.stderr

def subset_rules():
    # Split a quantified subset using its only membership bit. Lean checks these lemmas too.
    src = ''
    for carrier in ['Set', 'Finset']:
        ty = carrier + ' (Fin 1)'
        c = 'cases' + carrier
        src += f'''private theorem {c} (s : {ty}) : s = ∅ ∨ s = {{0}} := by
  classical
  by_cases h : (0 : Fin 1) ∈ s
  · right
    apply {carrier}.ext
    intro i
    rw [Subsingleton.elim i (0 : Fin 1)]
    simp [h]
  · left
    apply {carrier}.ext
    intro i
    rw [Subsingleton.elim i (0 : Fin 1)]
    simp [h]
private theorem all{carrier} (p : {ty} → Prop) : (∀ s, p s) ↔ p ∅ ∧ p {{0}} := by
  constructor
  · intro h
    exact ⟨h _, h _⟩
  · rintro ⟨he, ho⟩ s
    rcases {c} s with h | h
    · simpa only [h] using he
    · simpa only [h] using ho
private theorem ex{carrier} (p : {ty} → Prop) : (∃ s, p s) ↔ p ∅ ∨ p {{0}} := by
  constructor
  · rintro ⟨s, hs⟩
    rcases {c} s with h | h
    · exact Or.inl (h ▸ hs)
    · exact Or.inr (h ▸ hs)
  · rintro (h | h)
    · exact ⟨∅, h⟩
    · exact ⟨{{0}}, h⟩
'''
    return src

def main():
    global lean, env
    lean = local(params['lean'])
    if not lean.is_file():
        return 'Missing staged Lean executable at ' + params['lean']
    roots = [local(p) for p in params['olean_roots']]
    roots += sorted(local('.lake/packages').glob('*/.lake/build/lib/lean'))
    env = {'HOME': str(root), 'PATH': str(lean.parent),
           'LEAN_PATH': os.pathsep.join(str(local(p)) for p in roots)}
    rc, printed = check(header + '#check Erdos151.erdos_151.variants.cliqueFree_four\n#print ' + number + '\n' +
                        'example : (∅ : Finset (Fin 1)) ≠ {0} := by decide\n')
    result['import_and_sanity_log'] = printed
    if rc:
        return 'The exact import, declaration lookup, or singleton sanity check failed. See import_and_sanity_log.'
    result['sanity_check'] = 'Lean checked that the empty finset differs from the singleton.'
    body = printed.partition(':=')[2]
    names = re.findall(r"[\w']+(?:\.[\w']+)*", body)
    named = list(dict.fromkeys(x for x in names if x.split('.')[-1].lower() in {'iscliquetransversal', 'cliquetransversal'}))
    graph = '(SimpleGraph (Fin 1))'
    src = header + f'''private def atEmpty {{A : Type}} [EmptyCollection A]
    (measure : (A → Prop) → ℕ) (G : {graph}) (p : A → Prop)
    (_ : {number} G = measure p) : Prop := p ∅
'''
    src += f'private def singletonQuestion (G : {graph}) : Prop := by\n  first\n'
    for pred in named:
        for carrier in ['Finset', 'Set']:
            empty = '(∅ : ' + carrier + ' (Fin 1))'
            for args in ['G ' + empty, empty + ' G']:
                src += '  | exact ' + pred + ' ' + args + '\n'
    for carrier, card in [('Finset', 'card'), ('Set', 'ncard')]:
        ty = carrier + ' (Fin 1)'
        for equality in [f's.{card} = k', f'k = s.{card}', f's.{card} ≤ k']:
            for clause in ['p s ∧ ' + equality, equality + ' ∧ p s', '∃ _ : p s, ' + equality]:
                measure = f'(fun (p : {ty} → Prop) => sInf {{k : ℕ | ∃ s : {ty}, {clause}}})'
                src += '  | exact atEmpty ' + measure + ' G _ rfl\n'
        src += f'  | exact atEmpty (fun (p : {ty} → Prop) => sInf ((fun s : {ty} => s.{card}) \'\' {{s | p s}})) G _ rfl\n'
    src += '#print singletonQuestion\n'
    rc, binding = check(src)
    result['predicate_binding_log'] = binding
    if rc:
        return 'The cardinality definition was printed, but its witness predicate could not be bound. Its exact representation is the remaining gap.'
    raw = 'singletonQuestion (⊥ : SimpleGraph (Fin 1))'
    helpers = ['singletonQuestion', 'atEmpty'] + named
    words = re.findall(r"[\w']+(?:\.[\w']+)*", body + '\n' + binding)
    helpers += [w for w in words if 'clique' in w.lower() and w not in {number, 'SimpleGraph', 'singletonQuestion'}]
    helpers += ['SimpleGraph.IsMaxClique', 'SimpleGraph.IsMaximalClique', 'Maximal', 'SimpleGraph.IsClique', 'Set.Pairwise', 'Set.Nonempty', 'Finset.Nonempty']
    tactic = '  first\n  | decide\n  | classical\n'
    for h in dict.fromkeys(helpers):
        tactic += '    all_goals try simp only [' + h + ']\n'
    tactic += '    all_goals simp [allFinset, exFinset, allSet, exSet, Fin.forall_fin_succ, Fin.exists_fin_succ] <;> first | decide | aesop\n'
    result['attempts'] = []
    for verdict, goal in [('QUALIFIES', raw), ('DOES_NOT_QUALIFY', '¬ (' + raw + ')')]:
        proof = 'theorem singletonCertificate : ' + goal + ' := by\n' + tactic
        source = src + subset_rules() + proof + '#print axioms singletonCertificate\n'
        rc, log = check(source)
        result['attempts'].append({'polarity': verdict, 'returncode': rc, 'log': log[-6000:]})
        audit = log.split("'singletonCertificate'", 1)[-1]
        listed = re.search(r'depends on axioms:\s*\[([^\]]*)\]', audit)
        clean = ('does not depend on any axioms' in audit or
                 (listed is not None and set(x.strip() for x in listed[1].split(',')) <= {'propext', 'Classical.choice', 'Quot.sound'}))
        if rc == 0 and clean:
            result.update(status=verdict, lean_source=source, author_support='proved_here',
                          justification='The included Lean source proves this polarity for the displayed predicate binding. The kernel accepted it and the axiom audit passed.')
            return 'Lean checked the singleton certificate: ' + verdict
    return 'The predicate was bound, but neither polarity yielded an accepted certificate with a clean axiom audit. The proof goals and diagnostics are in attempts.'

try:
    result['summary'] = main()
except (OSError, ValueError, TimeoutError, subprocess.TimeoutExpired) as exc:
    result['summary'] = 'No certificate obtained: ' + str(exc)
with open('result.json', 'w') as out:
    json.dump(result, out, ensure_ascii=False)
