/-
Scratch space for trying things out. Not part of any conjecture.

Tip: import only what you need (e.g. `Mathlib.Tactic.Ring`) rather than all of
`Mathlib` — on an 8 GB machine, `import Mathlib` takes minutes to load.
-/
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring
import Mathlib.Basic.Real.Basic

theorem two_add_two : (2 : ℕ) + 2 = 4 := by norm_num

example (a b : ℝ) : (a + b)^2 = a^2 + 2*a*b + b^2 := by ring
