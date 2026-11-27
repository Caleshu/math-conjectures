# Critical exponents of morphic images (Currie's Conjecture 1)

**Status:** Open. **Partial progress** (a Walnut pipeline is built and calibrated on G; see item 4):
- Proved for 4 of the 10 morphisms by a short argument.
- The 10 words fall into 3 equivalence classes, so only 2 words are left.
- Numerically, all 10 behave as conjectured.

## Statement

Let G be the fixed point of γ: 0 → 01, 1 → 2, 2 → 02, and let G′ be the fixed point of γᴿ: 0 → 10, 1 → 2, 2 → 20. Both
have factor complexity 2n + 1 and critical exponent μ = 2 + 1/(λ² − 1) ≈ 2.48086, where λ ≈ 1.75488 is the real root of
x³ − 2x² + x − 1 (Shallit–Shur).

**Conjecture 1** (Currie, *Words with factor complexity 2n+1 and minimal critical exponent*, arXiv:2507.09387, §7). For
each of the 4 morphisms h in Figure 1, h(G) has factor complexity 2n + 1 and critical exponent μ. The same holds for
h(G′) for each of the 6 morphisms in Figure 2.

## Results

**1. Four cases are immediate** (`computations/conj.py`). If h is a conjugate of π∘γᵏ, where π permutes the letters, then
h(G) is a suffix of π(G). Here a conjugate means that h(x) = p⁻¹·π(γᵏ(x))·p for every letter x and a fixed word p. A
suffix of π(G) has the same factors as G, because G is uniformly recurrent, so it has the same complexity and critical
exponent. The search finds:

| Morphism | as a conjugate of |
|---|---|
| Fig. 1 #3 [021201212, 0212012, 021201212012] | π∘γ⁴, π = 201 (Currie notes this one) |
| Fig. 2 #1 [10212, 0212, 0210212] | π∘(γᴿ)³, π = 201 |
| Fig. 2 #3 [121201210, 1201210, 120121201210] | π∘(γᴿ)⁴, π = 102 |

Fig. 2 #2 has exactly the factors of a relabelled G, up to length 30 (`cls.py`). It is in the same class as the three
above, but the conjugacy search does not cover it, so it still needs its own proof.

**2. Three classes** (`computations/cls.py`). Two words are put in the same class when their sets of factors of length 25
agree after relabelling letters or reversing the word.

| Class | Members | Status |
|---|---|---|
| B (= G) | F1.3, F2.1, F2.2, F2.3 | proved via item 1, except F2.2 (factor-set match up to length 30 only) |
| A | F1.1, F1.2, F2.4, F2.5 | open |
| C | F1.4, F2.6 | open |

So Conjecture 1 comes down to two words, A = h(G) with h = [1210202, 12102, 1210202102], and
C = h(G) with h = [21021102211021102, 2102110221102, 2102110221102110221102].

The letter-count matrix of h is singular for both of these. So for k ≤ 11 no morphism φ satisfies φ∘h = h∘γᵏ, and the
shortcut from item 1 cannot work.

**3. Numerics** (`computations/emp.py`). All 10 words have complexity exactly 2n + 1 for n ∈ {5, 10, 20, 40, 80}. The
largest exponent seen among periods below 1500, in prefixes of length 30,000, is 2.4797–2.4803 for every word. This
approaches μ from below, as expected.

**4. Walnut pipeline** (`computations/walnut/`). It is built and checked, but it has not decided A or C yet.

- **Numeration `msd_gam`** (`automata/msd_gam.txt`). G's Dumont–Thomas system, with weights 1, 2, 3, 5, 9, 16, 28, …
  satisfying Uₙ = 2Uₙ₋₁ − Uₙ₋₂ + Uₙ₋₃.
  - `linaut.py` builds the 153-state addition automaton exactly. A state tracks the language state and the pending
    linear form, so the automaton is sound by construction.
  - Walnut then proves it total, unique, commutative, associative and consistent with `<` (`verify_numeration.txt`,
    8/8 TRUE).
- **Words.** `GAM` is G as a DFAO. `BLKA` and `BLKC` (165 and 224 states) give the start of block m of h(G).
  - Walnut proves them correct by induction: the start value, existence, uniqueness, and the step
    BLK(m+1, s + |h(G[m])|).
  - `WA` and `WC` are A and C as DFAOs in `msd_gam` (`build_and_verify_AC.txt`, all TRUE; both match the first 40
    letters).
- **Calibration on G** (`period_G.txt`, `reps_G.txt`):
  - The period predicate has 664 states. The set of (length, period) pairs of maximal repetitions with exponent ≥ 2
    is a 22-state automaton (`automata/GAMrep.txt`).
  - Decoded with `reps.py`, the periods are exactly the numbers written 10…0 or 1010…0. For p = Uₖ, the longest
    repetition has n − 2p = Uₖ₋₂ + Uₖ₋₄ + ⋯, so n/p increases to 2 + 1/(λ² − 1) = μ from below.
  - This agrees with Shallit–Shur. Turning the closed form into a written proof is still to do.
  - Walnut takes a definition's free variables in alphabetical order: `GAMeq` is called as `$GAMeq(p,u)`.
- **Blocked on memory.** The comparison automata for A and C are much larger: `WA[u]=WA[u+p]` has 22,502 states, and
  `WC[u]=WC[u+p]` has 37,707. G's has 101.
  - With the A comparison, the "for all u" step builds a 350,605-state product and runs out of memory at a 6 GB heap,
    on an 8 GB machine. The C product (574,081 states) ran out at 4 GB and was not retried with more.
  - The formulation in `reps_A.txt`/`reps_C.txt`, which uses the first mismatch, is the cheapest found so far. It is
    10× faster than the direct one on G.

## Next step

- **More memory.** Run `reps_A.txt`/`reps_C.txt` on a machine with ≳ 16 GB.
- **Or work in G's coordinates**, where the automata are small. Write h = [XY, X, XYZ] with X = 12102, Y = 02 and
  Z = 102. A maximal repetition of G with period p should lift to one of A with period |h(G[j..j+p))|, extended by
  boundary terms:

  | Mismatched letters | L (left) | R (right) |
  |---|---|---|
  | {0,1} | 2 | 5 |
  | {0,2} | 2 | 8 |
  | {1,2} | 4 | 5 |

  These terms depend only on the mismatched pair. Two pieces are still needed: a synchronization-delay argument to
  make the lift rigorous, and a numerical check of the formula (not yet done).
- Then do factor complexity the same way.
