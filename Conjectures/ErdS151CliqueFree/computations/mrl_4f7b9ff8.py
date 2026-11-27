# MathResearchLab experiment 4f7b9ff8-8129-4263-b221-ea68e561a82e
# Extract the singleton eligibility predicate and certify its polarity
# sha256(code) = 91aee5d4a87a0504da970e1755b5ac6f763701fbea32bd147bc26847a25951e9
# parameters: {"lean_paths": []}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from pathlib import Path
import re
import subprocess
import tempfile
import time

params = json.load(open(os.environ['MRL_PARAMS']))
root = Path.cwd().resolve()
deadline = time.monotonic() + 92
module = 'FormalConjectures/ErdosProblems/151'

def local(path):
    p = Path(path).resolve()
    return p == root or root in p.parents

def matches(pattern):
    return sorted(p.resolve() for p in root.glob(pattern) if local(p))

def source_excerpt(path):
    lines = path.read_text(errors='replace').splitlines()
    for i, line in enumerate(lines):
        if re.search(r'\b(?:def|abbrev)\s+(?:[\w.]+\.)?cliqueTransversalNumber\b', line):
            return {'path': str(path.relative_to(root)), 'first_line': i + 1,
                    'text': '\n'.join(lines[i:i + 24])}
    return {'path': str(path.relative_to(root)), 'definition_in_excerpt': False}

def lean_probe():
    header = '''import FormalConjectures.ErdosProblems.«151»
namespace Erdos151
open SimpleGraph
#print cliqueTransversalNumber
private abbrev tauProbe := cliqueTransversalNumber (⊥ : SimpleGraph (Fin 1))
'''
    # The underscores in `pickN (p := _) rfl` are essential. Lean supplies
    # the predicate from the import. None of these templates says which
    # cliques are eligible or what it means to meet one.
    defs, names = [], []
    for domain, card in [('Finset (Fin 1)', 's.card'), ('Set (Fin 1)', 's.ncard')]:
        for size in [card + ' = k', 'k = ' + card, card + ' ≤ k']:
            for body in [size + ' ∧ p s', 'p s ∧ ' + size,
                         '∃ _ : p s, ' + size, '∃ _ : ' + size + ', p s']:
                name = 'probePick' + str(len(names))
                names.append(name)
                defs.append(f'private def {name} {{p : {domain} → Prop}}\n'
                            f'    (_ : tauProbe = sInf {{k : ℕ | ∃ s : {domain}, {body}}}) : Prop := p ∅\n')
    extract = 'def singletonProbeQ : Prop := by\n  first\n' + ''.join(
        f'  | exact {name} (p := _) rfl\n' for name in names)
    inspect = '''set_option pp.explicit true in
#print singletonProbeQ
'''
    finite = '''private theorem probeAll {α : Type} {a b : α}
    (cover : ∀ x : α, x = a ∨ x = b) (p : α → Prop) :
    (∀ x, p x) ↔ p a ∧ p b := by
  constructor
  · intro h
    exact ⟨h a, h b⟩
  · rintro ⟨ha, hb⟩ x
    rcases cover x with h | h
    · simpa only [h] using ha
    · simpa only [h] using hb
private theorem probeEx {α : Type} {a b : α}
    (cover : ∀ x : α, x = a ∨ x = b) (p : α → Prop) :
    (∃ x, p x) ↔ p a ∨ p b := by
  constructor
  · rintro ⟨x, hx⟩
    rcases cover x with h | h
    · exact Or.inl (h ▸ hx)
    · exact Or.inr (h ▸ hx)
  · rintro (ha | hb)
    · exact ⟨a, ha⟩
    · exact ⟨b, hb⟩
'''
    for name, domain in [('probeF', 'Finset (Fin 1)'), ('probeS', 'Set (Fin 1)')]:
        finite += f'''private theorem {name} (s : {domain}) : s = ∅ ∨ s = {{0}} := by
  classical
  by_cases h : 0 ∈ s
  · right
    ext i
    simp [Subsingleton.elim i (0 : Fin 1), h]
  · left
    ext i
    simp [Subsingleton.elim i (0 : Fin 1), h]
'''
    # The finite-domain rewrites are proved above independently of the
    # imported convention. Each optional unfolding is only a proof tactic.
    reduced = ', '.join(['singletonProbeQ'] + names)
    finite_simps = ('probeAll probeF, probeEx probeF, probeAll probeS, probeEx probeS, '
                    'Fin.forall_fin_succ, Fin.exists_fin_succ')
    optional = ['IsCliqueTransversal', 'SimpleGraph.IsCliqueTransversal',
                'SimpleGraph.maxCliques', 'SimpleGraph.maximalCliques',
                'SimpleGraph.IsMaxClique', 'SimpleGraph.IsMaximalClique',
                'Maximal', 'SimpleGraph.IsClique', 'Set.Pairwise',
                'Finset.Nonempty', 'Set.Nonempty', 'Finset.disjoint_left',
                'Set.disjoint_left']
    proof = '    first\n    | decide\n    | classical\n      simp only [' + reduced + ']\n'
    for name in optional:
        proof += '      all_goals try simp only [' + name + ']\n'
    proof += '      all_goals simp_all [' + finite_simps + ']\n      all_goals first | decide | aesop\n'
    # A tactic branch can only succeed after its proof term is complete.
    verdict = 'def singletonProbeDecision : Decidable singletonProbeQ := by\n  first\n'
    for ctor in ['isTrue', 'isFalse']:
        verdict += '  | exact ' + ctor + ' (by\n' + proof + '    )\n'
    verdict += '''#print singletonProbeDecision
#print axioms singletonProbeDecision
private def probeBit : Bool :=
  match singletonProbeDecision with
  | isTrue _ => true
  | isFalse _ => false
-- Require the tag to reduce by definitional equality in the kernel.
private theorem probeTagReduces : probeBit = true ∨ probeBit = false := by
  first | exact Or.inl rfl | exact Or.inr rfl
#eval if probeBit then "MRL_isTrue" else "MRL_isFalse"
end Erdos151
'''
    return header + '\n'.join(defs) + extract + inspect + finite + verdict

