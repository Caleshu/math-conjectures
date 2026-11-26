/-
# Erdős Problem 64 (Erdős–Gyárfás conjecture)

Does every finite graph with minimum degree at least 3 contain a cycle of length
2ᵏ for some k ≥ 2?

Status: open. See README.md.
Statement adapted from google-deepmind/formal-conjectures (Apache 2.0).
-/
import Mathlib.Combinatorics.SimpleGraph.Finite
import Mathlib.Combinatorics.SimpleGraph.Paths

namespace Conjectures.Erdos64

/-- **Erdős Problem 64.** Every finite graph with minimum degree at least 3 contains a
cycle whose length is a power of two, `2 ^ k` with `k ≥ 2` (so length 4, 8, 16, …). -/
theorem erdos_64 (V : Type*) (G : SimpleGraph V) [Fintype V] [DecidableRel G.Adj]
    (hδ : G.minDegree ≥ 3) :
    ∃ (k : ℕ) (v : V) (c : G.Walk v v), k ≥ 2 ∧ c.IsCycle ∧ c.length = 2 ^ k := by
  sorry

end Conjectures.Erdos64
