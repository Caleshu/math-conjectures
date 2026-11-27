/-
# Chip-firing on `Q_6`: rank-0 certificates

Vertices of `Q_6` are `0 ≤ v < 64`; bit `k` is coordinate `k`, so the neighbours of `v` are
`v ^^^ 2^k`. A *divisor* is `D : ℕ → ℤ` (only `D v` for `v < 64` matters).

* `D ~ F` (`Equiv D F`) iff `F = D - L z` for some firing script `z`, where `L` is the
  Laplacian. This is the usual linear equivalence of divisors.
* `D` has *positive rank* (`PosRank D`) iff for every vertex `q`, `D - q` is equivalent to an
  effective divisor.

`certOK D q z ord` is a Boolean check that `E := D - L z` is effective, `E q = 0`, and `ord`
is a Dhar burning order for `E` from `q`: every vertex, when it burns, has fewer chips than
burnt neighbours. `not_posRank_of_certOK` proves that such a certificate shows `D` does not
have positive rank (the standard argument: fire the set where a firing script is maximal).
-/
import Mathlib

namespace GonalityQ6

/-- The six neighbours of `v` in `Q_6`. -/
def nbrs (v : ℕ) : List ℕ := [v ^^^ 1, v ^^^ 2, v ^^^ 4, v ^^^ 8, v ^^^ 16, v ^^^ 32]

/-- The Laplacian: `(L z)(u) = Σ_{w ~ u} (z u - z w)`. -/
def lap (z : ℕ → ℤ) (u : ℕ) : ℤ := ((nbrs u).map fun w => z u - z w).sum

/-- Linear equivalence: `F = D - L z` on `V(Q_6)` for some firing script `z`. -/
def Equiv (D F : ℕ → ℤ) : Prop := ∃ z : ℕ → ℤ, ∀ u < 64, F u = D u - lap z u

/-- `F` is effective. -/
def Eff (F : ℕ → ℤ) : Prop := ∀ u < 64, 0 ≤ F u

/-- `D - q`. -/
def subPt (D : ℕ → ℤ) (q : ℕ) : ℕ → ℤ := fun u => D u - if u = q then 1 else 0

/-- `D` has positive rank: for every vertex `q`, `D - q` is equivalent to an effective divisor. -/
def PosRank (D : ℕ → ℤ) : Prop := ∀ q < 64, ∃ F, Eff F ∧ Equiv (subPt D q) F

/-- The certificate check described in the module docstring. -/
def certOK (D : ℕ → ℤ) (q : ℕ) (z : List ℤ) (ord : List ℕ) : Bool :=
  let E : ℕ → ℤ := fun u => D u - lap (fun x => z.getD x 0) u
  decide (q < 64) && decide (E q = 0) && (List.range 64).all (fun u => decide (0 ≤ E u)) &&
  (ord.length == 64) && ord.all (· < 64) && (List.range 64).all (fun u => ord.contains u) &&
  (ord.head? == some q) &&
  (List.range 63).all fun j =>
    decide (E (ord.getD (j + 1) 0) <
      ((nbrs (ord.getD (j + 1) 0)).countP fun x => (ord.take (j + 1)).contains x : ℕ))

lemma nbrs_lt {u x : ℕ} (hu : u < 64) (hx : x ∈ nbrs u) : x < 64 := by
  simp only [nbrs, List.mem_cons, List.not_mem_nil, or_false] at hx
  have h : ∀ k ≤ 5, u ^^^ 2 ^ k < 64 := fun k hk =>
    Nat.xor_lt_two_pow (n := 6) hu (lt_of_le_of_lt (Nat.pow_le_pow_right (by norm_num) hk)
      (by norm_num))
  rcases hx with rfl | rfl | rfl | rfl | rfl | rfl
  · exact h 0 (by norm_num)
  · exact h 1 (by norm_num)
  · exact h 2 (by norm_num)
  · exact h 3 (by norm_num)
  · exact h 4 (by norm_num)
  · exact h 5 (by norm_num)

lemma lap_sub (y z : ℕ → ℤ) (u : ℕ) : lap y u - lap z u = lap (fun x => y x - z x) u := by
  simp only [lap, nbrs, List.map_cons, List.map_nil, List.sum_cons, List.sum_nil]; ring

/-- At a maximum of `w`, the Laplacian is at least the number of neighbours below the maximum. -/
lemma countP_le_sum {w : ℕ → ℤ} {M : ℤ} (u : ℕ) (hu : w u = M) :
    ∀ l : List ℕ, (∀ x ∈ l, w x ≤ M) →
      ((l.countP fun x => decide (w x ≠ M) : ℕ) : ℤ) ≤ (l.map fun x => w u - w x).sum
  | [], _ => by simp
  | x :: l, h => by
    have ih := countP_le_sum u hu l (fun y hy => h y (List.mem_cons_of_mem _ hy))
    have hx := h x (List.mem_cons_self ..)
    rw [List.map_cons, List.sum_cons]
    by_cases hxM : w x = M
    · rw [List.countP_cons_of_neg (by simp [hxM])]
      have : 0 ≤ w u - w x := by rw [hu]; linarith
      linarith
    · rw [List.countP_cons_of_pos (by simp [hxM])]
      have : 1 ≤ w u - w x := by have := lt_of_le_of_ne hx hxM; rw [hu]; omega
      push_cast; linarith

