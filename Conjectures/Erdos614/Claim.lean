/-
# Erdős Problem 614 — the main extremal claim (complement form)

`claim`: let `m = M+1`, `J ≥ 0` with `2J + 4 ≤ m`, and let `U` be a set of `m + J` vertices of a
graph `H` such that no `m`-subset of `U` is a 2-set. Then `D(U) + M ≤ M² + 2J + 2`, i.e.
`e(H[U]) ≤ C(m-1,2) + J + 1`.  See `PROOF.md` for the human-readable proof.
-/
import Conjectures.Erdos614.Basic
import Conjectures.Erdos614.Arith

set_option linter.unusedSectionVars false

namespace Conjectures.Erdos614

open Finset

variable {V : Type*} [DecidableEq V] {H : SimpleGraph V} [DecidableRel H.Adj]

lemma D_le' (S : Finset V) : D H S + #S ≤ #S * #S := by
  have h1 := D_le (H := H) S
  have h2 := mul_pred_add_self #S
  omega

/-- **Fact A.** A vertex of degree `≥ J+2` in `U` has `≥ 2` neighbours in any `S ⊆ U` that misses
only `J` vertices of `U`. -/
lemma two_le_degIn_of_free {U S : Finset V} {J : ℕ} (hSU : S ⊆ U) (hcard : #U = #S + J)
    {v : V} (_hv : v ∈ S) (hdeg : J + 2 ≤ degIn H U v) : 2 ≤ degIn H S v := by
  have hdisj : Disjoint S (U \ S) := disjoint_sdiff
  have h1 : degIn H U v = degIn H S v + degIn H (U \ S) v := by
    rw [← degIn_union hdisj v, union_sdiff_of_subset hSU]
  have h2 := degIn_le_card (H := H) (U \ S) v
  rw [card_sdiff_of_subset hSU] at h2
  omega

/-- **Main case** (`δ(H[U]) ≥ 2`, `J ≥ 1`). -/
theorem main_case (M J : ℕ) (U : Finset V) (hU : #U = M + 1 + J) (hJ : 1 ≤ J)
    (hM : 2 * J + 3 ≤ M) (hdeg : ∀ v ∈ U, 2 ≤ degIn H U v)
    (hno : ∀ S ⊆ U, #S = M + 1 → ¬ TwoSet H S) :
    D H U + M ≤ M * M + 2 * J + 2 := by
  set F := U.filter (fun v => J + 2 ≤ degIn H U v) with hF
  set L := U.filter (fun v => ¬ J + 2 ≤ degIn H U v) with hL
  have hFU : F ⊆ U := filter_subset _ _
  have hLU : L ⊆ U := filter_subset _ _
  have hdisjFL : Disjoint F L := disjoint_filter_filter_not _ _ _
  have hUFL : F ∪ L = U := filter_union_filter_not_eq _ _
  have hcardFL : #F + #L = #U := card_filter_add_card_filter_not _
  have hLdeg : ∀ w ∈ L, degIn H U w ≤ J + 1 := fun w hw => by
    have := (mem_filter.mp hw).2
    omega
  have hFdeg : ∀ v ∈ F, J + 2 ≤ degIn H U v := fun v hv => (mem_filter.mp hv).2
  -- Fact B: gluing
  have glue : ∀ W Y : Finset V, W ⊆ L → Y ⊆ F → #W + #Y ≤ M + 1 → M + 1 ≤ #W + #F →
      (∀ w ∈ W, 2 ≤ degIn H (W ∪ Y) w) → False := by
    intro W Y hWL hYF hle hge hW
    have hYle : #Y ≤ #F := card_le_card hYF
    obtain ⟨Y', hY'sub, hY'card⟩ :=
      exists_subset_card_eq (s := F \ Y) (n := M + 1 - #W - #Y)
        (by rw [card_sdiff_of_subset hYF]; omega)
    have hY'F : Y' ⊆ F := hY'sub.trans sdiff_subset
    have hdYY' : Disjoint Y Y' := disjoint_of_subset_right hY'sub disjoint_sdiff
    have hdW : Disjoint W (Y ∪ Y') :=
      disjoint_of_subset_left hWL
        (disjoint_of_subset_right (union_subset hYF hY'F) hdisjFL.symm)
    have hSU : W ∪ (Y ∪ Y') ⊆ U :=
      union_subset (hWL.trans hLU) (union_subset (hYF.trans hFU) (hY'F.trans hFU))
    have hScard : #(W ∪ (Y ∪ Y')) = M + 1 := by
      rw [card_union_of_disjoint hdW, card_union_of_disjoint hdYY', hY'card]
      omega
    apply hno _ hSU hScard
    intro v hv
    rcases mem_union.mp hv with hvW | hvY
    · calc 2 ≤ degIn H (W ∪ Y) v := hW v hvW
        _ ≤ degIn H (W ∪ (Y ∪ Y')) v :=
          degIn_mono (union_subset_union subset_rfl subset_union_left) v
    · exact two_le_degIn_of_free hSU (by omega) hv (hFdeg v (union_subset hYF hY'F hvY))
  -- `f ≤ M`
  have hf : #F ≤ M := by
    by_contra hcon
    obtain ⟨Y, hYF, hYcard⟩ := exists_subset_card_eq (s := F) (n := M + 1) (by omega)
    exact glue ∅ Y (empty_subset _) hYF (by simp [hYcard]) (by simp; omega) (by simp)
  obtain ⟨a, hfa⟩ : ∃ a, #F + a = M := ⟨M - #F, by omega⟩
  have hLc : #L = J + 1 + a := by omega
  -- Fact C: at most `a` good vertices
  have hgood : #(L.filter (fun w => 2 ≤ degIn H F w)) ≤ a := by
    by_contra hcon
    obtain ⟨W, hWg, hWcard⟩ :=
      exists_subset_card_eq (s := L.filter (fun w => 2 ≤ degIn H F w)) (n := a + 1) (by omega)
    refine glue W F (hWg.trans (filter_subset _ _)) subset_rfl (by omega) (by omega) ?_
    intro w hw
    calc 2 ≤ degIn H F w := (mem_filter.mp (hWg hw)).2
      _ ≤ degIn H (W ∪ F) w := degIn_mono subset_union_right w
  -- bound on `X = ∑_{w ∈ L} deg_F(w)`
  have hX : (∑ w ∈ L, degIn H F w) + #(L.filter (fun w => 2 ≤ degIn H F w)) ≤
      #(L.filter (fun w => 2 ≤ degIn H F w)) * min #F (J + 1) + #L := by
    rw [← sum_filter_add_sum_filter_not L (fun w => 2 ≤ degIn H F w)]
    have hc := card_filter_add_card_filter_not (s := L) (p := fun w => 2 ≤ degIn H F w)
    have hA : ∑ w ∈ L.filter (fun w => 2 ≤ degIn H F w), degIn H F w ≤
        #(L.filter (fun w => 2 ≤ degIn H F w)) * min #F (J + 1) := by
      calc ∑ w ∈ L.filter (fun w => 2 ≤ degIn H F w), degIn H F w
          ≤ ∑ _w ∈ L.filter (fun w => 2 ≤ degIn H F w), min #F (J + 1) :=
            sum_le_sum fun w hw => le_min (degIn_le_card _ _)
              (le_trans (degIn_mono hFU w) (hLdeg w (mem_filter.mp hw).1))
        _ = _ := by simp
    have hB : ∑ w ∈ L.filter (fun w => ¬ 2 ≤ degIn H F w), degIn H F w ≤
        #(L.filter (fun w => ¬ 2 ≤ degIn H F w)) := by
      calc ∑ w ∈ L.filter (fun w => ¬ 2 ≤ degIn H F w), degIn H F w
          ≤ ∑ _w ∈ L.filter (fun w => ¬ 2 ≤ degIn H F w), 1 :=
            sum_le_sum fun w hw => by
              have := (mem_filter.mp hw).2
              omega
        _ = _ := by simp
    omega
  -- degree-sum decompositions
  have hsplitU : ∀ w, degIn H U w = degIn H F w + degIn H L w := fun w => by
    rw [← degIn_union hdisjFL w, hUFL]
  have hcomm := sum_degIn_comm (H := H) F L
  have hDU : D H U = D H F + 2 * (∑ w ∈ L, degIn H F w) + D H L := by
    have e1 : D H U = ∑ v ∈ F, degIn H U v + ∑ v ∈ L, degIn H U v := by
      unfold D
      conv_lhs => rw [← hUFL]
      rw [sum_union hdisjFL, hUFL]
    rw [e1]
    unfold D
    simp only [hsplitU, sum_add_distrib]
    omega
  have hsumL : ∑ w ∈ L, degIn H U w = ∑ w ∈ L, degIn H F w + D H L := by
    unfold D
    rw [← sum_add_distrib]
    exact sum_congr rfl fun w _ => hsplitU w
  have hY : ∑ w ∈ L, degIn H U w ≤ (J + 1) * #L := by
    calc ∑ w ∈ L, degIn H U w ≤ ∑ _w ∈ L, (J + 1) := sum_le_sum hLdeg
      _ = (J + 1) * #L := by rw [sum_const, smul_eq_mul, Nat.mul_comm]
  have hDF := D_le' (H := H) F
  -- the three cases
  rcases Nat.eq_zero_or_pos a with ha0 | hapos
  · -- `a = 0`: glue all of `L` together with its `F`-neighbours
    exfalso
    have hg0 : #(L.filter (fun w => 2 ≤ degIn H F w)) = 0 := by omega
    rw [hg0, Nat.zero_mul] at hX
    have hYle : #(F.filter (fun y => ∃ w ∈ L, H.Adj w y)) ≤ ∑ w ∈ L, degIn H F w := by
      calc #(F.filter (fun y => ∃ w ∈ L, H.Adj w y))
          ≤ #(L.biUnion (fun w => F.filter (H.Adj w))) := by
            apply card_le_card
            intro y hy
            obtain ⟨hyF, w, hwL, hwy⟩ := mem_filter.mp hy
            exact mem_biUnion.mpr ⟨w, hwL, mem_filter.mpr ⟨hyF, hwy⟩⟩
        _ ≤ ∑ w ∈ L, #(F.filter (H.Adj w)) := card_biUnion_le
        _ = ∑ w ∈ L, degIn H F w := rfl
    refine glue L (F.filter (fun y => ∃ w ∈ L, H.Adj w y)) subset_rfl (filter_subset _ _)
      (by omega) (by omega) ?_
    intro w hw
    calc 2 ≤ degIn H U w := hdeg w (hLU hw)
      _ ≤ degIn H (L ∪ F.filter (fun y => ∃ w ∈ L, H.Adj w y)) w := by
        apply card_le_card
        intro u hu
        rw [mem_filter] at hu ⊢
        refine ⟨?_, hu.2⟩
        have huU := hu.1
        rw [← hUFL] at huU
        rcases mem_union.mp huU with huF | huL
        · exact mem_union_right _ (mem_filter.mpr ⟨huF, w, hw, hu.2⟩)
        · exact mem_union_left _ huL
  · rcases le_or_gt a J with haJ | haJ
    · -- Case I: `1 ≤ a ≤ J`, use the peeling lemma on `L`
      have hpeel := D_le_of_twoSets_le (H := H) a L (fun T hTL h2 => by
        by_contra hcon
        have hTc : #T ≤ #L := card_le_card hTL
        exact glue T ∅ hTL (empty_subset _) (by simp; omega) (by simp; omega)
          (fun w hw => by rw [union_empty]; exact h2 w hw))
      have hDL : D H L + 3 * a ≤ a * a + 2 * #L :=
        le_trans (Nat.add_le_add_right hpeel _) (max_peel_le a #L hapos (by omega))
      have key := arith_caseI J #F a _ (min #F (J + 1)) #L _ _ _ (by omega) hLc hapos haJ
        hgood (min_le_right _ _) hX hDF hDL
      rw [hfa] at key
      omega
    · -- Case II: `a ≥ J+1`
      have key := arith_caseII J #F a _ (min #F (J + 1)) #L _ _ _ (by omega) hLc (by omega)
        hgood (min_le_right _ _) (min_le_left _ _) hX hDF hY
      rw [hfa] at key
      omega

/-- **Main claim**, by induction on `J`. -/
theorem claim (M : ℕ) : ∀ (J : ℕ) (U : Finset V), #U = M + 1 + J → 2 * J + 3 ≤ M →
    (∀ S ⊆ U, #S = M + 1 → ¬ TwoSet H S) → D H U + M ≤ M * M + 2 * J + 2 := by
  intro J
  induction J with
  | zero =>
    intro U hU _ hno
    have hnot := hno U subset_rfl (by omega)
    unfold TwoSet at hnot
    push_neg at hnot
    obtain ⟨v, hv, hdeg⟩ := hnot
    rw [D_erase hv]
    have h1 := D_le' (H := H) (U.erase v)
    have h2 := card_erase_of_mem hv
    rw [show #(U.erase v) = M by omega] at h1
    omega
  | succ J ih =>
    intro U hU hM hno
    by_cases hlow : ∃ v ∈ U, degIn H U v ≤ 1
    · obtain ⟨v, hv, hdeg⟩ := hlow
      have h2 := card_erase_of_mem hv
      have hrec := ih (U.erase v) (by omega) (by omega)
        (fun S hS hc => hno S (hS.trans (erase_subset v U)) hc)
      rw [D_erase hv]
      omega
    · push_neg at hlow
      exact main_case M (J + 1) U hU (by omega) hM (fun v hv => by have := hlow v hv; omega) hno

end Conjectures.Erdos614
