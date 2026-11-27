# Math Conjectures

Conjectures I'm working on, each with an informal write-up and a formal statement in
[Lean 4](https://lean-lang.org) using [Mathlib](https://github.com/leanprover-community/mathlib4).

## Layout

```
Conjectures/<Name>/README.md   informal statement, motivation, progress, notes
Conjectures/<Name>/Main.lean   formal statement (and eventually the proof)
Playground.lean                scratch space
templates/conjecture/          template for new conjectures
scripts/new-conjecture.sh      creates a new conjecture folder
platform/                      MathResearchLab: web app for finding, recording and testing conjectures (see platform/README.md)
```

## Adding a conjecture

```sh
scripts/new-conjecture.sh MyConjecture "My Conjecture"
```

## Building

```sh
lake exe cache get   # download prebuilt Mathlib (first time only)
lake build
```

Unproven conjectures use `sorry`, which Lean reports as a warning, not an error.

## Conjectures

- [Erdős Problem 64 (Erdős–Gyárfás conjecture)](Conjectures/Erdos64/) — Open; statement formalized
- [Erdős Problem 614](Conjectures/Erdos614/) — Open; formula proved (Lean-verified) for k+2 ≤ n ≤ (3k+2)/2, extending Erdős–Reid–Schelp–Staton / Pikhurko–Thomason; fails for all n ≥ 2k+1
- [Altitude of the hypercube](Conjectures/AltitudeQ4/) — **f(Q_d) = d fails for every d ≥ 4**: f(Q_d) ≤ d − ⌊d/4⌋, Lean-verified for all d (product bound + explicit Q_4 ordering); f(Q_3) = f(Q_4) = 3
- [Digital anomalies (Seraj)](Conjectures/DigitalAnomalies/) — **Conjecture 4.6 false; infinitely many two-digit anomalies**, Lean-verified (Pell family x = B²/2)
- [Proper conflict-free colouring, Δ = 4](Conjectures/PCFColouring/) — Open; no counterexample on ≤ 12 vertices (exhaustive)
- [Local Irregularity Conjecture, subcubic](Conjectures/LocalIrregularity/) — Open; holds for all connected subcubic graphs on ≤ 16 vertices (exhaustive)
- [Additive colouring of bipartite graphs](Conjectures/AdditiveColouring/) — Open; η ≤ 2 for all connected bipartite graphs on ≤ 15 vertices (exhaustive)
- [Order sequences of equal-order simple groups (Cameron–Dey Q8.5)](Conjectures/OrderSequenceSimple/) — **Answered: no**; PSp(6,5) and Ω(7,5) (also PSp(8,3), Ω(9,3)) have incomparable order sequences (GAP, cross-checked)
- [Gonality of Q_6](Conjectures/GonalityQ6/) — **gon(Q_6) = 32** (computer-assisted proof; computations re-run independently; Lean formalization of the finite lemmas in progress)
- [Kuca's conjecture, V(2,5)](Conjectures/KucaV25/) — **Proved** for n = 5: even terms are 2, 10, 52 (period 694 from 2131; Lean formalization in progress)
- [Hypercubes with distant faulty vertices (Gregor–Škrekovski)](Conjectures/DistantFaults/) — Open; holds for n ≤ 6 in both forms (exhaustive)
- [Critical exponents of morphic images (Currie Conj. 1)](Conjectures/CurrieExponent/) — Open; 4 of 10 morphisms proved, the rest reduce to two words; numerics consistent
- [Handoff from a parallel session](Conjectures/Handoff2026-11/) — Kuca/Finch V(a,b), U(a,b) cases, Litt's game, knight sequence; unverified here
- [Inscribed squares in hypercube Hamiltonian cycles (Sagols–Morales-Luna)](Conjectures/HypercubeSquares/) — **False**; Lean-verified square-free Hamiltonian cycle of Q_8 (also Q_9, Q_10); true for n ≤ 6
- [Parity vectors of Hamiltonian cycles of the hypercube are exactly the balanced vectors](Conjectures/ParityVectors/) — **False** (MathResearchLab)
- [Tightness of the lower bound $\alpha_=(Q_n)\ge 2^{n-2}$ for even $n$](Conjectures/AlphaEqLowerBoundTightness/) — Likely already resolved (novelty pre-check); not researched (MathResearchLab)
- [Characterize the chromatic vectors of Hamiltonian cycles of $Q_n$](Conjectures/ChromaticVectors/) — Open per source; openness not yet verified (MathResearchLab)
- [Characterize the chromatic-segments vectors $\delta_i(h)$ of Hamiltonian cycles of $Q_n$](Conjectures/ChromaticSegmentsVectors/) — Open per source; openness not yet verified (MathResearchLab)
- [Compute the equi-independence number of the hypercube](Conjectures/EquiIndependenceNumberHypercube/) — Open per source; openness not yet verified (MathResearchLab)
