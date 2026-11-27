# Critical exponents of morphic images (Currie's Conjecture 1)

**Status:** Open. **Partial progress:**
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

## Next step

The plan is to use Walnut, which is installed locally. Walnut's `image` command needs uniform morphisms, so the work is:
1. Add G's Dumont–Thomas numeration system, based on 1, 2, 3, 5, 9, 16, 28, …, which satisfies
   Uₙ = 2Uₙ₋₁ − Uₙ₋₂ + Uₙ₋₃. This needs an addition automaton, which is regular because λ is a Pisot number.
2. Express A and C through the synchronized letter counts of prefixes of G.
3. Decide complexity and critical exponent in Walnut.
