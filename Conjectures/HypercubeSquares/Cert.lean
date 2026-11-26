/-
# Certificates: from a checked vertex list to a square-free Hamiltonian cycle

A cycle `0, v₁, …, v_{N-1}, 0` of `Q_n` is given as a list of natural numbers (bit `i` of a
number is coordinate `i`). `goodCycle` checks it with Boolean computations only;
`exists_of_goodCycle` turns a successful check into a Hamiltonian cycle of `cube n` with no
inscribed square.
-/
import Conjectures.HypercubeSquares.Main

namespace Conjectures.HypercubeSquares

open Finset

variable {n : ℕ}

/-- The vertex of `Q_n` encoded by `k`: coordinate `i` is bit `i` of `k`. -/
def toV (n k : ℕ) : Fin n → Bool := fun i => k.testBit i

lemma toV_xor (k d : ℕ) (hd : d < n) : toV n (k ^^^ 2 ^ d) = flip (toV n k) ⟨d, hd⟩ := by
  funext i
  by_cases h : i = ⟨d, hd⟩
  · subst h; simp [toV, flip]
  · have : d ≠ (i : ℕ) := fun e => h (Fin.ext e.symm)
    simp [toV, flip, Function.update_of_ne h, this]

lemma toV_inj {a b : ℕ} (ha : a < 2 ^ n) (hb : b < 2 ^ n) (h : toV n a = toV n b) : a = b := by
  apply Nat.eq_of_testBit_eq
  intro i
  by_cases hi : i < n
  · exact congrFun h ⟨i, hi⟩
  · have hle : 2 ^ n ≤ 2 ^ i := Nat.pow_le_pow_right (by omega) (not_lt.1 hi)
    rw [Nat.testBit_lt_two_pow (lt_of_lt_of_le ha hle),
      Nat.testBit_lt_two_pow (lt_of_lt_of_le hb hle)]

lemma flip_comm (u : Fin n → Bool) (i j : Fin n) : flip (flip u i) j = flip (flip u j) i := by
  funext k
  by_cases hi : k = i <;> by_cases hj : k = j
  · subst hi; subst hj; rfl
  · subst hi
    simp [flip, Function.update_of_ne hj, Function.update_of_ne (Ne.symm hj)]
  · subst hj
    simp [flip, Function.update_of_ne hi, Function.update_of_ne (Ne.symm hi)]
  · simp [flip, Function.update_of_ne hi, Function.update_of_ne hj]

lemma cube_adj_flip (u : Fin n → Bool) (i : Fin n) : (cube n).Adj u (flip u i) := by
  show (univ.filter fun k => u k ≠ flip u i k).card = 1
  rw [Finset.card_eq_one]
  refine ⟨i, ?_⟩
  ext k
  simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_singleton]
  by_cases h : k = i
  · subst h; simp [flip]
  · simp [flip, h]

/-- `b` is `a` with one of the first `n` bits flipped. -/
def step (n a b : ℕ) : Bool := (List.range n).any fun d => b == a ^^^ 2 ^ d

lemma adj_of_step {a b : ℕ} (h : step n a b = true) : (cube n).Adj (toV n a) (toV n b) := by
  obtain ⟨d, hd, rfl⟩ : ∃ d, d < n ∧ b = a ^^^ 2 ^ d := by simpa [step] using h
  rw [toV_xor _ _ hd]; exact cube_adj_flip _ _

/-- Every consecutive pair of `a :: l ++ [t]` is a cube step. -/
def stepsOK (n t : ℕ) : ℕ → List ℕ → Bool
  | a, [] => step n a t
  | a, b :: l => step n a b && stepsOK n t b l

/-- The consecutive pairs of `a :: l ++ [t]`. -/
def pairs (t : ℕ) : ℕ → List ℕ → List (ℕ × ℕ)
  | a, [] => [(a, t)]
  | a, b :: l => (a, b) :: pairs t b l

