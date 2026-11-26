/-
# Inscribed squares in Hamiltonian cycles of the hypercube (Sagols–Morales-Luna 2010)

Let `H` be a Hamiltonian cycle of the hypercube `Q_n`. `H` has an *inscribed square* if it
contains two opposite edges of some 4-cycle of `Q_n`: two direction-`i` edges whose endpoints
differ in exactly one further coordinate `j`.

**Conjecture.** For every `n ≥ 2`, every Hamiltonian cycle of `Q_n` has an inscribed square.

Source: F. Sagols, G. Morales-Luna, *Parity balance of the i-th dimension edges in Hamiltonian
cycles of the hypercube*, arXiv:1009.3304 (2010), Conjecture 5.1.

Status: **false**. `Counterexample.lean` builds a square-free Hamiltonian cycle of `Q_8`.
-/
import Mathlib.Combinatorics.SimpleGraph.Hamiltonian

namespace Conjectures.HypercubeSquares

open Finset

/-- Flip coordinate `i` of a vertex of the cube. -/
def flip {n : ℕ} (u : Fin n → Bool) (i : Fin n) : Fin n → Bool :=
  Function.update u i (!u i)

/-- The `n`-dimensional hypercube `Q_n` on `{0,1}^n`: two vertices are adjacent iff they differ
in exactly one coordinate. -/
def cube (n : ℕ) : SimpleGraph (Fin n → Bool) where
  Adj u v := (univ.filter fun i => u i ≠ v i).card = 1
  symm := ⟨fun u v h => by simpa only [ne_comm] using h⟩
  loopless := ⟨fun u h => by simp at h⟩

/-- The walk `c` contains an inscribed square: a direction-`i` edge `{u, u + eᵢ}` together with
the opposite edge `{u + eⱼ, u + eⱼ + eᵢ}` of the 4-cycle spanned by directions `i ≠ j`. -/
def HasInscribedSquare {n : ℕ} {v : Fin n → Bool} (c : (cube n).Walk v v) : Prop :=
  ∃ (u : Fin n → Bool) (i j : Fin n), i ≠ j ∧
    s(u, flip u i) ∈ c.edges ∧ s(flip u j, flip (flip u j) i) ∈ c.edges

/-- **Sagols–Morales-Luna conjecture.** Every Hamiltonian cycle of `Q_n`, `n ≥ 2`, has an
inscribed square. It is **false**: see `not_conjecture` in `Counterexample.lean`. -/
def Conjecture : Prop :=
  ∀ n : ℕ, 2 ≤ n → ∀ (v : Fin n → Bool) (c : (cube n).Walk v v),
    c.IsHamiltonianCycle → HasInscribedSquare c

end Conjectures.HypercubeSquares
