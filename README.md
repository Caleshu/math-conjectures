# Math Conjectures

Conjectures I'm working on, each with an informal write-up and a formal statement in
[Lean 4](https://lean-lang.org) using [Mathlib](https://github.com/leanprover-community/mathlib4).

<!-- problems:begin (generated from problems.toml and MathResearchLab; edit problems.toml, not this block) -->

## Status at a glance

| ✅ Proved (true) | ❌ Disproved (false) | ⏳ Open |
|:-:|:-:|:-:|
| **2** | **6** | **28** |

*Verification* says how a result is known. **Lean-verified**: checked by the Lean kernel. **Computer-assisted / computer-checked**: an exact computation, reproducible from the folder. **AI research**: produced by MathResearchLab's AI agents and not yet checked by a human. Treat it as a lead, not a theorem. Problems marked 🤖 were found and researched by MathResearchLab (`platform/`). New folders are picked up automatically. To change a problem's category or summary, edit `problems.toml`.

## ✅ Proved — true

| Problem | Result | Verification |
|---|---|---|
| [Gonality of Q_6](Conjectures/GonalityQ6/) | **gon(Q_6) = 32** (computer-assisted proof; computations re-run independently) | Computer-assisted; Lean formalization of the finite lemmas in progress |
| [Kuca's conjecture, V(2,5)](Conjectures/KucaV25/) | **Proved** for n = 5: even terms are 2, 10, 52 (period 694 from 2131) | Computer-assisted; Lean formalization in progress |

## ❌ Disproved — false

| Problem | Result | Verification |
|---|---|---|
| [Altitude of the hypercube](Conjectures/AltitudeQ4/) | **f(Q_d) = d fails for every d ≥ 4**: f(Q_d) ≤ d − ⌊d/4⌋ for all d (product bound + explicit Q_4 ordering); f(Q_3) = f(Q_4) = 3 | Lean-verified |
| [Digital anomalies (Seraj)](Conjectures/DigitalAnomalies/) | **Conjecture 4.6 false; infinitely many two-digit anomalies** (Pell family x = B²/2) | Lean-verified |
| [Inscribed squares in hypercube Hamiltonian cycles (Sagols–Morales-Luna)](Conjectures/HypercubeSquares/) | **False**; square-free Hamiltonian cycle of Q_8 (also Q_9, Q_10); true for n ≤ 6 | Lean-verified |
| [Order sequences of equal-order simple groups (Cameron–Dey Q8.5)](Conjectures/OrderSequenceSimple/) | **Answered: no**; PSp(6,5) and Ω(7,5) (also PSp(8,3), Ω(9,3)) have incomparable order sequences | Computer-assisted (GAP, cross-checked) |
| [Parity vectors of Hamiltonian cycles of Qₙ are the balanced vectors (Sagols–Morales-Luna)](Conjectures/ParityVectors/) 🤖 | The 'if' direction is false: in $Q_3$ with $k=4$ the balanced vector 0011 is never a parity vector (for $k=2^{n-1}$ every parity vector alternates) | Elementary proof + exhaustive computer check (n ≤ 4) |
| [Tightness of the bound α₌(Qₙ) ≥ 2ⁿ⁻² for even n (Sagols–Morales-Luna)](Conjectures/AlphaEqLowerBoundTightness/) 🤖 | False at $n=6$: an explicit balanced independent set of size 20 in $Q_6$ gives $\alpha_=(Q_6)\ge 20>16$ | Explicit witness, computer-checked |

## ⏳ Open

| Problem | Progress so far | Verification |
|---|---|---|
| [A combinatorial interpretation of Kronecker coefficients](Conjectures/CombinatorialInterpretationKroneckerCoef/) 🤖 | AI research run in progress. | AI research (not human-reviewed) |
| [A combinatorial interpretation of ordinary Schubert structure constants](Conjectures/CombinatorialInterpretationOrdinarySchub/) 🤖 | Recorded from the literature; not yet researched. | AI research (not human-reviewed) |
| [A common right descent decreases the length-thirteen Kazhdan–Lusztig coefficient by at most four](Conjectures/CommonRightDescentDecreases/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [A zero–one bound for the top permitted Kazhdan–Lusztig coefficient when $G=0$](Conjectures/ZeroOneBoundTop/) 🤖 | AI research run in progress. | AI research (not human-reviewed) |
| [A000032: Lucas numbers beginning at 2: L(n) = L(n-1) + L(n-2), L(0) = 2, L(1) = 1.](Conjectures/A000032LucasNumbersBeginning/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [A000041: a(n) is the number of partitions of n (the partition numbers).](Conjectures/A000041NNumberPartitions/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [A000122: Expansion of Jacobi theta function theta3(x) = Sum{m =-oo..oo} x^(m^2) (number of integer solutions to k^2 = n).](Conjectures/A000122ExpansionJacobiTheta/) 🤖 | Novelty pre-check: likely resolved. | AI research (not human-reviewed) |
| [A000166: Subfactorial or rencontres numbers, or derangements: number of permutations of n elements with no fixed points.](Conjectures/A000166SubfactorialOrRencontres/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [A000188: (1) Number of solutions to x^2 == 0 (mod n). (2) Also square root of largest square dividing n. (3) Also max_{ d divides n } gcd(d](Conjectures/A0001881NumberSolutions/) 🤖 | Novelty pre-check: trivial or ill posed. | AI research (not human-reviewed) |
| [A000215: Fermat numbers: a(n) = 2^(2^n) + 1.](Conjectures/A000215FermatNumbersN/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [A000247: a(n) = 2^n - n - 2.](Conjectures/A000247N2N/) 🤖 | Novelty pre-check: trivial or ill posed. | AI research (not human-reviewed) |
| [A000254: Unsigned Stirling numbers of first kind, s(n+1,2): a(n+1) = (n+1)*a(n) + n!.](Conjectures/A000254UnsignedStirlingNumbers/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [A000330: Square pyramidal numbers: a(n) = 0^2 + 1^2 + 2^2 + ... + n^2 = n*(n+1)*(2*n+1)/6.](Conjectures/A000330SquarePyramidalNumbers/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [A000332: Binomial coefficient binomial(n,4) = n*(n-1)*(n-2)*(n-3)/24.](Conjectures/A000332BinomialCoefficientBinomial/) 🤖 | Novelty pre-check: trivial or ill posed. | AI research (not human-reviewed) |
| [A000364: Euler (or secant or "Zig") numbers: e.g.f. (even powers only) sec(x) = 1/cos(x).](Conjectures/A000364EulerOrSecant/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [Additive colouring of bipartite graphs](Conjectures/AdditiveColouring/) | η ≤ 2 for all connected bipartite graphs on ≤ 15 vertices (exhaustive) | Computational evidence |
| [Chromatic vectors of Hamiltonian cycles of Qₙ (Sagols–Morales-Luna)](Conjectures/ChromaticVectors/) 🤖 | New necessary condition $\sum_{i\in S}c_i\ge 2^{\lvert S\rvert}$; with evenness it characterises chromatic vectors for $n\le 4$ (exhaustive) and $n=5$ (CP-SAT). Open for $n\ge 6$ | AI research + computation (not human-reviewed) |
| [Chromatic-segment vectors δᵢ(h) of Hamiltonian cycles of Qₙ (Sagols–Morales-Luna)](Conjectures/ChromaticSegmentsVectors/) 🤖 | First AI research run stopped at its runtime limit before review (31 unreviewed claims); being re-run | AI research (not human-reviewed) |
| [Critical exponents of morphic images (Currie Conj. 1)](Conjectures/CurrieExponent/) | 4 of 10 morphisms proved, the rest reduce to two words; numerics consistent | Partial proof |
| [Equi-independence number α₌(Qₙ) of the hypercube (Sagols–Morales-Luna)](Conjectures/EquiIndependenceNumberHypercube/) 🤖 | Exact values for $m\le 7$: 0, 0, 2, 4, 10, 20, 44 (CP-SAT; $m\le 4$ also brute force). Open in general | Computational (solver-dependent for m ≥ 5) |
| [Erdős Problem 151 — cliqueFree four](Conjectures/ErdS151CliqueFree/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [Erdős Problem 366 — weaker](Conjectures/ErdS366Weaker/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [Erdős Problem 614](Conjectures/Erdos614/) | Formula proved for k+2 ≤ n ≤ (3k+2)/2, extending Erdős–Reid–Schelp–Staton / Pikhurko–Thomason; fails for all n ≥ 2k+1 | Partial result Lean-verified |
| [Erdős Problem 64 (Erdős–Gyárfás conjecture)](Conjectures/Erdos64/) | Statement formalized | Statement formalized in Lean |
| [Hypercubes with distant faulty vertices (Gregor–Škrekovski)](Conjectures/DistantFaults/) | Holds for n ≤ 6 in both forms (exhaustive) | Computational evidence |
| [Local Irregularity Conjecture, subcubic](Conjectures/LocalIrregularity/) | Holds for all connected subcubic graphs on ≤ 16 vertices (exhaustive) | Computational evidence |
| [Lollipop graphs maximize the hitting time index among connected n-vertex graphs](Conjectures/LollipopGraphsMaximizeHitting/) 🤖 | AI research run finished; see the folder's report. | AI research (not human-reviewed) |
| [Proper conflict-free colouring, Δ = 4](Conjectures/PCFColouring/) | No counterexample on ≤ 12 vertices (exhaustive) | Computational evidence |

## 📝 Notes and handoffs

- [Handoff from a parallel session](Conjectures/Handoff2026-11/): Kuca/Finch V(a,b), U(a,b) cases, Litt's game, knight sequence; unverified here

<!-- problems:end -->

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
