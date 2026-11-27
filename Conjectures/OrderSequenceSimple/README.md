# Order sequences of simple groups of the same order

**Status:** Question 8.5 of Cameron–Dey **answered: no.** The groups PSp(6,5) and Ω(7,5) have the same order, but
neither order sequence dominates the other. PSp(8,3) and Ω(9,3) are a second incomparable pair. This is computer-verified
(GAP character tables, cross-checked as described below). It is not in Lean. I found no earlier answer in the
literature (checked November 2026).

## Statement

The *order sequence* os(G) of a group of order n lists the orders of its n elements in non-decreasing order. For
groups G, H of the same order, os(G) *dominates* os(H) if the i-th entry of os(G) is at least the i-th entry of os(H)
for every i. Equivalently, for every t, G has at most as many elements of order ≤ t as H.

**Question 8.5** (Cameron–Dey, *On the order sequence of a group*, Electron. J. Combin. 32(2) (2025) P2.9,
arXiv:2310.06516; Question 34 in the journal numbering). Let G and H be non-isomorphic non-abelian simple groups of the
same order. Must os(G) dominate os(H), or os(H) dominate os(G)?

By the classification, the only such pairs are A₈ and PSL(3,4), and PSp(2n,q) and Ω(2n+1,q) for odd q and n ≥ 3. The paper
notes that os(A₈) dominates os(PSL(3,4)) and says the other cases are unknown.

## Results

| Pair | Order | Result |
|---|---|---|
| A₈, PSL(3,4) | 20160 | os(A₈) dominates (matches the paper) |
| PSp(6,3), Ω(7,3) | 4,585,351,680 | os(PSp(6,3)) dominates os(Ω(7,3)) |
| **PSp(6,5), Ω(7,5)** | 228,501,000,000,000 | **incomparable** |
| **PSp(8,3), Ω(9,3)** | 65,784,756,654,489,600 | **incomparable** |

**Why PSp(6,5) and Ω(7,5) are incomparable.**

- PSp(6,5) has **more involutions**: 153,969,375 against 138,345,375. So at t = 2 it has more elements of order ≤ t, and
  os(PSp(6,5)) does not dominate os(Ω(7,5)).
- Ω(7,5) has **far more elements of order ≤ 4**: 215,584,857,876 against 17,566,281,876. Most of the difference comes from
  elements of order 4: 209,947,500,000 against 11,913,300,000. So os(Ω(7,5)) does not dominate os(PSp(6,5)).

**Why PSp(8,3) and Ω(9,3) are incomparable.** Ω(9,3) has more involutions: 2,414,735,631 against 1,284,001,551. But
PSp(8,3) has more elements of order ≤ 4: 13,208,666,412,672 against 11,147,771,774,592.

## Verification

1. `computations/q85.g` (GAP 4.16.1 with CTblLib) reads the ATLAS character tables `S6(3)`, `O7(3)`, `S6(5)`,
   `O7(5)`, `S8(3)` and `O9(3)`. It adds up class sizes by element order and compares the cumulative counts. The output
   is in `computations/q85_output.txt`. Library tables for q = 7 and 9 and for n = 5 are not available.
2. `computations/invol.py` re-derives the involution counts from classical formulas, independently of the tables.
   - In PSp(2n,q), involutions lift to elements x with x² = I (centralizer Sp(2k) × Sp(2n−2k)) or with x² = −I
     (centralizer GL(n,q) if q ≡ 1 (mod 4), GU(n,q) if q ≡ 3 (mod 4)).
   - In Ω(2n+1,q), involutions are −1 on a non-degenerate 2k-dimensional subspace of square discriminant.
   - The formulas give exactly the table values in all six cases.
3. `computations/sample.g` draws 200,000 pseudo-random elements from the actual matrix groups Sp(6,5) (using
   projective order) and Ω(7,5). It estimates the proportion of elements of order ≤ 4 at 1.05×10⁻⁴ and 8.55×10⁻⁴.
   The tables give 0.77×10⁻⁴ and 9.43×10⁻⁴. The roughly 8× gap that makes the pair incomparable shows up without
   using the tables.

## A pattern

`invol.py` also shows the following for all 3 ≤ n ≤ 6 and odd q ≤ 27: PSp(2n,q) has more involutions than Ω(2n+1,q)
**if and only if q ≡ 1 (mod 4)**. For all those q ≡ 1 (mod 4), os(PSp(2n,q)) therefore does not dominate
os(Ω(2n+1,q)). Open: prove this for all n and q, and decide when Ω(2n+1,q) dominates PSp(2n,q).

## Related: Question 8.2 (already answered elsewhere)

Question 8.2 asks whether Theorem 2.6 (journal: Theorem 8) needs "G abelian". A GAP search of SmallGroups up to order
1000 finds SmallGroup(96,201) = 2^{1+4}₊ ⋊ C₃, which has 48 elements of order 12, while 2^{1+4}₊ × C₃ has only 24. So the
hypothesis is needed. **This is not new:** Lazorec, arXiv:2610.24950 (October 2026), answers Question 8.2 with the same
group.