/-- The walk `a, l₁, …, l_k, t` of `cube n`. -/
def walkTo (n t : ℕ) : (a : ℕ) → (l : List ℕ) → stepsOK n t a l = true →
    (cube n).Walk (toV n a) (toV n t)
  | a, [], h => .cons (adj_of_step (by simpa [stepsOK] using h)) .nil
  | a, b :: l, h =>
    have h' : step n a b = true ∧ stepsOK n t b l = true := by simpa [stepsOK] using h
    .cons (adj_of_step h'.1) (walkTo n t b l h'.2)

lemma walkTo_support (t a : ℕ) (l : List ℕ) (h) :
    (walkTo n t a l h).support = (a :: (l ++ [t])).map (toV n) := by
  induction l generalizing a with
  | nil => simp [walkTo]
  | cons b l ih => simp [walkTo, ih]

lemma walkTo_edges (t a : ℕ) (l : List ℕ) (h) :
    (walkTo n t a l h).edges = (pairs t a l).map fun p => s(toV n p.1, toV n p.2) := by
  induction l generalizing a with
  | nil => simp [walkTo, pairs]
  | cons b l ih => simp [walkTo, pairs, ih]

lemma walkTo_length (t a : ℕ) (l : List ℕ) (h) : (walkTo n t a l h).length = l.length + 1 := by
  induction l generalizing a with
  | nil => simp [walkTo]
  | cons b l ih => simp [walkTo, ih]

lemma mem_pairs {t a : ℕ} {l : List ℕ} {p : ℕ × ℕ} (hp : p ∈ pairs t a l) :
    p.1 ∈ a :: (l ++ [t]) ∧ p.2 ∈ a :: (l ++ [t]) := by
  induction l generalizing a with
  | nil => simp [pairs] at hp; subst hp; simp
  | cons b l ih =>
    simp only [pairs, List.mem_cons] at hp
    rcases hp with rfl | hp
    · simp
    · have := ih hp; simp_all

/-- Unordered equality of two pairs. -/
def symEq (p q : ℕ × ℕ) : Bool := (p.1 == q.1 && p.2 == q.2) || (p.1 == q.2 && p.2 == q.1)

def nodupB : List ℕ → Bool
  | [] => true
  | a :: l => !(l.contains a) && nodupB l

lemma nodup_of_nodupB {l : List ℕ} (h : nodupB l = true) : l.Nodup := by
  induction l with
  | nil => simp
  | cons a l ih => simp [nodupB] at h; exact List.nodup_cons.2 ⟨h.1, ih h.2⟩

/-- A code for the unordered pair `{a, b}` that does not depend on the order. -/
def edgeIdx (n : ℕ) (p : ℕ × ℕ) : ℕ := (p.1 ^^^ p.2) * 2 ^ n + (p.1 &&& p.2)

lemma edgeIdx_of_symEq {p q : ℕ × ℕ} (h : symEq p q = true) : edgeIdx n p = edgeIdx n q := by
  simp only [symEq, Bool.or_eq_true, Bool.and_eq_true, beq_iff_eq] at h
  rcases h with ⟨h1, h2⟩ | ⟨h1, h2⟩
  · simp [edgeIdx, h1, h2]
  · simp [edgeIdx, h1, h2, Nat.xor_comm, Nat.and_comm]

/-- A bitmask with bit `edgeIdx n q` set for each `q ∈ P`. -/
def mask (n : ℕ) (P : List (ℕ × ℕ)) : ℕ := P.foldr (fun q m => m ||| 2 ^ edgeIdx n q) 0

lemma testBit_mask {P : List (ℕ × ℕ)} {q : ℕ × ℕ} (hq : q ∈ P) :
    (mask n P).testBit (edgeIdx n q) = true := by
  induction P with
  | nil => simp at hq
  | cons a P ih =>
    simp only [mask, List.foldr_cons] at ih ⊢
    rw [Nat.testBit_or]
    rcases List.mem_cons.1 hq with rfl | hq
    · simp
    · simp [ih hq]

