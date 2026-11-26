/-
# Erdős Problem 614 — the two counting inequalities

Purely arithmetic facts that close the two counting cases of the main proof
(`PROOF.md`, Cases I and II). Everything is stated without natural-number subtraction.
Variables: `M = m-1 = f + a` (so `m = k+2`), `J ≥ 1` vertices to delete, `f = |F|`,
`L = |Lo| = J+1+a`, `g` = number of good vertices (`g ≤ a`), `s` = max number of
`F`-neighbours of an `Lo`-vertex, `X = ∑_{w∈Lo} deg_F(w)`, `DF = D(F)`, `DL = D(Lo)`,
`Y = ∑_{w∈Lo} deg_U(w)`. The target `D(U) + M ≤ M² + 2J + 2` is
`D(U) ≤ (m-1)(m-2) + 2J + 2`, i.e. `e(H) ≤ C(m-1,2) + J + 1`.
-/
import Mathlib.Tactic.Linarith
import Mathlib.Order.MinMax

namespace Conjectures.Erdos614

/-- `f(f-1) + f = f²` in `ℕ`. -/
theorem mul_pred_add_self (f : ℕ) : f * (f - 1) + f = f * f := by
  cases f with
  | zero => simp
  | succ f => simp [Nat.mul_succ]

/-- The peeling bound simplifies for `1 ≤ a ≤ L`:
`max (2(L-1)) (a(a-1) + 2(L-a)) + 3a ≤ a² + 2L`. -/
theorem max_peel_le (a L : ℕ) (ha : 1 ≤ a) (haL : a ≤ L) :
    max (2 * (L - 1)) (a * (a - 1) + 2 * (L - a)) + 3 * a ≤ a * a + 2 * L := by
  obtain ⟨b, rfl⟩ : ∃ b, a = b + 1 := ⟨a - 1, by omega⟩
  have hb : b ≤ b * b := Nat.le_mul_self b
  have e : (b + 1) * (b + 1 - 1) = b * b + b := by simp [Nat.add_mul]
  rw [e]
  have sq : (b + 1) * (b + 1) = b * b + 2 * b + 1 := by
    rw [Nat.add_mul, Nat.mul_add, Nat.mul_one, Nat.one_mul]; omega
  have h1 : 2 * (L - 1) + 3 * (b + 1) ≤ (b + 1) * (b + 1) + 2 * L := by omega
  have h2 : b * b + b + 2 * (L - (b + 1)) + 3 * (b + 1) ≤ (b + 1) * (b + 1) + 2 * L := by
    omega
  rcases le_total (2 * (L - 1)) (b * b + b + 2 * (L - (b + 1))) with h | h
  · rw [max_eq_right h]; exact h2
  · rw [max_eq_left h]; exact h1

/-- Case I: `1 ≤ a ≤ J`. -/
theorem arith_caseI (J f a g s L X DF DL : ℕ) (hm : 2 * J + 3 ≤ f + a)
    (hL : L = J + 1 + a) (ha1 : 1 ≤ a) (haJ : a ≤ J) (hg : g ≤ a) (hs : s ≤ J + 1)
    (hX : X + g ≤ g * s + L) (hDF : DF + f ≤ f * f) (hDL : DL + 3 * a ≤ a * a + 2 * L) :
    DF + 2 * X + DL + (f + a) ≤ (f + a) * (f + a) + 2 * J + 2 := by
  subst hL
  obtain ⟨b, rfl⟩ : ∃ b, a = b + 1 := ⟨a - 1, by omega⟩
  have h1 : g * s ≤ g * J + g := by
    have := Nat.mul_le_mul_left g hs
    linarith [Nat.mul_succ g J]
  have h2 : g * J ≤ (b + 1) * J := Nat.mul_le_mul_right J hg
  have h3 : (2 * J + 3) * (b + 1) ≤ (f + (b + 1)) * (b + 1) := Nat.mul_le_mul_right _ hm
  have h4 : b * b ≤ b * J := Nat.mul_le_mul_left b (by omega)
  nlinarith

/-- Case II: `a ≥ J+1`. -/
theorem arith_caseII (J f a g s L X DF Y : ℕ) (hm : 2 * J + 3 ≤ f + a)
    (hL : L = J + 1 + a) (haJ : J + 1 ≤ a) (hg : g ≤ a) (hsJ : s ≤ J + 1) (hsf : s ≤ f)
    (hX : X + g ≤ g * s + L) (hDF : DF + f ≤ f * f) (hY : Y ≤ (J + 1) * L) :
    DF + X + Y + (f + a) ≤ (f + a) * (f + a) + 2 * J + 2 := by
  subst hL
  rcases le_total f (J + 1) with hfJ | hfJ
  · -- small `f` (so `a ≥ J+2`): use `s ≤ f`
    have ha2 : J + 2 ≤ a := by omega
    have h1 : g * s ≤ a * f := Nat.mul_le_mul hg hsf
    have h2 : (2 * J + 3) * a ≤ (f + a) * a := Nat.mul_le_mul_right _ hm
    have h3 : (J + 2) * J ≤ a * J := Nat.mul_le_mul_right J ha2
    nlinarith
  · -- large `f`: use `s ≤ J+1`
    obtain ⟨p, rfl⟩ : ∃ p, a = J + 1 + p := ⟨a - (J + 1), by omega⟩
    obtain ⟨q, rfl⟩ : ∃ q, f = J + 1 + q := ⟨f - (J + 1), by omega⟩
    have h1 : g * s ≤ g * J + g := by
      have := Nat.mul_le_mul_left g hsJ
      linarith [Nat.mul_succ g J]
    have h2 : g * J ≤ (J + 1 + p) * J := Nat.mul_le_mul_right J hg
    nlinarith

end Conjectures.Erdos614
