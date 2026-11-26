/-
# Erdős Problem 63

Does every graph with infinite chromatic number contain a cycle of length 2ⁿ for
infinitely many n?

Status: solved (affirmatively), following Liu–Montgomery (2020). See README.md.
Statement adapted from google-deepmind/formal-conjectures (Apache 2.0),
using only core Mathlib definitions.
-/
import Mathlib.Combinatorics.SimpleGraph.Coloring.Vertex
import Mathlib.Combinatorics.SimpleGraph.Paths

namespace Conjectures.Erdos63

open SimpleGraph

/-- `G` contains a cycle of length exactly `m`. -/
def HasCycleOfLength {V : Type*} (G : SimpleGraph V) (m : ℕ) : Prop :=
  ∃ (u : V) (p : G.Walk u u), p.IsCycle ∧ p.length = m

/-- **Erdős Problem 63.** Every graph with infinite chromatic number has a cycle of
length `2 ^ n` for infinitely many `n` (stated as: for every `N` there is such an
`n ≥ N`). -/
theorem erdos_63 {V : Type*} (G : SimpleGraph V) (hG : G.chromaticNumber = ⊤) :
    ∀ N : ℕ, ∃ n ≥ N, HasCycleOfLength G (2 ^ n) := by
  sorry

end Conjectures.Erdos63