def run():
    code = lean_probe()
    sources = matches('**/' + module + '.lean')
    artifacts = matches('**/' + module + '.olean')
    out = {'status': 'inconclusive', 'polarity': None,
           'scope': {'n': 1, 'graph': 'bottom', 'candidate': 'empty'},
           'source_evidence': [source_excerpt(p) for p in sources],
           'import_artifacts': [str(p.relative_to(root)) for p in artifacts],
           'lean_input': code}
    executables = matches('**/bin/lean')
    if params.get('lean'):
        executables.insert(0, (root / params['lean']).resolve())
    lean = next((p for p in executables if local(p) and p.is_file() and os.access(p, os.X_OK)), None)
    if lean is None:
        out['summary'] = 'No executable Lean kernel driver was found inside the workspace. The attached probe has no kernel verdict.'
        return out
    if not artifacts and not sources:
        out['summary'] = 'The named module is absent as both source and compiled import. Its predicate could not be extracted.'
        return out
    with tempfile.TemporaryDirectory(dir=root) as tmp:
        work = Path(tmp)
        roots = [work] + [p.parents[2] for p in artifacts]
        roots += matches('**/build/lib/lean') + matches('**/toolchain/lib/lean')
        for entry in params.get('lean_paths', []):
            p = (root / entry).resolve()
            if not local(p):
                raise ValueError('lean_paths must stay inside the working directory')
            roots.append(p)
        env = dict(os.environ, LEAN_PATH=os.pathsep.join(map(str, dict.fromkeys(roots))), TMPDIR=tmp)
        def invoke(args, cwd):
            remaining = deadline - time.monotonic()
            if remaining < 1:
                raise TimeoutError('probe time budget exhausted')
            proc = subprocess.run([str(lean), '-j1', '-DwarningAsError=true', *args],
                                  cwd=cwd, env=env, capture_output=True, text=True,
                                  errors='replace', timeout=remaining)
            return proc.returncode, proc.stdout + proc.stderr
        if not artifacts:
            src = sources[0]
            obj = work / (module + '.olean')
            obj.parent.mkdir(parents=True)
            rc, log = invoke(['-o', str(obj), str(src)], src.parents[2])
            out['module_build'] = {'exit_code': rc, 'transcript': log}
            if rc:
                out['summary'] = 'The module source was found, but compiling it against the staged dependencies failed. See module_build.'
                return out
        file = work / 'SingletonProbe.lean'
        file.write_text(code)
        rc, log = invoke([str(file)], work)
        out.update(exit_code=rc, transcript=log)
        if rc:
            out['summary'] = 'Lean rejected the probe. The transcript gives the imported definition if loading succeeded, and the first failed obligation.'
            return out
        tags = re.findall(r'^"MRL_(isTrue|isFalse)"\s*$', log, re.M)
        ax = re.search(r"'Erdos151\.singletonProbeDecision' depends on axioms:\s*\[([^\]]*)\]", log)
        ax_free = "'Erdos151.singletonProbeDecision' does not depend on any axioms" in log
        axioms = [a.strip() for a in ax.group(1).split(',') if a.strip()] if ax else []
        out['axioms'] = axioms if ax or ax_free else None
        if len(tags) != 1 or not (ax or ax_free) or set(axioms) - {'propext', 'Classical.choice', 'Quot.sound'}:
            out['summary'] = 'Lean exited successfully, but the constructor tag or axiom audit could not be validated. Inspect the transcript.'
            return out
        out.update(status='kernel_accepted', polarity=tags[0], author_support='proved_here',
                   justification='The printed definition instantiates the imported eligibility predicate at the empty set. The printed declaration inhabits Decidable singletonProbeQ, and probeTagReduces checks constructor reduction by rfl.')
        out['summary'] = 'The singleton declaration was kernel-accepted with constructor ' + tags[0] + '.'
        return out

try:
    result = run()
except subprocess.TimeoutExpired as exc:
    partial = exc.stdout or b''
    result = {'summary': 'The bounded Lean check timed out without a certified polarity.', 'status': 'timeout', 'polarity': None, 'partial_stdout': partial.decode(errors='replace') if isinstance(partial, bytes) else partial}
except (OSError, ValueError, TimeoutError) as exc:
    result = {'summary': 'The local probe could not complete.', 'status': 'inconclusive', 'polarity': None, 'error': str(exc)}
Path('result.json').write_text(json.dumps(result, ensure_ascii=False))