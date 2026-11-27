# MathResearchLab experiment 1173f0eb-9cf2-444c-997d-d3ebff4baaea
# Extract the candidate before specializing to the singleton graph
# sha256(code) = ddd7e657271bb35755fd4577e22b4240ddb6ab3a3f09e8c871f16a4e5c7f479a
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from pathlib import Path
import re
import subprocess
import time

params = json.load(open(os.environ['MRL_PARAMS']))
root = Path.cwd()
start = time.monotonic()
module = Path('FormalConjectures/ErdosProblems/151')
source = None
artifact = None
executables = []
roots = set()
out = {'scope': {'n': 1, 'graph': 'bottom', 'candidate': 'empty'}, 'status': 'UNCHECKED'}

def local(path):
    return path.resolve().is_relative_to(root)

# Preserve source evidence independently of whether a compiler is staged.
for folder, dirs, files in os.walk(root):
    base = Path(folder)
    dirs[:] = [d for d in dirs if d != '.git' and not (base / d).is_symlink()]
    if time.monotonic() - start > 12:
        out['discovery_truncated'] = True
        break
    if base.parts[-2:] == ('lib', 'lean'):
        roots.add(base)
    if 'lean' in files and base.name == 'bin' and local(base / 'lean') and os.access(base / 'lean', os.X_OK):
        executables.append(base / 'lean')
    if base.parts[-2:] == tuple(module.parent.parts):
        for suffix in ['.lean', '.olean']:
            p = base / ('151' + suffix)
            if p.name in files and local(p):
                if suffix == '.lean':
                    source = p
                else:
                    artifact = p
                    roots.add(base.parent.parent)

source_text = source.read_text() if source else ''
if source:
    out['source_path'] = str(source.relative_to(root))
    match = re.search(r'(?m)^.*\b(?:def|abbrev)\s+(?:[\w.]+\.)?cliqueTransversalNumber\b', source_text)
    if match:
        out['definition_excerpt'] = source_text[match.start():match.start() + 2200]
    else:
        out['source_occurrences'] = [line for line in source_text.splitlines() if 'cliqueTransversalNumber' in line][:12]

lean = min(executables, key=lambda p: (len(p.parts), str(p)), default=None)
if not lean or not artifact:
    out['missing'] = [name for name, found in [('staged Lean executable', lean), ('imported 151.olean', artifact)] if not found]
    out['summary'] = 'Kernel check unavailable. Any source excerpt is raw evidence only.'
