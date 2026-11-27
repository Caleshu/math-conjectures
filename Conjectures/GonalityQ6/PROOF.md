# The gonality of the 6-dimensional hypercube is 32 (computer-assisted)

## Statement
gon(Q6) = 32. The upper bound is classical (put one chip on each vertex of one bipartite class). We prove gon(Q6) ≥ 32.

## Ingredients
1. **Harper's edge-isoperimetric inequality.** A set of m vertices in Q6 has at least 6m − 2h(m) boundary edges, where h(m) = Σ_{i<m} popcount(i). For 11 ≤ m ≤ 53 this is ≥ 32; for m = 10 it is 30. Boundaries in Q6 are always even.
2. **The proof of sn(G) ≤ gon(G)** (Harp–Jackson–Jensen–Speeter, Thm 4.1), reused step by step.

## Definitions
- W ⊆ V is *cheap* if |W| ≤ 10, |∂W| ≤ 30, and W is not a closed neighborhood N[v].
- An *egg* is a connected C ⊆ V not contained in any cheap set. Eggs are upward closed among connected sets.
- Every closed neighborhood N[v] is an egg (every strict superset of N[v] with ≤ 10 vertices has boundary ≥ 32).

## Lemma 1 (cuts)
If A contains an egg and V∖A contains an egg, then |∂A| ≥ 32, or A or V∖A is a closed neighborhood.
*Proof.* If both sides have ≥ 11 vertices, Harper gives ≥ 32. Otherwise the smaller side S has ≤ 10 vertices and contains an egg, so S is not cheap: either |∂S| ≥ 31 (hence ≥ 32 by parity) or S is a closed neighborhood.

## Lemma 2 (C1, computer)
Every set X with |X| ≤ 31 misses some egg.

## Lemma 3 (C2, computer)
None of the 130 divisors 5·1_{N(0)} + R or 2·1_{S2(0)} + R (R = 0 or a single chip) has positive rank.

## Proof of gon(Q6) ≥ 32
Suppose D′ has positive rank and degree d ≤ 31. Among effective divisors equivalent to D′, choose D whose support meets the most eggs.
- If Supp(D) meets every egg, Lemma 2 gives d ≥ |Supp D| ≥ 32. Contradiction.
- Otherwise, Thm 4.1's argument produces a legal firing of a set U from an effective D_{i−1} ~ D′, with an egg inside U and an egg inside V∖U. Then d ≥ D_{i−1}(U) ≥ |∂U|. By Lemma 1, either |∂U| ≥ 32 (contradiction), or U = N[v] or V∖U = N[v].
  - If U = N[v]: each neighbor of v has 5 edges leaving U, so D_{i−1} ≥ 5·1_{N(v)}. That is 30 chips, so D_{i−1} = 5·1_{N(v)} + R with deg R ≤ 1.
  - If V∖U = N[v]: each of the 15 vertices at distance 2 from v has 2 edges into N(v), so D_{i−1} = 2·1_{S2(v)} + R with deg R ≤ 1.
  - By symmetry v = 0, and Lemma 3 says D_{i−1}, hence D′, has rank 0. Contradiction. ∎

## Computations
- Lemma 3: two independent rank checkers (Python and C, both using Dhar's burning algorithm), validated on known cases.
- Lemma 2: exhaustive branch-and-prune search over X (C), with WLOG reductions: vertex 0 ∉ X; 0 has the maximum number of non-X neighbors among non-X vertices; and the X-membership of 0's neighbors is sorted (coordinate permutations). If 0 has no non-X neighbors, V∖X is independent, so |X| ≥ 32. The search prunes when a partial component of V∖X becomes an egg, or when a vertex of V∖X has no X-neighbor. About 2.98·10^10 nodes, result: none. Calibration: the same code finds valid sets of size 32, confirmed by a separate checker. Independent reimplementation (different vertex order, brute-force egg test, separate code): also none, in 32 chunks. Both programs find valid hitting sets at size 32.

## Files
- `dfs3.c`: main exhaustive search for Lemma 2 (run `./dfs3 31 16 k` for k = 0..15).
- `dfsB.c`: independent reimplementation (run `./dfsB 31 32 k` for k = 0..31).
- `special.py`, `c2.c`: Lemma 3 in Python and C.
- `eggcut.py`: Harper table and the closed-neighborhood superset check.
- `verify_eggs.py`: standalone egg checker, used to validate the size-32 hitting set.
