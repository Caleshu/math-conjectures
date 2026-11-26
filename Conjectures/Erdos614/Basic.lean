/-
# Erdős Problem 614 — general finite-graph lemmas

Notation (complement form of the problem, see `PROOF.md`):
* `degIn H S v` — number of neighbours of `v` inside the vertex set `S`;
* `TwoSet H S`  — every vertex of `S` has at least two neighbours inside `S`
                  (i.e. `H[S]` has minimum degree ≥ 2);
* `D H S`       — the degree sum `∑_{v ∈ S} degIn H S v` (= twice the number of edges of `H[S]`).
-/
import Mathlib.Combinatorics.SimpleGraph.Finite
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic.Linarith

set_option linter.unusedSectionVars false

namespace Conjectures.Erdos614

open Finset

variable {V : Type*} [DecidableEq V] (H : SimpleGraph V) [DecidableRel H.Adj]

/-- Number of neighbours of `v` inside `S`. -/
def degIn (S : Finset V) (v : V) : ℕ := #(S.filter (H.Adj v))

/-- `H[S]` has minimum degree at least 2. -/
def TwoSet (S : Finset V) : Prop := ∀ v ∈ S, 2 ≤ degIn H S v

/-- Degree sum of `H[S]` (twice its number of edges). -/
def D (S : Finset V) : ℕ := ∑ v ∈ S, degIn H S v

variable {H}

lemma degIn_mono {S T : Finset V} (h : S ⊆ T) (v : V) : degIn H S v ≤ degIn H T v :=
  card_le_card (filter_subset_filter _ h)

lemma degIn_le_card (S : Finset V) (v : V) : degIn H S v ≤ #S := card_filter_le _ _

lemma degIn_le_card_sub_one {S : Finset V} {v : V} (hv : v ∈ S) : degIn H S v ≤ #S - 1 := by
  have hsub : S.filter (H.Adj v) ⊆ S.erase v := by
    intro w hw
    rw [mem_filter] at hw
    exact mem_erase.mpr ⟨(H.ne_of_adj hw.2).symm, hw.1⟩
  calc degIn H S v ≤ #(S.erase v) := card_le_card hsub
    _ = #S - 1 := card_erase_of_mem hv

lemma D_le (S : Finset V) : D H S ≤ #S * (#S - 1) := by
  unfold D
  calc ∑ v ∈ S, degIn H S v ≤ ∑ _v ∈ S, (#S - 1) :=
        sum_le_sum fun v hv => degIn_le_card_sub_one hv
    _ = #S * (#S - 1) := by simp

/-- Degree into a disjoint union splits. -/
lemma degIn_union {A B : Finset V} (h : Disjoint A B) (v : V) :
    degIn H (A ∪ B) v = degIn H A v + degIn H B v := by
  unfold degIn
  rw [filter_union, card_union_of_disjoint (disjoint_filter_filter h)]

/-- Removing a vertex `v ∈ S` lowers the degree of `w` by one iff `w ~ v`. -/
lemma degIn_erase {S : Finset V} {v : V} (hv : v ∈ S) (w : V) :
    degIn H S w = degIn H (S.erase v) w + if H.Adj w v then 1 else 0 := by
  unfold degIn
  rw [filter_erase]
  split_ifs with h
  · exact (card_erase_add_one (mem_filter.mpr ⟨hv, h⟩)).symm
  · rw [erase_eq_of_notMem (fun hm => h (mem_filter.mp hm).2), add_zero]

/-- Vertex-removal identity for degree sums. -/
lemma D_erase {S : Finset V} {v : V} (hv : v ∈ S) :
    D H S = D H (S.erase v) + 2 * degIn H S v := by
  unfold D
  rw [← add_sum_erase S _ hv]
  have h1 : ∑ w ∈ S.erase v, degIn H S w
      = ∑ w ∈ S.erase v, degIn H (S.erase v) w + ∑ w ∈ S.erase v, (if H.Adj w v then 1 else 0) := by
    rw [← sum_add_distrib]
    exact sum_congr rfl fun w _ => degIn_erase hv w
  have h2 : ∑ w ∈ S.erase v, (if H.Adj w v then 1 else 0) = degIn H S v := by
    rw [sum_boole, Nat.cast_id]
    unfold degIn
    congr 1
    ext w
    simp only [mem_filter, mem_erase]
    constructor
    · rintro ⟨⟨_, hw⟩, hadj⟩; exact ⟨hw, hadj.symm⟩
    · rintro ⟨hw, hadj⟩; exact ⟨⟨(H.ne_of_adj hadj).symm, hw⟩, hadj.symm⟩
  rw [h1, h2]
  omega

/-- Double counting of edges between two vertex sets. -/
lemma sum_degIn_comm (A B : Finset V) :
    ∑ v ∈ A, degIn H B v = ∑ w ∈ B, degIn H A w := by
  unfold degIn
  simp_rw [card_filter]
  rw [sum_comm]
  refine sum_congr rfl fun w _ => sum_congr rfl fun v _ => ?_
  simp only [H.adj_comm]

/-- **Peeling lemma.** If every 2-set inside `X` has at most `t` vertices, then
`D(X) ≤ max (2(|X|-1)) (t(t-1) + 2(|X|-t))`. -/
lemma D_le_of_twoSets_le (t : ℕ) :
    ∀ (X : Finset V), (∀ T ⊆ X, TwoSet H T → #T ≤ t) →
      D H X ≤ max (2 * (#X - 1)) (t * (t - 1) + 2 * (#X - t)) := by
  intro X
  obtain ⟨x, hx⟩ : ∃ x, #X = x := ⟨_, rfl⟩
  induction x generalizing X with
  | zero =>
    intro _
    have : X = ∅ := card_eq_zero.mp hx
    subst this
    simp [D]
  | succ x ih =>
    intro hT
    by_cases hxt : x + 1 ≤ t
    · -- small sets: trivial bound
      have h1 := D_le (H := H) X
      rw [hx] at h1
      have h2 : (x + 1) * (x + 1 - 1) ≤ t * (t - 1) :=
        Nat.mul_le_mul hxt (Nat.sub_le_sub_right hxt 1)
      exact le_trans (le_trans h1 h2) (le_trans (Nat.le_add_right _ _) (le_max_right _ _))
    · push_neg at hxt
      -- `X` is too big to be a 2-set, so some vertex has degree ≤ 1
      have hnot : ¬ TwoSet H X := fun h2 => by
        have := hT X subset_rfl h2
        omega
      unfold TwoSet at hnot
      push_neg at hnot
      obtain ⟨v, hv, hdeg⟩ := hnot
      have hcard : #(X.erase v) = x := by simp [card_erase_of_mem hv, hx]
      have hrec := ih (X.erase v) hcard
        (fun T hTX h2 => hT T (hTX.trans (erase_subset v X)) h2)
      rw [D_erase hv, hx]
      rw [hcard] at hrec
      generalize t * (t - 1) = c at hrec ⊢
      have hd : degIn H X v ≤ 1 := by omega
      -- now purely linear
      rcases le_total (2 * (x - 1)) (c + 2 * (x - t)) with h | h
      · rw [max_eq_right h] at hrec
        apply le_max_of_le_right
        omega
      · rw [max_eq_left h] at hrec
        rcases Nat.lt_or_ge x 1 with hx1 | hx1
        · apply le_max_of_le_right; omega
        · apply le_max_of_le_left; omega

end Conjectures.Erdos614
