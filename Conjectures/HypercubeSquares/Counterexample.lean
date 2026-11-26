/-
# The Sagols–Morales-Luna conjecture is false

An explicit Hamiltonian cycle of `Q_8` with no inscribed square. Vertex `k` is the point of
`{0,1}^8` whose coordinate `i` is bit `i` of `k`. The cycle is `0, 8, q8Rest…, 0`;
the Lean kernel checks it with `decide +kernel` (no `native_decide`, no extra axioms).

The cycle comes from a SAT search (see README.md); square-free cycles of `Q_9` and `Q_10`
are in `computations/`.
-/
import Conjectures.HypercubeSquares.Cert

namespace Conjectures.HypercubeSquares

/-- The cycle after its first two vertices `0, 8`. -/
def q8Rest : List ℕ := [
  9, 11, 27, 19, 147, 145, 177, 185, 57, 41, 33, 161, 163, 131, 139, 143,
  207, 223, 221, 157, 149, 21, 23, 55, 119, 103, 111, 239, 238, 206, 204, 220,
  252, 248, 184, 186, 187, 155, 219, 91, 90, 122, 120, 121, 113, 97, 96, 100,
  102, 230, 166, 164, 165, 181, 245, 241, 240, 224, 160, 168, 40, 104, 72, 76,
  68, 84, 20, 16, 17, 1, 65, 69, 71, 199, 198, 214, 222, 218, 216, 88,
  80, 112, 48, 176, 180, 148, 150, 22, 30, 62, 63, 59, 123, 107, 105, 109,
  77, 13, 141, 140, 172, 188, 189, 191, 175, 167, 39, 38, 6, 70, 66, 64,
  192, 200, 136, 138, 170, 174, 46, 110, 106, 98, 114, 115, 243, 179, 183, 182,
  190, 254, 126, 118, 86, 87, 83, 81, 209, 217, 249, 251, 255, 247, 215, 151,
  135, 133, 129, 128, 144, 208, 212, 213, 197, 205, 201, 73, 89, 25, 29, 61,
  53, 49, 51, 35, 99, 67, 75, 79, 78, 94, 92, 93, 85, 117, 116, 244,
  246, 242, 250, 234, 232, 233, 225, 193, 195, 211, 210, 82, 18, 2, 3, 7,
  15, 47, 45, 44, 36, 52, 54, 50, 58, 42, 43, 171, 235, 203, 202, 74,
  10, 14, 12, 28, 156, 152, 153, 137, 169, 173, 237, 253, 125, 127, 95, 31,
  159, 158, 142, 134, 130, 194, 226, 227, 231, 229, 101, 37, 5, 4, 132, 196,
  228, 236, 108, 124, 60, 56, 24, 26, 154, 146, 178, 162, 34, 32]

theorem q8_good : goodCycle 8 8 q8Rest = true := by decide +kernel

/-- A Hamiltonian cycle of `Q_8` with no inscribed square. -/
theorem q8_counterexample :
    ∃ c : (cube 8).Walk (toV 8 0) (toV 8 0), c.IsHamiltonianCycle ∧ ¬ HasInscribedSquare c :=
  exists_of_goodCycle q8_good

/-- **The Sagols–Morales-Luna inscribed-square conjecture is false** (at `n = 8`). -/
theorem not_conjecture : ¬ Conjecture := by
  intro h
  obtain ⟨c, hc, hsq⟩ := q8_counterexample
  exact hsq (h 8 (by decide) _ c hc)

end Conjectures.HypercubeSquares