theorem not_posRank_of_certOK {D : ℕ → ℤ} {q : ℕ} {z : List ℤ} {ord : List ℕ}
    (h : certOK D q z ord = true) : ¬ PosRank D := by
  simp only [certOK, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq, List.all_eq_true,
    List.mem_range, List.contains_iff_mem] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨hq, hEq⟩, hEff⟩, hlen⟩, hlt⟩, hall⟩, hhead⟩, hburn⟩ := h
  set z0 : ℕ → ℤ := fun x => z.getD x 0
  set E : ℕ → ℤ := fun u => D u - lap z0 u
  intro hpos
  obtain ⟨F, hF, y, hy⟩ := hpos q hq
  set w : ℕ → ℤ := fun x => y x - z0 x
  -- `F = E - q - L w`
  have hFE : ∀ u < 64, F u = E u - (if u = q then 1 else 0) - lap w u := by
    intro u hu
    rw [hy u hu, ← lap_sub]
    simp only [subPt, E]; ring
  -- a maximum `M` of `w`
  obtain ⟨m, hm, hmax⟩ := Finset.exists_max_image (Finset.range 64) w ⟨q, Finset.mem_range.2 hq⟩
  set M := w m
  have hle : ∀ x < 64, w x ≤ M := fun x hx => hmax x (Finset.mem_range.2 hx)
  -- at a vertex `u` where `w` is maximal, `#(neighbours below M) ≤ L w u ≤ E u - [u = q]`
  have key : ∀ u < 64, w u = M →
      ((nbrs u).countP fun x => decide (w x ≠ M) : ℤ) + (if u = q then 1 else 0) ≤ E u := by
    intro u hu hwu
    have h1 := countP_le_sum u hwu (nbrs u) (fun x hx => hle x (nbrs_lt hu hx))
    have h2 := hF u hu
    rw [hFE u hu] at h2
    simp only [lap] at h2
    omega
  -- `w q < M`, since `E q = 0`
  have hwq : w q ≠ M := by
    intro hwq
    have h1 := key q hq hwq
    rw [if_pos rfl] at h1
    have h2 : E q = 0 := hEq
    have := Nat.cast_nonneg (α := ℤ) ((nbrs q).countP fun x => decide (w x ≠ M))
    linarith
  -- the first vertex of the burning order where `w` is maximal
  have hex : ∃ x ∈ ord, decide (w x = M) = true :=
    ⟨m, hall m (Finset.mem_range.1 hm), by simp [M]⟩
  have hi : ord.findIdx (fun x => decide (w x = M)) < ord.length :=
    List.findIdx_lt_length_of_exists hex
  set i := ord.findIdx (fun x => decide (w x = M)) with hidef
  have gget : ∀ k (hk : k < ord.length), ord.getD k 0 = ord[k] := fun k hk => by
    rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hk]; rfl
  have hwi : w (ord.getD i 0) = M := by
    rw [gget i hi]; simpa using List.findIdx_getElem (w := hi)
  have hbefore : ∀ k, k < i → w (ord.getD k 0) ≠ M := by
    intro k hk
    have hk' : k < ord.length := lt_trans hk hi
    rw [gget k hk']; simpa using List.not_of_lt_findIdx hk
  have hq0 : ord.getD 0 0 = q := by
    cases ord with
    | nil => simp at hlen
    | cons a l => simp at hhead; simp [hhead]
  have hi0 : i ≠ 0 := by
    intro h0
    have : ord.getD i 0 = q := by rw [h0]; exact hq0
    exact hwq (this ▸ hwi)
  obtain ⟨j, hj⟩ : ∃ j, i = j + 1 := ⟨i - 1, by omega⟩
  have hb := hburn j (by omega)
  rw [← hj] at hb
  set u := ord.getD i 0 with hudef
  have hu : u < 64 := hlt u (by rw [hudef, gget i hi]; exact List.getElem_mem _)
  -- every vertex burnt before `u` has `w < M`
  have hcount : (nbrs u).countP (fun x => (ord.take i).contains x) ≤
      (nbrs u).countP (fun x => decide (w x ≠ M)) := by
    apply List.countP_mono_left
    intro x _ hx
    simp only [List.contains_iff_mem, decide_eq_true_eq] at hx ⊢
    obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hx
    rw [List.length_take] at hk
    rw [List.getElem_take]
    have := hbefore k (by omega)
    rwa [gget k (by omega)] at this
  have h1 := key u hu hwi
  have hc : ((nbrs u).countP (fun x => (ord.take i).contains x) : ℤ) ≤
      ((nbrs u).countP (fun x => decide (w x ≠ M)) : ℤ) := by exact_mod_cast hcount
  have : (0 : ℤ) ≤ if u = q then 1 else 0 := by split_ifs <;> norm_num
  have hEu : E u = D u - lap z0 u := rfl
  linarith

end GonalityQ6