/-- No direction-`i` edge `p` has its translate by a different direction `j` in `P`. -/
def squareFreeB (n : ℕ) (P : List (ℕ × ℕ)) : Bool :=
  let M := mask n P
  P.all fun p => (List.range n).all fun j =>
    (p.1 ^^^ p.2 == 2 ^ j) || !(M.testBit (edgeIdx n (p.1 ^^^ 2 ^ j, p.2 ^^^ 2 ^ j)))

/-- The full check on the cycle `0, v₁, rest…, 0`. -/
def goodCycle (n v₁ : ℕ) (rest : List ℕ) : Bool :=
  (v₁ :: (rest ++ [0])).all (· < 2 ^ n) &&
  nodupB (v₁ :: (rest ++ [0])) &&
  (rest.length + 2 == 2 ^ n) &&
  stepsOK n 0 0 (v₁ :: rest) &&
  (pairs 0 v₁ rest).all (fun q => !symEq q (0, v₁)) &&
  squareFreeB n (pairs 0 0 (v₁ :: rest))

lemma toV_pair_eq {a b c d : ℕ} (ha : a < 2 ^ n) (hb : b < 2 ^ n) (hc : c < 2 ^ n)
    (hd : d < 2 ^ n) (h : s(toV n a, toV n b) = s(toV n c, toV n d)) : symEq (a, b) (c, d) = true := by
  rcases Sym2.eq_iff.1 h with ⟨h1, h2⟩ | ⟨h1, h2⟩
  · simp [symEq, toV_inj ha hc h1, toV_inj hb hd h2]
  · simp [symEq, toV_inj ha hd h1, toV_inj hb hc h2]

lemma xor_xor_cancel (a c : ℕ) : a ^^^ (a ^^^ c) = c := by
  rw [← Nat.xor_assoc, Nat.xor_self, Nat.zero_xor]

