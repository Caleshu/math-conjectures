/-
# Digital anomalies: infinitely many with two digits

Positive integers `(x, y, B)`, `B ≥ 2`, form a *digital anomaly* with `k` digits if
`x / y = y + x / B^k`, where `k` is the number of base-`B` digits of `x`
(`B^(k-1) ≤ x < B^k`). Example: `5 / 2 = 2.5` (`k = 1`).

S. Seraj, *Diophantine Analysis of a Digital Anomaly*, arXiv:2512.06056, Conjecture 4.6,
says the only two-digit anomalies are `(18, 4, 6)` and `(1323, 36, 42)`.

**Theorem (`infinitely_many_two_digit`).** There are infinitely many two-digit anomalies.

Construction: if `p² = 8v² + 1` (Pell), then `B = 2vp`, `y = 4v²`, `x = 2v²p² = B²/2` works:
`x/y = p²/2 = y + 1/2 = y + x/B²`. The Pell solutions `(3,1), (17,6), (99,35), …` come from
`(p, v) ↦ (3p + 8v, p + 3v)`.
-/
import Mathlib

namespace DigitalAnomalies

/-- `(x, y, B)` is a digital anomaly with `k` base-`B` digits. -/
def IsAnomaly (k x y B : ℕ) : Prop :=
  2 ≤ B ∧ 0 < y ∧ B ^ (k - 1) ≤ x ∧ x < B ^ k ∧ (x : ℚ) / y = y + (x : ℚ) / (B : ℚ) ^ k

/-- Solutions of `p² = 8v² + 1`. -/
def pell : ℕ → ℕ × ℕ
  | 0 => (3, 1)
  | n + 1 => (3 * (pell n).1 + 8 * (pell n).2, (pell n).1 + 3 * (pell n).2)

lemma pell_eq (n : ℕ) : (pell n).1 ^ 2 = 8 * (pell n).2 ^ 2 + 1 := by
  induction n with
  | zero => simp [pell]
  | succ n ih => simp only [pell]; nlinarith [ih]

lemma pell_ge (n : ℕ) : n + 1 ≤ (pell n).2 ∧ 1 ≤ (pell n).1 := by
  induction n with
  | zero => simp [pell]
  | succ n ih => simp only [pell]; omega

/-- The anomaly built from a Pell solution `p² = 8v² + 1`. -/
theorem anomaly_of_pell {p v : ℕ} (h : p ^ 2 = 8 * v ^ 2 + 1) (hv : 1 ≤ v) (hp : 1 ≤ p) :
    IsAnomaly 2 (2 * v ^ 2 * p ^ 2) (4 * v ^ 2) (2 * v * p) := by
  have hvp : 1 ≤ v * p := Nat.one_le_iff_ne_zero.2 (by positivity)
  refine ⟨by nlinarith, by positivity, ?_, ?_, ?_⟩
  · show (2 * v * p) ^ 1 ≤ 2 * v ^ 2 * p ^ 2
    nlinarith
  · nlinarith
  · have hq : ((p : ℚ)) ^ 2 = 8 * (v : ℚ) ^ 2 + 1 := by exact_mod_cast h
    have hv0 : (v : ℚ) ≠ 0 := by positivity
    have hp0 : (p : ℚ) ≠ 0 := by positivity
    push_cast
    field_simp
    rw [hq]; ring

/-- **Seraj's Conjecture 4.6 is false; there are infinitely many two-digit anomalies.** For
every `N` there is one with base `B > N`. -/
theorem infinitely_many_two_digit (N : ℕ) : ∃ x y B, N < B ∧ IsAnomaly 2 x y B := by
  obtain ⟨hv, hp⟩ := pell_ge N
  refine ⟨_, _, _, ?_, anomaly_of_pell (pell_eq N) (by omega) hp⟩
  nlinarith

/-- The two solutions in the paper, and the next one, `(20808, 144, 204)`. -/
example : IsAnomaly 2 18 4 6 ∧ IsAnomaly 2 1323 36 42 ∧ IsAnomaly 2 20808 144 204 := by
  refine ⟨⟨?_, ?_, ?_, ?_, ?_⟩, ⟨?_, ?_, ?_, ?_, ?_⟩, ⟨?_, ?_, ?_, ?_, ?_⟩⟩ <;> norm_num

end DigitalAnomalies
