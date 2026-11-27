# MathResearchLab experiment c11752fd-8e35-4d35-b6f0-4f071fb64218
# Extract and certify the empty candidate on the singleton graph
# sha256(code) = 9bc9d3cee43ecd49a6ee557134eb05edd1b34e773139d625b43c81638954ded7
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

params = json.load(open(os.environ['MRL_PARAMS']))
root = Path.cwd().resolve()
result = {'scope': {'n': 1, 'graph': 'bottom', 'candidate': 'empty'}, 'status': 'UNRESOLVED'}

def local(path):
    path = (root / path).resolve()
    if not path.is_relative_to(root):
        raise ValueError('A staged input must be inside the working directory')
    return path

header = '''import FormalConjectures.ErdosProblems.«151»
open Lean Meta Elab Term
open Erdos151 SimpleGraph
namespace Singleton151Probe
abbrev V := Fin 1
'''

# These are alternative representations of the cardinality index. P is an
# unknown metavariable in every match. None of the patterns defines eligibility.
shapes = []
domains = [('Finset V', 's.card', 'Finset.univ'), ('Set V', 's.ncard', 'Set.univ')]
for d, (typ, card, full) in enumerate(domains):
    for equality in [card + ' = k', 'k = ' + card]:
        for body in [equality + ' ∧ P s', 'P s ∧ ' + equality, '∃ _ : P s, ' + equality]:
            shapes.append((d, '{k | ∃ s : ' + typ + ', ' + body + '}'))
    shapes.append((d, '(fun s : ' + typ + ' => ' + card + ') '' {s | P s}'))
# Build the image expression with Lean's image operator (two literal apostrophes).
for i, (d, shape) in enumerate(shapes):
    if shape.startswith('(fun'):
        typ, card, _ = domains[d]
        shapes[i] = (d, f"(fun s : {typ} => {card}) '' {{s | P s}}")

def lean_program(extra_names):
    parts = [header]
    for i, (d, shape) in enumerate(shapes):
        typ = domains[d][0]
        parts.append(f'def shape{i} (P : {typ} → Prop) : Set ℕ := {shape}\n')
    names = ', '.join('``shape' + str(i) for i in range(len(shapes)))
    parts.append('''
elab "importedSingletonQ" : term => do
  let lhs ← elabTerm (← `(cliqueTransversalNumber (⊥ : SimpleGraph (Fin 1)))) (some (mkConst ``Nat))
  synthesizeSyntheticMVarsNoPostponing
  let lhs ← instantiateMVars lhs
  let .const nm levels := lhs.getAppFn | throwError "unexpected transversal-number head: {lhs}"
  let .defnInfo info ← getConstInfo nm | throwError "no definition body for {nm}"
  let body := (mkAppN (info.value.instantiateLevelParams info.levelParams levels) lhs.getAppArgs).headBeta
  logInfo m!"IMPORTED_BODY {nm} = {body}"
  unless body.isAppOf ``sInf do throwError "unrecognized outer operation: {body}"
  let spectrum := body.getAppArgs.back!
  for shape in #[SHAPES] do
    let fn := mkConst shape
    let .forallE _ predType _ _ ← inferType fn | throwError "invalid matcher"
    let pred ← mkFreshExprMVar (some predType)
    if ← withTransparency .all (isDefEq spectrum (mkApp fn pred)) then
      let pred ← instantiateMVars pred
      if !pred.hasMVar then
        let .forallE _ domain _ _ ← whnf predType | throwError "invalid predicate type"
        let emptySet ← elabTerm (← `(∅)) (some domain)
        synthesizeSyntheticMVarsNoPostponing
        let q ← instantiateMVars ((mkApp pred emptySet).headBeta)
        if !q.hasMVar then
          logInfo m!"MATCH {shape}\\nIMPORTED_P {pred}\\nSPECIALIZED_Q {q}"
          return q
  throwError "no cardinality-index match for {spectrum}"

def Q : Prop := importedSingletonQ
'''.replace('SHAPES', names))
    # Prove the exhaustive case split for each supported vertex-set type.
    for d, (typ, _, full) in enumerate(domains):
        parts.append(f'''
private theorem cases{d} (s : {typ}) : s = ∅ ∨ s = {full} := by
  by_cases h : (0 : V) ∈ s
  · right
    ext i
    have hi : i = 0 := Subsingleton.elim _ _
    simp [hi, h]
  · left
    ext i
    have hi : i = 0 := Subsingleton.elim _ _
    simp [hi, h]
private theorem all{d} (p : {typ} → Prop) : (∀ s, p s) ↔ p ∅ ∧ p {full} := by
  constructor
  · intro h
    exact ⟨h _, h _⟩
  · intro h s
    rcases cases{d} s with h0 | h1
    · exact h0 ▸ h.1
    · exact h1 ▸ h.2
private theorem ex{d} (p : {typ} → Prop) : (∃ s, p s) ↔ p ∅ ∨ p {full} := by
  constructor
  · rintro ⟨s, hs⟩
    rcases cases{d} s with h0 | h1
    · exact Or.inl (h0 ▸ hs)
    · exact Or.inr (h1 ▸ hs)
  · rintro (h | h)
    · exact ⟨_, h⟩
    · exact ⟨_, h⟩
''')
    parts.append('attribute [local simp] all0 ex0 all1 ex1\n')
    parts.append('''-- Positive and negative controls use the same singleton universe.
example : ∀ s : Finset V, s = ∅ ∨ s = Finset.univ := cases0
example : ¬ (∀ s : Finset V, s = ∅) := by
  intro h
  have bad := h {0}
  simpa using bad
''')
    unfold_names = ['Q'] + extra_names + ['IsCliqueTransversal', 'IsMaximalClique', 'IsMaxClique', 'SimpleGraph.IsMaximalClique', 'SimpleGraph.IsMaxClique', 'Maximal', 'SimpleGraph.IsClique', 'Set.Pairwise', 'Set.Nonempty', 'Finset.Nonempty']
    # An unknown helper name is harmless inside `try`. The final `done`
    # forces complete closure before `first` commits to a constructor.
    proof = ['first', '| decide', '| classical']
    proof += ['  all_goals try simp only [' + name + ']' for name in dict.fromkeys(unfold_names)]
    proof += ['  all_goals simp_all', '  all_goals first | decide | aesop', '  done']
    parts.append('def verdict : Decidable Q := by\n  first\n')
    for constructor in ['isTrue', 'isFalse']:
        parts.append('  | exact ' + constructor + ' (by\n' + '\n'.join('      ' + line for line in proof) + ')\n')
    parts.append('''
#print Q
#print verdict
#print axioms verdict
run_cmd
  let .defnInfo info ← getConstInfo ``verdict | throwError "missing declaration"
  let ctor := info.value.getAppFn.constName!
  unless ctor == ``Decidable.isTrue || ctor == ``Decidable.isFalse do
    throwError "unexpected stored body: {info.value}"
  logInfo m!"STORED_CONSTRUCTOR {ctor}"
end Singleton151Probe
''')
    return ''.join(parts)

