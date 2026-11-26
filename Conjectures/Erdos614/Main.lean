/-
# Erdős Problem 614

Let f(n,k) be the minimum number of edges in a graph on n vertices in which every set of
k+2 vertices induces a subgraph of maximum degree at least k.  Determine f(n,k).

Status: open in general.  See README.md for the results in this folder:
* Theorem (proved on paper in README.md, verified by computer for n ≤ 10):
    f(n,k) = (n-k-1)(n+k-2)/2   whenever  k+2 ≤ n ≤ (3k+2)/2.
* Conjecture (verified for n ≤ 10): the same formula holds for all k+2 ≤ n ≤ 2k,
  and it fails at n = 2k+1 (proved).

The definition below matches google-deepmind/formal-conjectures (Apache 2.0),
`FormalConjectures/ErdosProblems/614.lean`.  The Lean proofs are not written yet (`sorry`).
-/
import Mathlib.Combinatorics.SimpleGraph.Finite
import Mathlib.Combinatorics.SimpleGraph.Maps

namespace Conjectures.Erdos614

open scoped Classical

/-- `G` has the Erdős 614 property for `k`: every `(k+2)`-set of vertices induces a subgraph
with a vertex of degree at least `k`. -/
def Good {n : ℕ} (k : ℕ) (G : SimpleGraph (Fin n)) : Prop :=
  ∀ s : Finset (Fin n), s.card = k + 2 →
    ∃ v : s, k ≤ (G.induce (s : Set (Fin n))).degree v

/-- The set of edge counts of good graphs; `f(n,k)` is its least element. -/
def edgeCounts (n k : ℕ) : Set ℕ :=
  {m | ∃ G : SimpleGraph (Fin n), G.edgeFinset.card = m ∧ Good k G}

/-- **Theorem (this folder, proof in README.md).** For `k + 2 ≤ n ≤ (3k+2)/2`,
`f(n,k) = (n-k-1)(n+k-2)/2`. -/
theorem f_eq_of_le_three_halves (n k : ℕ) (h₁ : k + 2 ≤ n) (h₂ : 2 * n ≤ 3 * k + 2) :
    IsLeast (edgeCounts n k) ((n - k - 1) * (n + k - 2) / 2) := by
  sorry

/-- **Conjecture (this folder; verified for n ≤ 10).** The same formula for `k + 2 ≤ n ≤ 2k`. -/
theorem f_eq_of_le_two_mul (n k : ℕ) (h₁ : k + 2 ≤ n) (h₂ : n ≤ 2 * k) :
    IsLeast (edgeCounts n k) ((n - k - 1) * (n + k - 2) / 2) := by
  sorry

/-- **Sharpness (proved in README.md).** At `n = 2k+1` (for `k ≥ 2`) the formula is beaten by one. -/
theorem f_lt_at_two_mul_add_one (k : ℕ) (hk : 2 ≤ k) :
    ∃ m ∈ edgeCounts (2 * k + 1) k, m + 1 = k * (3 * k - 1) / 2 := by
  sorry

end Conjectures.Erdos614
