/-
# Erdős Problem 614 — main theorem

Let `f(n,k)` be the minimum number of edges of a graph on `n` vertices in which every set of
`k+2` vertices induces a subgraph of maximum degree at least `k`.

**Theorem (`f_eq`).** If `k + 2 ≤ n` and `2n ≤ 3k + 2`, then `f(n,k) = (n-k-1)(n+k-2)/2`.

The definitions `Good` / `edgeCounts` match google-deepmind/formal-conjectures
(`FormalConjectures/ErdosProblems/614.lean`, Apache 2.0): `f(n,k)` is the least element of
`edgeCounts n k`. No `sorry`, `admit` or new axioms are used (check with `#print axioms f_eq`).

The formula itself is the value `q(k,2,n-k-2) = (l+1)k + C(l+1,2)` of Erdős–Reid–Schelp–Staton
(Discrete Math. 158 (1996)); they proved it for `k ≥ max(2l, C(l+2,2))` and Pikhurko–Thomason
(Discrete Math. 248 (2002), Thm 14) for `k ≥ (8l+2)/3`, where `l = n-k-2`. The range here is
`k ≥ 2l+2`. See `README.md` and `PROOF.md`.
-/
import Conjectures.Erdos614.Claim
import Mathlib.Combinatorics.SimpleGraph.Maps
import Mathlib.Combinatorics.SimpleGraph.DegreeSum
import Mathlib.Order.Interval.Finset.Nat

set_option linter.unusedSectionVars false

namespace Conjectures.Erdos614

open Finset

section Defs

open scoped Classical

/-- `G` has the Erdős 614 property for `k`: every `(k+2)`-set of vertices induces a subgraph
with a vertex of degree at least `k`. -/
def Good {n : ℕ} (k : ℕ) (G : SimpleGraph (Fin n)) : Prop :=
  ∀ s : Finset (Fin n), s.card = k + 2 →
    ∃ v : s, k ≤ (G.induce (s : Set (Fin n))).degree v

/-- Edge counts of good graphs; `f(n,k)` is the least element of this set. -/
def edgeCounts (n k : ℕ) : Set ℕ :=
  {m | ∃ G : SimpleGraph (Fin n), G.edgeFinset.card = m ∧ Good k G}

end Defs

/-! ### Translating induced degrees and complements -/

lemma induce_degree_eq {n : ℕ} (G : SimpleGraph (Fin n)) [DecidableRel G.Adj]
    (s : Finset (Fin n)) (v : (s : Set (Fin n)))
    [Fintype ((G.induce (s : Set (Fin n))).neighborSet v)] :
    (G.induce (s : Set (Fin n))).degree v = #(s.filter (G.Adj v)) := by
  rw [← SimpleGraph.card_neighborFinset_eq_degree]
  have h : ((G.induce (s : Set (Fin n))).neighborFinset v).map
      (Function.Embedding.subtype _) = s.filter (G.Adj v) := by
    ext w
    constructor
    · intro hw
      rw [mem_map] at hw
      obtain ⟨x, hx, rfl⟩ := hw
      rw [SimpleGraph.mem_neighborFinset] at hx
      exact mem_filter.mpr ⟨Finset.mem_coe.mp x.2, hx⟩
    · intro hw
      rw [mem_filter] at hw
      rw [mem_map]
      exact ⟨⟨w, Finset.mem_coe.mpr hw.1⟩, by rw [SimpleGraph.mem_neighborFinset]; exact hw.2, rfl⟩
  rw [← h, card_map]

lemma card_adj_add_card_compl_adj {V : Type*} [DecidableEq V] (G : SimpleGraph V)
    [DecidableRel G.Adj] (s : Finset V) {v : V} (hv : v ∈ s) :
    #(s.filter (G.Adj v)) + #(s.filter (Gᶜ.Adj v)) = #s - 1 := by
  have h1 : s.filter (G.Adj v) = (s.erase v).filter (G.Adj v) := by
    ext w
    simp only [mem_filter, mem_erase]
    constructor
    · rintro ⟨hw, hadj⟩; exact ⟨⟨(G.ne_of_adj hadj).symm, hw⟩, hadj⟩
    · rintro ⟨⟨_, hw⟩, hadj⟩; exact ⟨hw, hadj⟩
  have h2 : s.filter (Gᶜ.Adj v) = (s.erase v).filter (fun w => ¬ G.Adj v w) := by
    ext w
    simp only [mem_filter, mem_erase, SimpleGraph.compl_adj]
    constructor
    · rintro ⟨hw, hne, hadj⟩; exact ⟨⟨hne.symm, hw⟩, hadj⟩
    · rintro ⟨⟨hne, hw⟩, hadj⟩; exact ⟨hw, hne.symm, hadj⟩
  rw [h1, h2, card_filter_add_card_filter_not, card_erase_of_mem hv]