try:
    # The optional source excerpt provides evidence even if only source was staged.
    sources = [local(params['source'])] if params.get('source') else [p for p in root.rglob('151.lean') if p.parent.name == 'ErdosProblems']
    extra = []
    if sources:
        src = local(sources[0]).read_text()
        hit = re.search(r'(?m)^.*?\bdef\s+cliqueTransversalNumber\b', src)
        if hit:
            result['staged_source_excerpt'] = src[hit.start():hit.start()+2400]
            # Unfold local definitions nearest the target first.
            extra = list(reversed(re.findall(r'\bdef\s+([A-Za-z_][A-Za-z0-9_\']*)', src[:hit.start()])))[:12]
    supplied = params.get('lean')
    binaries = [local(supplied)] if supplied else [p for p in root.rglob('lean') if p.parent.name == 'bin' and p.is_file()]
    if not binaries:
        raise FileNotFoundError('Lean executable was not staged')
    lean = local(binaries[0])
    paths = [local(p) for p in params.get('lean_path', [])]
    if not paths:
        paths = [local(p) for p in root.rglob('lean') if p.is_dir() and p.parent.name == 'lib']
        for p in root.rglob('151.olean'):
            if p.parent.name == 'ErdosProblems' and p.parent.parent.name == 'FormalConjectures':
                paths.append(local(p.parents[2]))
    env = {'LEAN_PATH': os.pathsep.join(str(p) for p in dict.fromkeys(paths))}
    with TemporaryDirectory(dir=root) as work:
        script = Path(work) / 'Singleton151.lean'
        script.write_text(lean_program(extra))
        proc = subprocess.run([str(lean), str(script)], cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=85)
        log = proc.stdout
        result.update(exit_code=proc.returncode, lean_output=log, submitted_lean=script.read_text())
        marker = re.search(r'STORED_CONSTRUCTOR Decidable\.(isTrue|isFalse)\b', log)
        if proc.returncode == 0 and marker and 'sorryAx' not in log and 'uses \'sorry\'' not in log:
            result.update(status='KERNEL_ACCEPTED', constructor=marker.group(1))
except subprocess.TimeoutExpired as error:
    partial = error.stdout or b''
    result.update(blocker='Lean exceeded the 85-second probe budget', partial_output=partial.decode(errors='replace') if isinstance(partial, bytes) else partial)
except (OSError, ValueError) as error:
    result['blocker'] = str(error)
result['summary'] = ('Lean accepted the singleton declaration with constructor ' + result['constructor']) if result['status'] == 'KERNEL_ACCEPTED' else 'No certified polarity. Inspect the blocker, imported body, or Lean diagnostic.'
Path('result.json').write_text(json.dumps(result, ensure_ascii=False))