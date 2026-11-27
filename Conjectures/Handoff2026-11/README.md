# Handoff from a parallel session (November 26, 2026)

This folder is the unmodified archive from a separate Claude session that worked on open problems from the same
shortlists. **`HANDOFF.md` is the summary.** It lists results, methods, and what still needs independent checking.
Nothing here has been peer-reviewed or re-verified in this repository.

The main results are listed below; see `HANDOFF.md` for the details and caveats.

- **Kuca / Finch additive sequences.**
  - Computer-assisted proofs of the even-term sets of V(2,9) (Kuca's Conjecture 3.1, case n − 1 = 8).
  - Many V(4,b), V(6,b) and V(10,b) cases (Conjecture 4.1).
  - Several U(a,b) cases, including U(4,7) (period 11,301,098).
  - Files: `vab/`, `kuca/`, `big/`.
- **Inscribed squares in hypercube Hamiltonian cycles.**
  - The answer is yes for n ≤ 7. The n = 7 case rests on a DRUP certificate that has not been checked with drat-trim yet.
  - Counterexamples for n = 8, 9, 10.
  - Files: `audit/`. See also [`../HypercubeSquares`](../HypercubeSquares/) for the Lean-verified Q₈ counterexample.
- **Digital anomalies, k = 2.** Another infinite family, built from the iterates mᵣ₊₁ = 2mᵣ² − 1 (`solve/`). Compare
  [`../DigitalAnomalies`](../DigitalAnomalies/).
- **Litt's game, Conjecture 2.** Exact checks for word lengths up to 10 (`round3/litt.c`). Still open.
- **Knight's-move sequence A394166.** Partial structural results (`round3/`, `solve/`).

Build: `gcc -O3 -march=native`. Some Python scripts need `sympy`, `python-sat` or `ortools`.