else:
    lines = ['import FormalConjectures.ErdosProblems.«151»', 'open SimpleGraph Erdos151', '#print cliqueTransversalNumber', 'namespace Singleton151Probe', 'set_option maxHeartbeats 250000', 'set_option autoImplicit false']
    names = []
    # P is an implicit argument inferred by matching the entire minimization.
    # In particular P cannot capture the bound cardinality variable k.
    for domain, measure in [('Finset', 's.card'), ('Set', 's.ncard')]:
        for relation in [measure + ' = k', 'k = ' + measure, measure + ' ≤ k']:
            for conjuncts in ['P s ∧ (' + relation + ')', '(' + relation + ') ∧ P s']:
                name = 'extract' + str(len(names))
                names.append(name)
                lines.extend([f'private def {name} {{n : ℕ}} (G : SimpleGraph (Fin n))', f'    {{P : {domain} (Fin n) → Prop}}', f'    (_ : cliqueTransversalNumber G = sInf {{k : ℕ | ∃ s : {domain} (Fin n), {conjuncts}}}) : Prop := P ∅'])
    lines.extend(['def emptyQualifies {n : ℕ} (G : SimpleGraph (Fin n)) : Prop := by', '  first'])
    lines.extend('  | exact ' + name + ' G rfl' for name in names)
    lines.extend(['def Q : Prop := emptyQualifies (⊥ : SimpleGraph (Fin 1))', 'set_option pp.explicit true in', '#print emptyQualifies', 'example : Q ↔ Q := by', '  dsimp only [Q, emptyQualifies, ' + ', '.join(names) + ']', '  trace_state', '  exact Iff.rfl'])
    # Sanity controls and exact quantifier expansion for both candidate domains.
    lines.extend(['example : (∅ : Finset (Fin 1)) ≠ {0} := by decide', 'private theorem splitF (s : Finset (Fin 1)) : s = ∅ ∨ s = {0} := by', '  revert s', '  decide', 'private theorem splitS (s : Set (Fin 1)) : s = ∅ ∨ s = {0} := by', '  classical', '  by_cases h : (0 : Fin 1) ∈ s', '  · right', '    ext x', '    simpa [Subsingleton.elim x (0 : Fin 1), h]', '  · left', '    ext x', '    simpa [Subsingleton.elim x (0 : Fin 1), h]'])
    for tag, dom in [('F', 'Finset'), ('S', 'Set')]:
        lines.extend([f'private theorem all{tag} (P : {dom} (Fin 1) → Prop) : (∀ s, P s) ↔ P ∅ ∧ P {{0}} := by', '  constructor', '  · exact fun h => ⟨h _, h _⟩', '  · rintro ⟨h₀, h₁⟩ s', f'    rcases split{tag} s with rfl | rfl <;> assumption', f'private theorem ex{tag} (P : {dom} (Fin 1) → Prop) : (∃ s, P s) ↔ P ∅ ∨ P {{0}} := by', '  constructor', '  · rintro ⟨s, h⟩', f'    rcases split{tag} s with rfl | rfl', '    · exact Or.inl h', '    · exact Or.inr h', '  · rintro (h | h)', '    · exact ⟨∅, h⟩', '    · exact ⟨{0}, h⟩'])
    # Unfold available eligibility definitions. Missing optional names are harmless.
    local_defs = re.findall(r'(?m)^\s*(?:noncomputable\s+)?(?:def|abbrev)\s+([A-Za-z_][\w.]*)', source_text)
    helpers = [d for d in local_defs if any(k in d.lower() for k in ['clique', 'transversal']) and d.split('.')[-1] != 'cliqueTransversalNumber']
    helpers += ['SimpleGraph.IsCliqueTransversal', 'SimpleGraph.IsMaxClique', 'SimpleGraph.IsMaximalClique', 'SimpleGraph.IsNClique', 'SimpleGraph.IsClique', 'Maximal', 'Set.Pairwise', 'Set.Nonempty', 'Finset.Nonempty', 'Set.Disjoint', 'Finset.disjoint_left']
    unfold = 'Q, emptyQualifies, ' + ', '.join(names)
    lines.extend(['def verdict : Decidable Q := by', '  first'])
    for ctor in ['isTrue', 'isFalse']:
        lines.extend(['  | apply ' + ctor, '    first', '    | decide', '    | classical', '      dsimp only [' + unfold + ']'])
        for helper in dict.fromkeys(helpers):
            lines.append('      all_goals try simp only [' + helper + ']')
        lines.extend(['      all_goals simp [allF, exF, allS, exS, Fin.forall_fin_succ, Fin.exists_fin_succ] <;> first | decide | aesop', '      done'])
    lines.extend(['#print verdict', '#print axioms verdict', 'open Lean in', 'run_cmd do', '  let .defnInfo d ← getConstInfo ``verdict | throwError "expected a definition"', '  let head := d.value.consumeMData.getAppFn', '  if head.isConstOf ``Decidable.isTrue then', '    logInfo "VERDICT_TRUE"', '  else if head.isConstOf ``Decidable.isFalse then', '    logInfo "VERDICT_FALSE"', '  else', '    throwError "verdict body has no explicit decision constructor"', 'end Singleton151Probe'])
    program = '\n'.join(lines) + '\n'
    out['lean_input'] = program
    import tempfile
    with tempfile.TemporaryDirectory(dir=root) as tmp:
        work = Path(tmp)
        probe = work / 'SingletonProbe.lean'
        probe.write_text(program)
        env = {'HOME': tmp, 'TMPDIR': tmp, 'PATH': str(lean.parent), 'LEAN_PATH': os.pathsep.join(map(str, sorted(roots)))}
        try:
            run = subprocess.run([str(lean), str(probe)], cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=max(1, 98 - (time.monotonic() - start)))
            log = run.stdout
            out['returncode'] = run.returncode
            out['lean_output'] = log
            markers = re.findall(r'^.*\b(VERDICT_TRUE|VERDICT_FALSE)\s*$', log, re.M)
            if run.returncode == 0 and len(markers) == 1 and 'sorryAx' not in log and "uses 'sorry'" not in log:
                out['status'] = 'KERNEL_ACCEPTED'
                out['constructor'] = {'VERDICT_TRUE': 'isTrue', 'VERDICT_FALSE': 'isFalse'}[markers[0]]
                out['summary'] = 'The imported singleton candidate has a kernel-checked verdict. See the printed predicate, constructor, and axiom report.'
            else:
                out['summary'] = 'No accepted verdict. The compiler transcript identifies the first failed declaration and preserves any preceding definition printout.'
        except subprocess.TimeoutExpired as exc:
            data = exc.stdout or b''
            out['lean_output'] = data.decode(errors='replace') if isinstance(data, bytes) else data
            out['summary'] = 'Time budget reached before verification completed.'
        except OSError as exc:
            out['summary'] = 'The staged compiler could not start.'
            out['error'] = str(exc)
with open('result.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False)