/-- A good graph's complement has no `(k+2)`-set of minimum degree `≥ 2`. -/
lemma not_twoSet_compl_of_good {n k : ℕ} (G : SimpleGraph (Fin n)) [DecidableRel G.Adj]
    (hG : Good k G) (S : Finset (Fin n)) (hS : #S = k + 2) : ¬ TwoSet Gᶜ S := by
  classical
  intro h2
  obtain ⟨⟨v, hv⟩, hdeg⟩ := hG S hS
  have hv' : v ∈ S := Finset.mem_coe.mp hv
  have e := induce_degree_eq G S ⟨v, hv⟩
  have hsplit := card_adj_add_card_compl_adj G S hv'
  have h := h2 v hv'
  unfold degIn at h
  -- the two instances of `Fintype (neighborSet)` agree
  have hdeg' : k ≤ #(S.filter (G.Adj v)) := by
    rw [← e]
    convert hdeg
  omega

/-- The number of edges does not depend on the `Fintype` instance used for `edgeSet`. -/
lemma card_edgeFinset_inst {V : Type*} (G : SimpleGraph V) (i₁ i₂ : Fintype G.edgeSet) :
    @Finset.card _ (@SimpleGraph.edgeFinset V G i₁) =
      @Finset.card _ (@SimpleGraph.edgeFinset V G i₂) := by
  rw [Subsingleton.elim i₁ i₂]

/-- Degree sums of a graph and its complement on `Fin n`. -/
lemma two_mul_card_edges_add_D_compl {n : ℕ} (G : SimpleGraph (Fin n)) [DecidableRel G.Adj] :
    2 * #G.edgeFinset + D Gᶜ univ = n * (n - 1) := by
  rw [← G.sum_degrees_eq_twice_card_edges]
  unfold D degIn
  rw [← sum_add_distrib]
  have : ∀ v ∈ (univ : Finset (Fin n)),
      G.degree v + #(univ.filter (Gᶜ.Adj v)) = n - 1 := by
    intro v hv
    rw [← SimpleGraph.card_neighborFinset_eq_degree, SimpleGraph.neighborFinset_eq_filter,
      card_adj_add_card_compl_adj G univ hv]
    simp
  rw [sum_congr rfl this, sum_const, card_univ, Fintype.card_fin, smul_eq_mul]

/-! ### Lower bound -/

theorem le_of_good {n k : ℕ} (h₁ : k + 2 ≤ n) (h₂ : 2 * n ≤ 3 * k + 2)
    (G : SimpleGraph (Fin n)) [DecidableRel G.Adj] (hG : Good k G) :
    (n - k - 1) * (n + k - 2) ≤ 2 * #G.edgeFinset := by
  obtain ⟨J, rfl⟩ : ∃ J, n = k + 2 + J := ⟨n - (k + 2), by omega⟩
  have hc := claim (H := Gᶜ) (k + 1) J univ (by simp)
    (by omega) (fun S _ hS => not_twoSet_compl_of_good G hG S hS)
  have hs := two_mul_card_edges_add_D_compl G
  have e1 : k + 2 + J - k - 1 = J + 1 := by omega
  have e2 : k + 2 + J + k - 2 = 2 * k + J := by omega
  have e3 : k + 2 + J - 1 = k + 1 + J := by omega
  rw [e1, e2]
  rw [e3] at hs
  nlinarith

/-! ### The extremal graph -/

/-- `G₀`: edges between vertices `1,…,n-1`, except inside `{1,…,k}`. Its complement is a clique
on `{0,…,k}` with every other vertex joined only to `0`. -/
def G₀ (n k : ℕ) : SimpleGraph (Fin n) where
  Adj u v := u ≠ v ∧ u.val ≠ 0 ∧ v.val ≠ 0 ∧ (k < u.val ∨ k < v.val)
  symm := ⟨fun _ _ ⟨h1, h2, h3, h4⟩ => ⟨h1.symm, h3, h2, h4.symm⟩⟩
  loopless := ⟨fun _ ⟨h, _⟩ => h rfl⟩

instance (n k : ℕ) : DecidableRel (G₀ n k).Adj := fun u v => by
  unfold G₀; infer_instance

lemma card_val_le {n : ℕ} (s : Finset (Fin n)) (t : Finset ℕ) (h : ∀ v ∈ s, v.val ∈ t) :
    #s ≤ #t :=
  card_le_card_of_injOn (fun v => v.val) h (fun _ _ _ _ e => Fin.ext e)

lemma G₀_good {n k : ℕ} (_h₁ : k + 2 ≤ n) : Good k (G₀ n k) := by
  classical
  intro s hs
  -- some vertex of `s` has value `> k`
  obtain ⟨p, hp, hpk⟩ : ∃ p ∈ s, k < p.val := by
    by_contra hcon
    push_neg at hcon
    have := card_val_le s (range (k + 1)) (fun v hv => mem_range.mpr (by have := hcon v hv; omega))
    rw [card_range] at this
    omega
  refine ⟨⟨p, Finset.mem_coe.mpr hp⟩, ?_⟩
  rw [induce_degree_eq]
  show k ≤ #(s.filter ((G₀ n k).Adj p))
  -- `s.erase p` minus the (at most one) vertex with value `0` are all neighbours of `p`
  have hsub : (s.erase p).filter (fun w => ¬ w.val = 0) ⊆ s.filter ((G₀ n k).Adj p) := by
    intro w hw
    simp only [mem_filter, mem_erase] at hw
    refine mem_filter.mpr ⟨hw.1.2, ?_⟩
    exact ⟨fun e => hw.1.1 e.symm, by omega, hw.2, Or.inl hpk⟩
  have hzero : #((s.erase p).filter (fun w => w.val = 0)) ≤ 1 :=
    card_le_one.mpr fun a ha b hb => Fin.ext (by
      rw [(mem_filter.mp ha).2, (mem_filter.mp hb).2])
  have hsplit := card_filter_add_card_filter_not (s := s.erase p) (p := fun w => w.val = 0)
  have herase := card_erase_of_mem hp
  have := card_le_card hsub
  omega

lemma G₀_edges {n k : ℕ} (h₁ : k + 2 ≤ n) :
    2 * #(G₀ n k).edgeFinset ≤ (n - k - 1) * (n + k - 2) := by
  classical
  rw [← (G₀ n k).sum_degrees_eq_twice_card_edges]
  simp_rw [← SimpleGraph.card_neighborFinset_eq_degree, SimpleGraph.neighborFinset_eq_filter]
  -- split the vertices into `val = 0`, `1 ≤ val ≤ k`, `val > k`
  rw [← sum_filter_add_sum_filter_not univ (fun v : Fin n => k < v.val)]
  rw [← sum_filter_add_sum_filter_not (univ.filter fun v : Fin n => ¬ k < v.val)
    (fun v : Fin n => v.val = 0)]
  -- vertices with value 0 have no neighbours
  have h0 : ∑ v ∈ (univ.filter fun v : Fin n => ¬ k < v.val).filter (fun v => v.val = 0),
      #(univ.filter ((G₀ n k).Adj v)) = 0 := by
    apply sum_eq_zero
    intro v hv
    rw [card_eq_zero, filter_eq_empty_iff]
    intro w _ hadj
    exact hadj.2.1 (mem_filter.mp hv).2
  -- vertices with `1 ≤ val ≤ k`: at most `n-k-1` neighbours, and at most `k` such vertices
  have hmid : ∑ v ∈ (univ.filter fun v : Fin n => ¬ k < v.val).filter (fun v => ¬ v.val = 0),
      #(univ.filter ((G₀ n k).Adj v)) ≤ k * (n - k - 1) := by
    calc _ ≤ ∑ _v ∈ (univ.filter fun v : Fin n => ¬ k < v.val).filter (fun v => ¬ v.val = 0),
          (n - k - 1) := by
          apply sum_le_sum
          intro v hv
          simp only [mem_filter] at hv
          have := card_val_le (univ.filter ((G₀ n k).Adj v)) (Ico (k + 1) n) (fun w hw => by
            simp only [mem_filter] at hw
            obtain ⟨_, _, _, _, hor⟩ := hw
            have := w.isLt
            refine mem_Ico.mpr ⟨?_, this⟩
            rcases hor with h | h
            · exact absurd h hv.1.2
            · omega)
          rw [Nat.card_Ico] at this
          omega
      _ ≤ k * (n - k - 1) := by
          rw [sum_const, smul_eq_mul]
          apply Nat.mul_le_mul_right
          have := card_val_le ((univ.filter fun v : Fin n => ¬ k < v.val).filter
              (fun v => ¬ v.val = 0)) (Ico 1 (k + 1)) (fun w hw => by
            simp only [mem_filter] at hw
            exact mem_Ico.mpr ⟨by omega, by omega⟩)
          rw [Nat.card_Ico] at this
          omega
  -- vertices with `val > k`: at most `n-2` neighbours, and at most `n-k-1` such vertices
  have hbig : ∑ v ∈ univ.filter (fun v : Fin n => k < v.val),
      #(univ.filter ((G₀ n k).Adj v)) ≤ (n - k - 1) * (n - 2) := by
    calc _ ≤ ∑ _v ∈ univ.filter (fun v : Fin n => k < v.val), (n - 2) := by
          apply sum_le_sum
          intro v hv
          simp only [mem_filter] at hv
          have := card_val_le (univ.filter ((G₀ n k).Adj v)) (((range n).erase v.val).erase 0)
            (fun w hw => by
              simp only [mem_filter] at hw
              obtain ⟨_, hne, _, hw0, _⟩ := hw
              refine mem_erase.mpr ⟨hw0, mem_erase.mpr ⟨fun e => hne (Fin.ext e).symm,
                mem_range.mpr w.isLt⟩⟩)
          rw [card_erase_of_mem (mem_erase.mpr ⟨by omega, mem_range.mpr (by omega)⟩),
            card_erase_of_mem (mem_range.mpr v.isLt), card_range] at this
          omega
      _ ≤ (n - k - 1) * (n - 2) := by
          rw [sum_const, smul_eq_mul]
          apply Nat.mul_le_mul_right
          have := card_val_le (univ.filter (fun v : Fin n => k < v.val)) (Ico (k + 1) n)
            (fun w hw => by
              simp only [mem_filter] at hw
              exact mem_Ico.mpr ⟨by omega, w.isLt⟩)
          rw [Nat.card_Ico] at this
          omega
  rw [h0]
  obtain ⟨J, rfl⟩ : ∃ J, n = k + 2 + J := ⟨n - (k + 2), by omega⟩
  have e1 : k + 2 + J - k - 1 = J + 1 := by omega
  have e2 : k + 2 + J + k - 2 = 2 * k + J := by omega
  have e3 : k + 2 + J - 2 = k + J := by omega
  rw [e1, e2]
  rw [e1] at hmid
  rw [e1, e3] at hbig
  nlinarith

/-! ### Main theorem -/

open scoped Classical in
/-- **Erdős Problem 614 for `k + 2 ≤ n ≤ (3k+2)/2`:** `f(n,k) = (n-k-1)(n+k-2)/2`. -/
theorem f_eq (n k : ℕ) (h₁ : k + 2 ≤ n) (h₂ : 2 * n ≤ 3 * k + 2) :
    IsLeast (edgeCounts n k) ((n - k - 1) * (n + k - 2) / 2) := by
  constructor
  · refine ⟨G₀ n k, ?_, G₀_good h₁⟩
    rw [card_edgeFinset_inst (G₀ n k) _ (SimpleGraph.fintypeEdgeSet (G₀ n k))]
    have hlow := le_of_good h₁ h₂ (G₀ n k) (G₀_good h₁)
    have hup := G₀_edges (n := n) (k := k) h₁
    omega
  · rintro m ⟨G, rfl, hG⟩
    rw [card_edgeFinset_inst G _ (SimpleGraph.fintypeEdgeSet G)]
    have := le_of_good h₁ h₂ G hG
    omega

open scoped Classical in
/-- `f_eq` restated with the *verbatim* set-builder of google-deepmind/formal-conjectures
(`FormalConjectures/ErdosProblems/614.lean`, theorem `erdos_614`), restricted to our range. -/
theorem erdos_614_of_two_mul_le (n k : ℕ) (h₁ : k + 2 ≤ n) (h₂ : 2 * n ≤ 3 * k + 2) :
    IsLeast {m : ℕ | ∃ G : SimpleGraph (Fin n), G.edgeFinset.card = m ∧
      ∀ s : Finset (Fin n), s.card = k + 2 →
        ∃ v : s, k ≤ (G.induce (s : Set (Fin n))).degree v}
      ((n - k - 1) * (n + k - 2) / 2) :=
  f_eq n k h₁ h₂

/-! ### Statements that are *not* proved here (recorded as propositions, no `sorry`) -/

open scoped Classical in
/-- Erdős–Reid–Schelp–Staton Conjecture 1, specialised to Problem 614 (`j = 2`): the formula holds
for all `k + 2 ≤ n ≤ 2k`. Open; verified by computer for `n ≤ 10` (see `README.md`). -/
def ERSSConjecture614 : Prop :=
  ∀ n k : ℕ, k + 2 ≤ n → n ≤ 2 * k → IsLeast (edgeCounts n k) ((n - k - 1) * (n + k - 2) / 2)

end Conjectures.Erdos614
