# Erdős Problem 614

**Status:** Open in general.
- **Formula:** f(n,k) = (n−k−1)(n+k−2)/2 for k+2 ≤ n ≤ (3k+2)/2. Proved here, with a complete
  Lean 4 proof (no `sorry`).
- **Sharpness:** the formula fails for every n ≥ 2k+1. Proved on paper and checked by computer;
  not in Lean.
- **Prior work:** most of the surrounding picture was already known. See
  [What was already known](#what-was-already-known).

## Statement

$f(n,k)$ is the minimum number of edges of a graph on $n$ vertices in which every set of $k+2$
vertices induces a subgraph of maximum degree at least $k$. Determine $f(n,k)$.
([erdosproblems.com/614](https://www.erdosproblems.com/614); Faudree–Rousseau–Schelp, *Problems in
graph theory from Memphis*, 1997.)

## What was already known

I read the erdosproblems.com forum thread (in a browser; it blocks automated fetches), the Tang–Ma
note it links, both available primary papers, and the citing literature.

1. **Complement / Turán reformulation:** known. Quanyu Tang (with Ma) posted it on the forum on
   7 Jan 2026 ([note](https://github.com/QuanyuTang/erdos-614-turan-reduction/blob/main/erdos614_note.pdf)).
   They show $f(n,k) = \binom n2 - \mathrm{ex}(n,\mathcal F_k^{\min})$, where $\mathcal F_k^{\min}$ is the
   edge-minimal graphs on $k+2$ vertices with minimum degree $\ge 2$. They also give explicit
   families for $k\le 6$, and $f(n,1)$, $f(n,2)$, $f(n,3)$ as Turán numbers. My Lemma 1 is the same
   reformulation.
2. **The formula and the conjectured range:** known. Problem 614 is the case $j=2$ of the
   function $q(a,j,l)$ of **Erdős, Reid, Schelp, Staton** (*Sizes of graphs with induced subgraphs of
   large maximum degree*, Discrete Math. 158 (1996) 283–286). Here $f(n,k) = q(k,2,l)$ with
   $l = n-k-2$. What I could not read directly I take from Pikhurko–Thomason's account below
   (ScienceDirect presented a CAPTCHA, which I did not attempt):
   - ERSS proved $q = (l+1)k + \binom{l+1}{2}$, which is **exactly this formula**, whenever
     $k\ge\max(2l, \binom{l+2}{2})$;
   - ERSS *conjectured* the same formula for all $k \ge l+2$, i.e. $n\le 2k$. That is
     "Conjecture 4" below, which is therefore **not mine**.
3. **Pikhurko–Thomason** (*Disjoint subgraphs of large maximum degree*, Discrete Math. 248 (2002)
   125–141; [author's PDF](https://opikhurko.warwick.ac.uk/E/PikhurkoThomason02dm.pdf), read in full):
   - Theorem 14 proves the formula when $k \ge (j+\tfrac12)l + \frac{2j+l}{4j-2}$, which for
     $j = 2$ is $k \ge \frac{8l+2}{3}$;
   - Theorem 13 shows it fails when $k < (j-1)l$, which for $j = 2$ is $k<l$, i.e. $n \ge 2k+3$;
   - they also give asymptotics, and disprove the ERSS conjecture for $j, l = \Theta(n)$. That does
     not touch $j=2$.
4. **Later work:** none found. Google Scholar lists 5 papers citing ERSS and 4 citing
   Pikhurko–Thomason. None improves the exact range; they are size-Ramsey and Hamiltonicity papers.
   An open-problem aggregator ([GEWU](https://magazine.gewu-lab.ai/en/problems/math-auth-0b992c70286f89653ff4))
   lists "the band between the known failure and success thresholds" as **open**.

## What is (as far as I can find) new

- **A wider proven range for $j=2$:** the formula holds for $k \ge 2l+2$, i.e. $n\le\frac{3k+2}{2}$.
  This contains Pikhurko–Thomason's range $k\ge\frac{8l+2}{3}$ (for $k \ge 6$; for $k \le 5$ the
  ranges coincide). With $l = n-k-2$, the **new cases** are
  $$2l+2\ \le\ k\ <\ \min\Bigl(\tfrac{8l+2}{3},\ \tbinom{l+2}{2}\Bigr),$$
  a band of width about $2l/3$. The first new case is $(n,k) = (13,8)$, then $(16,10)$ and $(17,11)$,
  and so on. The proof is different from ERSS/PT. It works in the complement and uses a
  "free vertex" gluing argument plus degree-sum counting.
- **Failure at $n = 2k+1$ and $n=2k+2$:** PT's Theorem 13 only reaches $n\ge 2k+3$. With it, the
  formula fails for **every** $n\ge 2k+1$ ($k\ge 2$). So for Problem 614 the ERSS threshold $n\le 2k$
  is exactly right, and what remains open is precisely $\frac{3k+2}{2} < n \le 2k$.
- **A machine-checked proof** of the formula on this range, also covering the previously known
  sub-ranges. I found no earlier formalization: formal-conjectures has only the open statement.

**Caveats.** I could not read the ERSS paper itself; its results are taken from PT and the GEWU
page. The literature search used web search, Google Scholar citations and the erdosproblems.com
thread. An unpublished or non-indexed result could exist. A specialist (for example Pikhurko) would
know.

## Claims ledger

### Proved, and formally verified in Lean 4

The axioms used are only `propext`, `Classical.choice`, `Quot.sound`; check with `#print axioms`.

| Claim | Lean |
|---|---|
| **Theorem.** $f(n,k) = (n-k-1)(n+k-2)/2$ for $k+2\le n$, $2n\le 3k+2$ | `Main.lean: f_eq` |
| Same, stated with the **verbatim** formal-conjectures set-builder | `erdos_614_of_two_mul_le` |
| Complement form: no 2-set of size $M+1$ in $U$, $\lvert U\rvert = M+1+J$, $2J+3\le M$ $\Rightarrow$ $e(H[U])\le \binom M2+J+1$ | `Claim.lean: claim` |
| Good $G$ $\Rightarrow$ $\overline G$ has no $(k+2)$-vertex subgraph of min degree $\ge 2$ (forward half of the reformulation) | `not_twoSet_compl_of_good` |
| The extremal graph $G_0$ is good and has exactly the formula's number of edges | `G₀_good`, `G₀_edges` |
| Peeling lemma, gluing lemma, counting inequalities | `Basic.lean`, `Claim.lean`, `Arith.lean` |

### Proved on paper, not in Lean (but computer-checked)

| Claim | Evidence |
|---|---|
| Full reformulation (both directions); already known (Tang–Ma) | `PROOF.md` §2; checked against `direct.c` for all graphs, $n\le 8$ |
| **Sharpness:** for $k\ge 2$, $n\ge 2k+1$: $f(n,k)\le$ formula $-1$ | `PROOF.md` §5; `sharpness.c`: every $k\le 15$ at $n=2k+1$, $k\le 14$ at $n=2k+2$, $k\le 13$ at $n = 2k+4$, from the original definition |
| The formula fails for all $n\ge 2k+1$ | sharpness above, plus PT Thm 13 |

### Computationally established (exhaustive)

| Claim | Method |
|---|---|
| Exact $f(n,k)$ for all $n\le 10$ (table below) | nauty `geng` + `sizes.c`, every graph on $\le 10$ vertices |
| The formula holds for every $k+2\le n\le\min(10,2k)$ | same table |
| SAT cross-check of a **new** case $(n,k)=(13,8)$: $f=38$ | `sat_check.py` (CaDiCaL); see `out/sat_n13_k8.txt` |
| SAT check of the encoding on known cases $(9,6)$, $(10,6)$, $(9,4)$ | `sat_check.py` |

### Conjectural (open)

| Claim | Status |
|---|---|
| **ERSS Conjecture (j=2):** the formula holds for all $k+2\le n\le 2k$ | Open. Due to Erdős–Reid–Schelp–Staton (1996), not to me. True for $n\le 10$; recorded as the Lean `Prop` `ERSSConjecture614` with no proof |
| Exact $f(n,k)$ for $n > 2k$ | Open. For fixed $k$ this is a Turán problem for $\mathcal F_k^{\min}$ (Tang–Ma) |

## Attack on range 2 ((3k+2)/2 < n ≤ 2k): status, 26 Nov 2026

**Not proved.** These notes record what was tried. Notation: m = k+2, J = n−m.

- **Where the Lean proof breaks.** Just past J = (m−4)/2 it fails in two places:
  - a ∈ {0,1}: fixable. The forest leaf-path argument in `PROOF.md` history works for all J ≤ m−4;
  - a ≈ J: the real obstruction.
- **Bootstrap closure.** Let B be the 2-neighbour bootstrap closure of the free set F inside the
  low-degree set L. By gluing, |B| ≤ a, and every other vertex of L has at most one neighbour in
  F ∪ B. Combined with:
  - strong induction on the 2-core of the remainder;
  - a "stuck descent" lemma (deleting vertices with no degree-2 neighbour; a stuck set has at least
    half of its vertices of degree 2);
  - a corrected count of edges inside F ∪ B,

  this scheme closes numerically up to about J ≤ 0.59m at m = 80. Compare J ≤ 0.5m for the proved
  theorem (`computations/range2_v4.py`). It is **not yet a written or verified proof**, and the gain
  is modest (n ≲ 1.6k instead of 1.5k).
- **Hard wall: graphs with no high-degree vertices.** If every vertex of H has degree ≤ J+1, the
  only available bound is n(J+1)/2. That bound exceeds the target once J > ((√5−1)/2)·k ≈ 0.618k.
  Beyond that point counting cannot work, and a structural theorem is needed. In G-language: a
  graph of minimum degree ≥ k on n = k+2+J vertices with fewer than (J+1)(2k+J)/2 edges must
  contain a (k+2)-set in which every vertex misses at least two others. Equivalently, in H: some
  J-set T leaves every vertex outside T with at least two neighbours outside T.
- **Consistency with the literature.** Pikhurko–Thomason's asymptotics give q(k,2,l) ~ formula
  when l = Θ(k), so no counterexample is expected from their methods. Their disproof of the ERSS
  conjecture needs j = Θ(n), not j = 2.

## Exact values for n ≤ 10 (exhaustive)

$f(n,k)$. Entries marked \* have $n\le 2k$ and match the formula. Entries with $n\in\{2k+1, 2k+2\}$
are one or two below it, as the sharpness result predicts.

| n \ k | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| 4 | 2 | 2\* | | | | | | |
| 5 | 4 | 4 | 3\* | | | | | |
| 6 | 6 | 8 | 7\* | 4\* | | | | |
| 7 | 9 | 12 | 11 | 9\* | 5\* | | | |
| 8 | 12 | 17 | 15 | 15\* | 11\* | 6\* | | |
| 9 | 16 | 23 | 22 | 21 | 18\* | 13\* | 7\* | |
| 10 | 20 | 29 | 29 | 28 | 26\* | 21\* | 15\* | 8\* |

## Files

- **[`PROOF.md`](PROOF.md):** the complete proof, every step explicit and keyed to Lean lemma names.
- **`Basic.lean`, `Arith.lean`, `Claim.lean`, `Main.lean`:** the Lean 4 formalization.
- **[`computations/`](computations/):**
  - `sizes.c`: exhaustive search in the complement form;
  - `direct.c`: exhaustive search from the original definition;
  - `sharpness.c`: the sharpness checks;
  - `sat_check.py`: the SAT cross-check;
  - `check_proof_inequalities.py`, `lean_case_split_check.py`: numeric checks of the case analysis;
  - `out/`: raw outputs.

Rebuild and check:
```sh
lake build Conjectures.Erdos614.Main
# then, in a file: import Conjectures.Erdos614.Main
#                  #print axioms Conjectures.Erdos614.f_eq
```

## References

- [erdosproblems.com/614](https://www.erdosproblems.com/614) and its
  [forum thread](https://www.erdosproblems.com/forum/thread/614)
- Q. Tang and Ma, *Erdős Problem #614: a Turán-type reformulation* (note, Jan 2026),
  [GitHub](https://github.com/QuanyuTang/erdos-614-turan-reduction)
- P. Erdős, T. J. Reid, R. Schelp, W. Staton, *Sizes of graphs with induced subgraphs of large maximum
  degree*, Discrete Math. 158 (1996) 283–286
- O. Pikhurko, A. Thomason, *Disjoint subgraphs of large maximum degree*, Discrete Math. 248 (2002)
  125–141
- R. J. Faudree, C. C. Rousseau, R. H. Schelp, *Problems in graph theory from Memphis*, The
  Mathematics of Paul Erdős II (1997), 7–26
- Formal statement: [google-deepmind/formal-conjectures, ErdosProblems/614.lean](https://github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/ErdosProblems/614.lean) (Apache 2.0)
