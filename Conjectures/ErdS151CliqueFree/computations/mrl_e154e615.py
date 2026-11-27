# MathResearchLab experiment e154e615-ec36-4c73-917f-0c939027b09b
# Kernel-check the singleton using the Erdős 151 import
# sha256(code) = 11c5fee7634fe619673bdb5d1ed3065782b259ac97cbfb2e3fd1c4c34cd87b78
# parameters: {"n": 1, "lean": "toolchain/bin/lean", "lean_path": [".lake/build/lib/lean"]}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
from pathlib import Path
import re
import subprocess

params = json.load(open(os.environ['MRL_PARAMS']))
assert params['n'] == 1

# Independently check the two readings. Neither value is supplied to Lean as a premise.
subsets = [frozenset(), frozenset({0})]
maximal = [s for s in subsets if not any(s < t for t in subsets)]
def qualifying(min_size):
    return [sorted(s) for s in subsets if all(s & c for c in maximal if len(c) >= min_size)]

sanity = {'maximal_cliques': [sorted(c) for c in maximal],
          'transversals_if_singletons_count': qualifying(1),
          'transversals_if_size_at_least_two': qualifying(2)}
assert sanity == {'maximal_cliques': [[0]], 'transversals_if_singletons_count': [[0]],
                  'transversals_if_size_at_least_two': [[], [0]]}

source = '''import FormalConjectures.ErdosProblems.«151»
open Erdos151 SimpleGraph
namespace Singleton151
set_option autoImplicit false
set_option maxHeartbeats 100000
#print H
#print cliqueTransversalNumber

private theorem uniqueGraph (G : SimpleGraph (Fin 1)) : G = ⊥ := by
  ext u v
  have h : u = v := Subsingleton.elim _ _
  subst v
  simp

-- Try executable definitions before introducing classical decidability.
macro "singleton_calc" : tactic =>
  `(tactic| first
    | decide
    | (classical; solve | simp | exact?)
    | (classical; simp [H, cliqueTransversalNumber, SimpleGraph.CliqueFree] <;> first | decide | grind | exact?))

theorem certificate (G : SimpleGraph (Fin 1)) :
    G.CliqueFree 4 ∧ H 1 = 1 ∧ cliqueTransversalNumber G = VALUE ∧
    ((cliqueTransversalNumber G ≤ 1 - H 1) ↔ (VALUE : ℕ) = 0) := by
  rw [uniqueGraph G]
  have hf : (⊥ : SimpleGraph (Fin 1)).CliqueFree 4 := by singleton_calc
  have hh : H 1 = 1 := by singleton_calc
  have ht : cliqueTransversalNumber (⊥ : SimpleGraph (Fin 1)) = VALUE := by singleton_calc
  exact ⟨hf, hh, ht, by simp [hh, ht]⟩

#print axioms Singleton151.certificate
end Singleton151
'''

root = Path.cwd().resolve()
def local(path):
    p = (root / path).resolve()
    if not p.is_relative_to(root):
        raise ValueError('The Lean installation and compiled imports must be inside the working directory')
    return p

report = {'scope': {'n': 1, 'graphs': 1, 'vertex_subsets': 2}, 'sanity': sanity,
          'lean_template': source, 'attempts': [], 'status': 'UNVERIFIED',
          'summary': 'The formal singleton inequality remains unchecked.'}
lean = local(params['lean'])
if not lean.is_file() or not os.access(lean, os.X_OK):
    report['remaining_gap'] = 'The Python sandbox has no bundled Lean executable at the specified path. The two convention checks do not identify the imported definition.'
else:
    dirs = [local(p) for p in params['lean_path']]
    deps = root / '.lake/packages'
    dirs.extend(local(p) for p in deps.glob('*/.lake/build/lib/lean'))
    env = dict(os.environ, LEAN_PATH=os.pathsep.join(map(str, dirs)))
    ordinary_axioms = {'propext', 'Classical.choice', 'Quot.sound'}
    for value in [0, 1]:
        try:
            run = subprocess.run([str(lean), '--stdin'], input=source.replace('VALUE', str(value)),
                                 cwd=root, env=env, capture_output=True, text=True, timeout=42)
        except (OSError, subprocess.TimeoutExpired) as e:
            report['attempts'].append({'value': value, 'status': 'TIMEOUT' if isinstance(e, subprocess.TimeoutExpired) else 'LAUNCH_ERROR', 'detail': str(e)})
            continue
        log = run.stdout + '\n' + run.stderr
        audit = re.search(r"'Singleton151\.certificate' (?:depends on axioms:\s*\[([^\]]*)\]|does not depend on any axioms)", log)
        axioms = sorted(a.strip() for a in (audit.group(1) or '').split(',') if a.strip()) if audit else None
        passed = run.returncode == 0 and axioms is not None and set(axioms) <= ordinary_axioms
        report['attempts'].append({'value': value, 'status': 'KERNEL_CHECKED' if passed else 'UNVERIFIED',
                                   'exit_code': run.returncode, 'axioms': axioms, 'lean_output': log})
        if passed:
            report.update(status='KERNEL_CHECKED', H_1=1, clique_free_four=True,
                          transversal_number=value, inequality_holds=(value == 0),
                          summary=('Lean certified the singleton inequality.' if value == 0 else 'Lean certified a singleton counterexample.'),
                          remaining_gap=('The computation covers only order one.' if value == 0 else 'None for the counterexample to the formal statement.'))
            break
    else:
        report['remaining_gap'] = 'Neither candidate has an accepted Lean certificate. The attempt logs record import, proof, timeout, or axiom-audit failures. A failed proof search gives no verdict on the inequality.'
with open('result.json', 'w') as out:
    json.dump(report, out, ensure_ascii=False)