theorem exists_of_goodCycle {v₁ : ℕ} {rest : List ℕ} (hg : goodCycle n v₁ rest = true) :
    ∃ c : (cube n).Walk (toV n 0) (toV n 0), c.IsHamiltonianCycle ∧ ¬ HasInscribedSquare c := by
  simp only [goodCycle, Bool.and_eq_true, beq_iff_eq] at hg
  obtain ⟨⟨⟨⟨⟨hbound, hnd⟩, hlen⟩, hsteps⟩, hfirst⟩, hsq⟩ := hg
  have hb : ∀ x ∈ (0 :: (v₁ :: (rest ++ [0]))), x < 2 ^ n := by
    intro x hx
    simp only [List.all_eq_true, decide_eq_true_eq] at hbound
    rcases List.mem_cons.1 hx with rfl | hx
    · exact Nat.two_pow_pos n
    · exact hbound x hx
  have hbP : ∀ p ∈ pairs 0 0 (v₁ :: rest), p.1 < 2 ^ n ∧ p.2 < 2 ^ n := by
    intro p hp; have := mem_pairs hp
    exact ⟨hb _ (by simpa using this.1), hb _ (by simpa using this.2)⟩
  refine ⟨walkTo n 0 0 (v₁ :: rest) hsteps, ?_, ?_⟩
  · -- Hamiltonian cycle
    rw [SimpleGraph.Walk.isHamiltonianCycle_iff_isCycle_and_length_eq]
    refine ⟨?_, ?_⟩
    · simp only [walkTo]
      rw [SimpleGraph.Walk.cons_isCycle_iff]
      refine ⟨?_, ?_⟩
      · rw [SimpleGraph.Walk.isPath_def, walkTo_support]
        refine (nodup_of_nodupB hnd).map_on ?_
        intro x hx y hy hxy
        exact toV_inj (hb x (List.mem_cons_of_mem _ hx)) (hb y (List.mem_cons_of_mem _ hy)) hxy
      · rw [walkTo_edges]
        intro hmem
        obtain ⟨q, hq, hqe⟩ := List.mem_map.1 hmem
        have hqb := mem_pairs hq
        have hq1 := hb q.1 (List.mem_cons_of_mem _ hqb.1)
        have hq2 := hb q.2 (List.mem_cons_of_mem _ hqb.2)
        have := toV_pair_eq hq1 hq2 (Nat.two_pow_pos n) (hb v₁ (by simp)) hqe
        simp only [List.all_eq_true, Bool.not_eq_true'] at hfirst
        rw [hfirst q hq] at this; exact absurd this (by simp)
    · rw [walkTo_length]; simp [hlen]
  · -- no inscribed square
    rintro ⟨u, i, j, hij, h1, h2⟩
    rw [walkTo_edges] at h1 h2
    obtain ⟨p, hp, hpe⟩ := List.mem_map.1 h1
    obtain ⟨hp1, hp2⟩ := hbP p hp
    have hi2 : 2 ^ (i : ℕ) < 2 ^ n := Nat.pow_lt_pow_right (by omega) i.2
    have hj2 : 2 ^ (j : ℕ) < 2 ^ n := Nat.pow_lt_pow_right (by omega) j.2
    -- in either orientation, `p` is a direction-`i` edge whose `j`-translate is in the cycle
    have key : p.1 ^^^ p.2 = 2 ^ (i : ℕ) ∧
        s(toV n (p.1 ^^^ 2 ^ (j : ℕ)), toV n (p.2 ^^^ 2 ^ (j : ℕ))) ∈
          (pairs 0 0 (v₁ :: rest)).map fun p => s(toV n p.1, toV n p.2) := by
      rcases Sym2.eq_iff.1 hpe with ⟨e1, e2⟩ | ⟨e1, e2⟩
      · -- u = toV p.1, flip u i = toV p.2
        subst e1
        have : p.2 = p.1 ^^^ 2 ^ (i : ℕ) :=
          toV_inj hp2 (Nat.xor_lt_two_pow hp1 hi2) (by rw [e2, toV_xor _ _ i.2])
        refine ⟨by rw [this, xor_xor_cancel], ?_⟩
        rw [toV_xor _ _ j.2, toV_xor _ _ j.2, this, toV_xor _ _ i.2]
        rw [← flip_comm] at h2
        exact h2
      · -- u = toV p.2, flip u i = toV p.1
        subst e2
        have : p.1 = p.2 ^^^ 2 ^ (i : ℕ) :=
          toV_inj hp1 (Nat.xor_lt_two_pow hp2 hi2) (by rw [e1, toV_xor _ _ i.2])
        refine ⟨by rw [this, Nat.xor_comm, xor_xor_cancel], ?_⟩
        rw [Sym2.eq_swap, toV_xor _ _ j.2, toV_xor _ _ j.2, this, toV_xor _ _ i.2]
        rw [← flip_comm] at h2
        exact h2
    obtain ⟨hxor, hmem⟩ := key
    obtain ⟨q, hq, hqe⟩ := List.mem_map.1 hmem
    obtain ⟨hq1, hq2⟩ := hbP q hq
    have hsym := toV_pair_eq hq1 hq2 (Nat.xor_lt_two_pow hp1 hj2) (Nat.xor_lt_two_pow hp2 hj2) hqe
    simp only [squareFreeB, List.all_eq_true, List.mem_range, Bool.or_eq_true, beq_iff_eq,
      Bool.not_eq_true'] at hsq
    rcases hsq p hp j j.2 with h | h
    · exact hij (Fin.ext (Nat.pow_right_injective (le_refl 2) (hxor.symm.trans h)))
    · have := testBit_mask (n := n) hq
      rw [edgeIdx_of_symEq hsym, h] at this
      exact absurd this (by simp)

end Conjectures.HypercubeSquares
