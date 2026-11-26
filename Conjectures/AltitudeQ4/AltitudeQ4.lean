/-
# An edge-ordering of Q₄ with no increasing path of length 4

Vertices of the 4-cube are `Fin 16`; vertex `v` is its 4-bit binary string (0101 = 5).
`lab` labels the 32 edges with 1..32 (0 on non-edges). With this labeling the longest path
with strictly increasing labels has 3 edges, which certifies `f(Q₄) ≤ 3`, where `f(G)` is the
minimum over edge-orderings of the longest increasing path. (The matching lower bound came
from a SAT solver and is not formalized here.)

Every theorem is checked by `decide`, i.e. by kernel evaluation; plain Lean core, no Mathlib.
-/

namespace AltitudeQ4

/-- `u` and `v` differ in exactly one bit. -/
def adj (u v : Fin 16) : Bool :=
  let x := u.val ^^^ v.val
  x == 1 || x == 2 || x == 4 || x == 8

/-- Label of the edge `{a, b}` for `a < b`, as natural numbers; `0` for non-edges. -/
def labN : Nat → Nat → Nat
  |  0,  8 =>  1  -- 0000–1000
  |  4,  6 =>  2  -- 0100–0110
  |  0,  4 =>  3  -- 0000–0100
  |  9, 11 =>  4  -- 1001–1011
  |  1,  3 =>  5  -- 0001–0011
  |  2, 10 =>  6  -- 0010–1010
  |  2,  3 =>  7  -- 0010–0011
  |  0,  2 =>  8  -- 0000–0010
  |  8,  9 =>  9  -- 1000–1001
  | 12, 14 => 10  -- 1100–1110
  |  5, 13 => 11  -- 0101–1101
  | 12, 13 => 12  -- 1100–1101
  |  7, 15 => 13  -- 0111–1111
  |  6,  7 => 14  -- 0110–0111
  | 11, 15 => 15  -- 1011–1111
  | 10, 14 => 16  -- 1010–1110
  |  1,  5 => 17  -- 0001–0101
  |  5,  7 => 18  -- 0101–0111
  |  6, 14 => 19  -- 0110–1110
  |  2,  6 => 20  -- 0010–0110
  |  8, 10 => 21  -- 1000–1010
  |  1,  9 => 22  -- 0001–1001
  |  0,  1 => 23  -- 0000–0001
  |  3, 11 => 24  -- 0011–1011
  |  3,  7 => 25  -- 0011–0111
  |  4, 12 => 26  -- 0100–1100
  |  4,  5 => 27  -- 0100–0101
  |  8, 12 => 28  -- 1000–1100
  | 13, 15 => 29  -- 1101–1111
  |  9, 13 => 30  -- 1001–1101
  | 10, 11 => 31  -- 1010–1011
  | 14, 15 => 32  -- 1110–1111
  | _, _ => 0

/-- Symmetric edge label. -/
def lab (u v : Fin 16) : Nat := labN (min u.val v.val) (max u.val v.val)

/-- Every edge gets a label in `1..32`, and distinct edges get distinct labels. -/
theorem labels_bijective :
    (∀ u v : Fin 16, adj u v = true → 1 ≤ lab u v ∧ lab u v ≤ 32) ∧
    (∀ u v : Fin 16, adj u v = true → ∀ x y : Fin 16, adj x y = true →
      lab u v = lab x y → (u = x ∧ v = y) ∨ (u = y ∧ v = x)) := by
  decide

/-- **Main result.** No path `v₀ v₁ v₂ v₃ v₄` of 5 distinct vertices has strictly increasing
labels. (Quantifiers are interleaved with the conditions so the search short-circuits.) -/
theorem no_increasing_path_4 :
    ¬ ∃ v0 v1 : Fin 16, adj v0 v1 = true ∧
      ∃ v2 : Fin 16, adj v1 v2 = true ∧ lab v0 v1 < lab v1 v2 ∧
      ∃ v3 : Fin 16, adj v2 v3 = true ∧ lab v1 v2 < lab v2 v3 ∧
      ∃ v4 : Fin 16, adj v3 v4 = true ∧ lab v2 v3 < lab v3 v4 ∧
        v0 ≠ v1 ∧ v0 ≠ v2 ∧ v0 ≠ v3 ∧ v0 ≠ v4 ∧ v1 ≠ v2 ∧
        v1 ≠ v3 ∧ v1 ≠ v4 ∧ v2 ≠ v3 ∧ v2 ≠ v4 ∧ v3 ≠ v4 := by
  decide

/-- An increasing path with 3 edges exists: 0000 → 0100 → 1100 → 1000 (labels 3, 26, 28). -/
theorem exists_increasing_path_3 :
    ∃ v0 v1 v2 v3 : Fin 16,
      adj v0 v1 = true ∧ adj v1 v2 = true ∧ adj v2 v3 = true ∧
      lab v0 v1 < lab v1 v2 ∧ lab v1 v2 < lab v2 v3 ∧
      v0 ≠ v1 ∧ v0 ≠ v2 ∧ v0 ≠ v3 ∧ v1 ≠ v2 ∧ v1 ≠ v3 ∧ v2 ≠ v3 :=
  ⟨0, 4, 12, 8, by decide⟩

/-- Distinctness matters: the closed walk 0000 → 1000 → 1001 → 0001 → 0000 has increasing
labels 1, 9, 22, 23. -/
theorem exists_increasing_closed_walk_4 :
    ∃ v0 v1 v2 v3 v4 : Fin 16, v4 = v0 ∧
      adj v0 v1 = true ∧ adj v1 v2 = true ∧ adj v2 v3 = true ∧ adj v3 v4 = true ∧
      lab v0 v1 < lab v1 v2 ∧ lab v1 v2 < lab v2 v3 ∧ lab v2 v3 < lab v3 v4 :=
  ⟨0, 8, 9, 1, 0, by decide⟩

end AltitudeQ4
