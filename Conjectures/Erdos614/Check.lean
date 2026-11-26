/-
Open this file in VS Code and put your cursor on each line below; the "Lean Infoview" panel
shows Lean's own answer. Or run in a terminal:  lake env lean Conjectures/Erdos614/Check.lean
-/
import Conjectures.Erdos614.Main

-- 1. The exact statement Lean has accepted as proved:
#check @Conjectures.Erdos614.erdos_614_of_two_mul_le

-- 2. What the proof depends on. A proof with any gap would list `sorryAx` here.
--    Expected: only [propext, Classical.choice, Quot.sound] (Lean's standard axioms).
#print axioms Conjectures.Erdos614.erdos_614_of_two_mul_le

-- 3. Sanity check: plug in n = 16, k = 10 (one of the newly covered cases).
--    Lean computes the formula value; (16-10-1)*(16+10-2)/2 = 5*24/2 = 60.
example : (16 - 10 - 1) * (16 + 10 - 2) / 2 = 60 := by decide
#check Conjectures.Erdos614.erdos_614_of_two_mul_le 16 10 (by decide) (by decide)
