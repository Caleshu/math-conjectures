# MathResearchLab experiment 72752b63-5d94-4b6a-97f0-063d60e277b0
# Kernel check of the empty candidate on the singleton graph
# sha256(code) = 006c31a27896b649128c44588fbf609bb4962dee5a735ad627fb9fa072822f52
# parameters: {}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
params = json.load(open(os.environ['MRL_PARAMS']))
import re
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path.cwd().resolve()
END = time.monotonic() + 104
MODULE = 'FormalConjectures.ErdosProblems.«151»'
TARGET = ('FormalConjectures', 'ErdosProblems', '151.olean')

def inside(p):
    return p.resolve().is_relative_to(ROOT)

def log_excerpt(s):
    return s if len(s) <= 18000 else s[:9000] + '\n[output abbreviated]\n' + s[-9000:]

def experiment():
    executables, imports, roots, sources = [], [], set(), []
    for directory, dirs, files in os.walk(ROOT, followlinks=False):
        if time.monotonic() > END - 20:
            return {'summary': 'Dependency discovery reached its time budget.', 'status': 'discovery_timeout'}
        d = Path(directory)
        dirs[:] = [x for x in dirs if x not in {'.git', 'node_modules', '__pycache__'} and not (d/x).is_symlink()]
        if d.parts[-2:] == ('lib', 'lean'):
            roots.add(d)
        if 'lean' in files and inside(d/'lean') and os.access(d/'lean', os.X_OK):
            executables.append(d/'lean')
        if d.parts[-2:] == TARGET[:2]:
            if TARGET[-1] in files and inside(d/TARGET[-1]):
                imports.append(d/TARGET[-1])
                roots.add(d.parent.parent)
            if '151.lean' in files and inside(d/'151.lean'):
                sources.append(d/'151.lean')
    report = {'scope': {'order': 1, 'graph': 'bottom', 'candidate': 'empty'}, 'executables': [str(p.relative_to(ROOT)) for p in executables], 'compiled_imports': [str(p.relative_to(ROOT)) for p in imports]}
    for file in sorted(sources):
        src = file.read_text(errors='replace')
        m = re.search(r'\b(?:def|abbrev)\s+(?:[\w.]+\.)?cliqueTransversalNumber\b', src)
        if m:
            report['source_excerpt'] = {'file': str(file.relative_to(ROOT)), 'text': src[max(0,m.start()-1000):m.start()+1500]}
            break
    if not executables or not imports:
        missing = []
        if not executables: missing.append('an executable lean')
        if not imports: missing.append('/'.join(TARGET))
        return dict(report, status='missing_dependency', summary='No kernel verdict. Missing from the working tree: ' + ', '.join(missing) + '.')
    lean = sorted(executables, key=lambda p: (p.parent.name != 'bin', len(p.parts), str(p)))[0]
    preamble = 'import ' + MODULE + '\nopen SimpleGraph Erdos151\n'
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        work = Path(tmp).resolve()
        env = dict(os.environ)
        env.update(HOME=str(work), TMPDIR=str(work), LEAN_PATH=os.pathsep.join(map(str, [work] + sorted(roots))))
        env.pop('LEAN_SYSROOT', None)
        def run(name, source, compile=False, limit=22):
            remaining = END - time.monotonic()
            if remaining < 1: return None, 'Overall time budget reached.'
            path = work/(name + '.lean')
            path.write_text(source)
            args = [str(lean)] + (['-o', name + '.olean'] if compile else []) + [path.name]
            try:
                proc = subprocess.run(args, cwd=work, env=env, text=True, errors='replace', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=min(remaining,limit))
                return proc.returncode, proc.stdout
            except subprocess.TimeoutExpired as e:
                out = e.stdout or b''
                return None, 'Lean invocation timed out.\n' + (out.decode(errors='replace') if isinstance(out,bytes) else out)
            except OSError as e:
                return None, str(e)
        inspect_src = preamble + 'set_option pp.fullNames true in\n#print cliqueTransversalNumber\n'
        rc, definition = run('Inspect151', inspect_src)
        report['import_inspection'] = {'exit': rc, 'output': log_excerpt(definition)}
        if rc != 0:
            return dict(report, status='import_or_lookup_failed', summary='No kernel verdict. The import or definition lookup failed. The Lean diagnostic is recorded.')

        # Match at arbitrary order and arbitrary G. This prevents accidental matches caused by specializing a numerical minimum at order one.
        base = preamble + '''namespace Probe151
noncomputable section
private def atCandidate {A : Type} (e : A) (objective : (A → Prop) → ℕ)
    (value : ℕ) {P : A → Prop} (_h : objective P = value) : Prop := P e

def emptyCondition (n : ℕ) (G : SimpleGraph (Fin n)) : Prop := by
  classical
  first
'''
        for carrier, cardinal in [('Finset (Fin n)', 's.card'), ('Set (Fin n)', 's.ncard')]:
            objectives = []
            for relation in [cardinal+' = k', 'k = '+cardinal, cardinal+' ≤ k']:
                for tests in ['P s ∧ '+relation, relation+' ∧ P s']:
                    objectives.append('sInf {k : ℕ | ∃ s : '+carrier+', '+tests+'}')
            objectives += ['sInf ((fun s : '+carrier+' => '+cardinal+') \'\' {s | P s})', 'sInf (Set.range (fun s : {s : '+carrier+' // P s} => '+cardinal.replace('s.', 's.val.')+'))']
            for obj in objectives:
                base += '  | exact atCandidate (∅ : '+carrier+') (fun P => '+obj+') (cliqueTransversalNumber G) (by rfl)\n'
        base += '''
abbrev C : Prop := emptyCondition 1 (⊥ : SimpleGraph (Fin 1))

-- Both candidate polarities are exercised on known predicates using the same extractor.
private def cards (P : Finset (Fin 1) → Prop) : ℕ := sInf {k : ℕ | ∃ s : Finset (Fin 1), P s ∧ s.card = k}
example : atCandidate (∅ : Finset (Fin 1)) cards (cards (fun s => s = ∅)) (by rfl) := by rfl
example : ¬ atCandidate (∅ : Finset (Fin 1)) cards (cards (fun s => 0 ∈ s)) (by rfl) := by decide
set_option pp.explicit true in
set_option pp.fullNames true in
#print emptyCondition
end
end Probe151
'''
        rc, recovered = run('ProbeBase', base, compile=True, limit=25)
        report['extractor_source'] = base
        report['extraction'] = {'exit': rc, 'output': log_excerpt(recovered)}
        if rc != 0:
            return dict(report, status='extraction_or_sanity_failed', summary='No kernel verdict. Inspect the imported definition and the extractor diagnostic. The extractor requires a definitionally matching minimum-cardinality representation.')

        # Generate only simplifier hints from names. Every resulting proof is checked by Lean.
        known = ['Maximal', 'Set.Pairwise', 'Set.Nonempty', 'Finset.Nonempty', 'SimpleGraph.IsClique', 'SimpleGraph.IsMaxClique', 'SimpleGraph.IsMaximalClique', 'SimpleGraph.maxCliques', 'SimpleGraph.maximalCliques']
        for name in re.findall(r'\b[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+\b', definition+'\n'+recovered):
            if any(k in name.lower() for k in ['clique','transversal','maximal']) and not name.endswith('cliqueTransversalNumber'):
                known.append(name)
        hints = ', '.join(json.dumps(x) for x in sorted(set(known)))
        proof_support = '''import ProbeBase
open Lean Elab Tactic
namespace Probe151
private theorem twoAll {A : Type} {a b : A} (h : ∀ x, x = a ∨ x = b) (P : A → Prop) : (∀ x, P x) ↔ P a ∧ P b := by
  constructor
  · exact fun f => ⟨f a, f b⟩
  · rintro ⟨ha,hb⟩ x
    rcases h x with hx | hx <;> simpa only [hx] using (by first | exact ha | exact hb : P x) <;> assumption
'''
        # Use explicit substitution in the two elimination lemmas.
        proof_support = proof_support[:proof_support.index('    rcases')] + '''    rcases h x with hx | hx
    · exact hx.symm ▸ ha
    · exact hx.symm ▸ hb
private theorem twoEx {A : Type} {a b : A} (h : ∀ x, x = a ∨ x = b) (P : A → Prop) : (∃ x, P x) ↔ P a ∨ P b := by
  constructor
  · rintro ⟨x,hx⟩
    rcases h x with he | he
    · exact Or.inl (he ▸ hx)
    · exact Or.inr (he ▸ hx)
  · rintro (ha | hb)
    · exact ⟨a,ha⟩
    · exact ⟨b,hb⟩
'''
        lemmas = []
        for ty, tag in [('Finset (Fin 1)','F'), ('Set (Fin 1)','S')]:
            proof_support += 'private theorem cases'+tag+' (s : '+ty+') : s = ∅ ∨ s = {0} := by\n  classical\n  by_cases h : 0 ∈ s\n  · right\n    ext x\n    have hx : x = 0 := Subsingleton.elim _ _\n    simp [hx,h]\n  · left\n    ext x\n    have hx : x = 0 := Subsingleton.elim _ _\n    simp [hx,h]\n'
            for quant, helper, rhs in [('∀','twoAll','P ∅ ∧ P {0}'),('∃','twoEx','P ∅ ∨ P {0}')]:
                label = helper+tag
                proof_support += 'private theorem '+label+' (P : '+ty+' → Prop) : ('+quant+' x, P x) ↔ '+rhs+' := '+helper+' cases'+tag+' P\n'
                lemmas.append(label)
        proof_support += '''elab "singleton_simp" : tactic => do
  let env ← getEnv
  let ns : List String := [''' + hints + ''']
  let ids := (ns.filterMap fun s => if (env.find? s.toName).isSome then some (mkIdent s.toName) else none).toArray
  evalTactic (← `(tactic| simp [C, emptyCondition, ''' + ', '.join(lemmas) + ''', $[$ids:ident],*]))
'''
        # The extractor is private. Make its reduction available through dsimp after unfolding emptyCondition.
        # delta-reduction of the application is also needed by simp to expose an anonymous recovered predicate.
        base = base.replace('private def atCandidate', '@[simp] def atCandidate')
        rc, updated = run('ProbeBase', base, compile=True, limit=15)
        report['extractor_source'] = base
        if rc != 0:
            return dict(report, status='base_compile_failed', summary='No kernel verdict. The proof-support import failed to compile.', diagnostic=log_excerpt(updated))
        report['attempts'] = []
        for polarity, target in [('satisfies', 'C'), ('fails', '¬ C')]:
            name = 'empty_' + polarity
            cert = proof_support + 'theorem '+name+' : '+target+' := by\n  first\n  | decide\n  | classical\n    singleton_simp <;> first | decide | aesop\n#print axioms '+name+'\nend Probe151\n'
            rc, out = run('Verdict', cert, compile=True, limit=24)
            report['attempts'].append({'polarity': polarity, 'exit': rc, 'output': log_excerpt(out)})
            if rc != 0: continue
            match = re.search(r"'Probe151\."+name+r"' depends on axioms:\s*\[([^\]]*)\]",out)
            clean = ("'Probe151."+name+"' does not depend on any axioms") in out
            if match:
                clean = {a.strip() for a in match.group(1).split(',')} <= {'propext','Classical.choice','Quot.sound'}
            if clean:
                return dict(report, status='kernel_accepted', verdict=polarity, certificate_source=cert, summary='Lean accepted Probe151.'+name+' for the recovered empty-candidate condition on the singleton graph.')
        return dict(report, status='no_certificate', proof_support=proof_support, summary='The generic predicate extraction and sanity checks passed. Neither attempted polarity yielded a validated certificate within the budget. See the Lean diagnostics.')

try:
    result = experiment()
except Exception as exc:
    result = {'status':'driver_error','summary':'No kernel verdict. The driver encountered an error.', 'diagnostic':repr(exc)}
(ROOT/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))