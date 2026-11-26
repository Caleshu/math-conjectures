# Erdős Problem 614

**Status:** Open in general. This folder proves an exact formula for f(n,k) when
k+2 ≤ n ≤ (3k+2)/2. It also shows the formula stops working at n = 2k+1, and gives
exhaustive computer data for every n ≤ 10.

> **Novelty caveat.** I could not read the erdosproblems.com page or forum thread (the site
> blocks automated access), so I couldn't check whether the results below appear in the
> forum discussion, including the January 2026 Turán-type reformulation. Check there before
> treating them as new. The other sources I could read (the UCSD problem page, the
> formal-conjectures entry, its PR discussion, and web search) give no values or bounds.

## Statement

Let $f(n,k)$ be the minimum number of edges in a graph on $n$ vertices in which every set of
$k+2$ vertices induces a subgraph of maximum degree at least $k$. Determine $f(n,k)$.
([erdosproblems.com/614](https://www.erdosproblems.com/614); Faudree, Rousseau and Schelp,
*Problems in graph theory from Memphis*, 1996.)

Trivially $f(n,k)=0$ when $n<k+2$ (the condition is vacuous) or $k=0$.

## Results

**Notation:** $m = k+2$, $j = n-m$, and $H = \overline{G}$ (the complement of $G$).

### Lemma 1 (complement reformulation)

$G$ is good if and only if $H$ has **no** $m$-vertex set $S$ such that $H[S]$ has minimum degree
$\ge 2$. Therefore
$$f(n,k) = \binom n2 - g(n,k+2),\qquad g(n,m)=\max\{e(H): |H|=n,\ \text{no } m\text{-set } S \text{ with } \delta(H[S])\ge 2\}.$$

*Proof.* Take a vertex $v \in S$ with $|S| = k+2$. Then $\deg_{G[S]}(v) = (k+1) - \deg_{H[S]}(v)$,
so $\deg_{G[S]}(v) \ge k$ iff $\deg_{H[S]}(v) \le 1$. So $S$ fails the condition in $G$ iff
every vertex of $S$ has $H[S]$-degree $\ge 2$. ∎

So the problem is a Turán-type problem: forbid every $m$-vertex graph of minimum degree $\ge 2$.
This is my own derivation; I expect it is the forum's reformulation, but I couldn't check.

### Theorem 2 (new range, proved)

For $k+2 \le n \le \frac{3k+2}{2}$:
$$\boxed{f(n,k) = \frac{(n-k-1)(n+k-2)}{2}}$$
Equivalently $g(n,m) = \binom{m-1}{2} + (n-m+1)$ for $m \le n$ and $2n \le 3m-4$.

**Extremal graph.** Take $H = K_{k+1}$ with each of the other $n-k-1$ vertices joined by a single
edge to the clique. So $G$ is a clique $O$ on $n-k-1$ vertices plus an independent set $I$ of $k+1$
vertices, where each $o\in O$ is adjacent to every vertex of $I$ except its own partner.

### Proposition 3 (sharpness, proved)

For $k \ge 2$: $f(2k+1,k) \le \frac{k(3k-1)}{2} - 1$, one below the formula. So no single formula
of this shape extends past $n = 2k$.

### Conjecture 4 (verified for all n ≤ 10)

The formula of Theorem 2 holds on the full range $k+2 \le n \le 2k$.

## Exact values (exhaustive search, all graphs up to 10 vertices)

$f(n,k)$. Entries marked \* lie in the range $n \le 2k$, where they match the formula
$(n-k-1)(n+k-2)/2$.

| n \ k | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| 4 | 2 | 2\* | | | | | | |
| 5 | 4 | 4 | 3\* | | | | | |
| 6 | 6 | 8 | 7\* | 4\* | | | | |
| 7 | 9 | 12 | 11 | 9\* | 5\* | | | |
| 8 | 12 | 17 | 15 | 15\* | 11\* | 6\* | | |
| 9 | 16 | 23 | 22 | 21 | 18\* | 13\* | 7\* | |
| 10 | 20 | 29 | 29 | 28 | 26\* | 21\* | 15\* | 8\* |

Sanity checks against known results:
- **k = 1:** $f = \binom n2 - \lfloor n^2/4\rfloor$, from Turán's theorem.
- **k = 2:** $f = \binom n2 - \mathrm{ex}(n, C_4)$, matching the known Zarankiewicz values
  4, 6, 7, 9, 11, 13, 16.
- **n = 2k+1 (beyond the range):** the values for (n,k) = (5,2), (7,3), (9,4) are exactly one
  below the formula, as Proposition 3 predicts.

## Proofs

Throughout, a **2-set** is a vertex set $S$ with $\delta(H[S])\ge 2$. If $A$ and $B$ are 2-sets,
so is $A\cup B$.

### Proof of Proposition 3 and the lower bound in Theorem 2

*Lower bound.* Let $H$ be $K_{m-1}$ plus $n-m+1$ pendant edges. A pendant vertex has degree
$\le 1$ in every induced subgraph, so every 2-set lies inside the clique and has at most $m-1$
vertices. So $g(n,m) \ge \binom{m-1}2 + n-m+1$ for all $n \ge m$.

*Proposition 3.* Let $n = 2m-3$ and $H = K_{m-1}$ on $Q$, plus a cycle $z_0z_1\cdots z_{m-2}z_0$
with $z_0 \in Q$ and $z_1, \dots, z_{m-2}$ new. Then $e(H) = \binom{m-1}2 + m-1$, one more than
the formula. Let $S$ be a 2-set and $P = S \cap \{z_1,\dots,z_{m-2}\}$.
- If $P$ is nonempty but proper, pick a maximal run of consecutive path vertices in $P$. Its end
  next to a missing path vertex has $\le 1$ neighbour in $S$, a contradiction.
- So $P = \emptyset$, which forces $S \subseteq Q$ and $|S|\le m-1$; or $P$ is the whole path.
  Then $z_0\in S$ (it is $z_1$'s second neighbour), and $S\cap Q$ is either $\{z_0\}$ or has
  $\ge 3$ vertices (a second clique vertex alone would have degree 1).
- Hence $|S| \in [3,m-1] \cup \{m-1\} \cup [m+1, 2m-3]$, which never equals $m$. ∎

### Proof of the upper bound in Theorem 2

We prove: if $|H| = n = m+j$ with $m \ge 2j+4$ and $H$ has no 2-set of size $m$, then
$e(H) \le \binom{m-1}2 + j + 1$. The proof is by induction on $j$.

**Base case, $j=0$.** $V$ itself is not a 2-set, so some vertex has degree $\le 1$. Deleting it
leaves at most $\binom{m-1}2$ edges.

**Low-degree vertex.** If some $v$ has $\deg v \le 1$, then $H-v$ has no 2-set of size $m$.
Also $m \ge 2(j-1)+4$, so induction gives $e(H) \le \binom{m-1}2 + (j-1) + 1 + 1$.

**Main case.** From now on $\delta(H)\ge 2$ and $j \ge 1$. Suppose for contradiction that
$e(H) \ge T+1$, where $T = \binom{m-1}2+j+1$.

Let $F = \{v : \deg v \ge j+2\}$, with $f = |F|$. Let $L = V\setminus F$; every vertex of $L$ has
degree in $[2, j+1]$. Put $a = m-1-f$, so $|L| = j+1+a$.

*Fact A (high-degree vertices are free).* If $|S| = m$ and $v\in S\cap F$, then
$|N(v)\cap S| \ge \deg v - |V\setminus S| = \deg v - j \ge 2$. So any $m$-subset of $F$ is a
2-set, and therefore $f \le m-1$, i.e. $a \ge 0$.

*Fact B (gluing).* Suppose $W \subseteq L$ and $Y\subseteq F$ satisfy
$|W|+|Y| \le m \le |W|+f$, and every $w\in W$ has $\ge 2$ neighbours in $W\cup Y$. Then
$S = W\cup Y\cup Y'$, for any $Y'\subseteq F\setminus Y$ of the right size, is a 2-set of size $m$.
This uses Fact A for the vertices of $F$. So such $W$ and $Y$ cannot exist.

Call $v\in L$ **good** if it has $\ge 2$ neighbours in $F$, and let $\gamma$ be the number of good
vertices.

*Fact C: $\gamma\le a$.* Otherwise apply Fact B with $a+1$ good vertices as $W$ and $Y=F$
(then $|W|+|Y| = m$).

*Fact D (core of $L$).* Let $C$ be the 2-core of $H[L]$, with $c = |C|$. If $f\ge j$ (so
$|L|\le m$), then $c \le a$. Otherwise apply Fact B with $W=C$ and $Y=\emptyset$. Peeling
$H[L]$ down to $C$ removes vertices that each have $\le 1$ neighbour among the vertices that
remain, so $e(H[L]) \le \binom c2 + |L| - c$.

**Case $a=0$.** By Fact C, no vertex is good. By Fact D (here $f = m-1 \ge j$), $H[L]$ is a forest.
Every $L$-vertex has degree $\ge 2$ but at most one $F$-neighbour, so it has $\ge 1$ neighbour in
$L$. Take a path $P$ between two leaves of a component. Each leaf has an $F$-neighbour. Apply
Fact B with $W = P$ and $Y$ the $\le 2$ leaf attachments: $|W|+|Y|\le j+3\le m$ and
$|W| + f \ge m$. Contradiction.

**Case $a=1$.** The same argument works. Fact D gives $c \le 1$, so $c=0$ and $H[L]$ is a forest.
- If some component has an edge, use a leaf-to-leaf path: $|P|\ge 2=a+1$ and
  $|P|+|Y|\le j+4\le m$.
- Otherwise every $L$-vertex has both of its $\ge 2$ neighbours in $F$, so $\gamma = j+2 > a$,
  contradicting Fact C.

**Case $a \ge 2$.** Let $s=\min(f, j+1)$, the most $F$-neighbours an $L$-vertex can have. By
Fact C, $e(F,L) \le a s + (|L|-a)$: good vertices contribute at most $s$ each and the others at
most 1; when $f=0$ the bound holds trivially, since $e(F,L)=0$. Also $\binom{m-1}2 = \binom f2 + \binom a2 + fa$.

- **(I) $2\le a\le j-1$.** Here $f \ge j+4$ and $s = j+1$. By Fact D,
  $e(H)\le \binom f2 + e(F,L) + |L| + \max(0,\binom a2 - a)$. For $a\ge 3$, $e(H)\le T$ reduces to
  $(a+1)(j+1)\le fa$, which follows from $f\ge 2j+3-a$ and $a(j+2-a)\ge j+1$ on $[3,j-1]$
  (a concave function; check the two endpoints). For $a=2$ it reduces to $2f\ge 3j+4$, true since
  $f = m-3 \ge 2j+1$ and $j\ge 3$.
- **(II) $a\ge\max(2,j)$.** Use
  $e(F,L)+e(L) = \tfrac12\big(\sum_{v\in L}\deg v + e(F,L)\big) \le \tfrac12\big((j+1)|L| + as + |L| - a\big)$.
  Then $e(H)\le T$ reduces to $j(j+1) + a(j+2+s) \le a^2 + 2fa$.
  - If $f\le j+1$ (so $s=f$ and $a \ge m-j-2 \ge j+2$), this is $j(j+1)\le a(m-j-3)$. It holds
    since $m-j-3 \ge j+1$.
  - If $f\ge j+1$ (so $s=j+1$), it is $j(j+1)\le a(2m-2j-5-a)$. The right side is concave in $a$.
    It holds at $a=\max(2,j)$ because $m\ge 2j+4$, and at $a = m-j-2$ because
    $(m-j-2)(m-j-3) \ge (j+2)(j+1)$.

Every case gives $e(H)\le T$, contradicting $e(H) \ge T+1$. ∎

Translating back with $m=k+2$: the condition $m\ge 2j+4$ is $2n\le 3k+2$, and
$\binom n2 - \binom{k+1}2 - (n-k-1) = \frac{(n-k-1)(n+k-2)}2$.

## Verification

All code is in [`computations/`](computations/).

| Check | How | Result |
|---|---|---|
| Lemma 1 numerically | `direct.c` (original definition, on G) vs `sizes.c` (complement form) on all graphs, n ≤ 8 | identical |
| Exact values | `geng` (nauty) piped into `sizes.c`: every graph on ≤ 10 vertices (about 12 million for n = 10) | table above |
| Theorem 2 and Conjecture 4 | compared against the table for n ≤ 10 | all agree |
| Case inequalities in the proof | `check_proof_inequalities.py`: every (m, j, a) with m ≤ 500, exactly as written above | 20,491,124 cases, 0 failures |
| Constructions | `constructions.py` piped into `sizes.c`, sizes up to 16 vertices | pendant graph meets the formula; cycle graph beats it by 1 at n = 2m−3 for m = 4..9 |

The case analysis is also proved by hand for every m. The computer check is a guard against
algebra slips, not part of the proof.

Rebuild the n ≤ 10 data: `cc -O3 -o sizes sizes.c && geng -q 10 | ./sizes 10` (about 10 minutes on 8 cores if
split with `geng res/mod`).

## Progress

- [x] Formal statement in Lean (`Main.lean`: definition matching formal-conjectures, plus the
      statements of Theorem 2, Conjecture 4 and Proposition 3)
- [x] Partial results: exact formula for k+2 ≤ n ≤ (3k+2)/2, proved
- [x] Sharpness of the n ≤ 2k range
- [ ] Close the gap (3k+2)/2 < n ≤ 2k (Conjecture 4)
- [ ] Lean proofs of Theorem 2 and Proposition 3
- [ ] Understand n > 2k (for fixed k as n → ∞, g grows like the Turán number of a family
      containing $K_{2,k}$ and $C_{k+2}$, so it is subquadratic)

## Notes

- **Where the proof is lossy.** The only cases that stop at m ≥ 2j+4 are the counting
  cases. The gluing argument (Fact B) is much stronger than the edge counting needs, so extending
  the path argument from a ∈ {0,1} to larger a looks like the natural route to Conjecture 4.
- **Structure of the hard case.** The largest minimum-degree-2 graphs with no 2-set of size m
  (`out/d2_n*.txt`) decode to dense blobs of size ≤ m−1, with long cycles threaded through blob
  vertices of low connectivity. Example (n = 10, m = 7, 16 edges): $K_5$ minus an edge, plus a
  vertex joined to both ends of the missing edge, plus a 5-cycle through that vertex. Past
  n = 2k the overall extremal graphs use the same trick; see Proposition 3.

## References

- [erdosproblems.com/614](https://www.erdosproblems.com/614)
- [UCSD Erdős problems: A problem on sparse induced subgraphs](https://mathweb.ucsd.edu/~erdosproblems/erdos/newproblems/SparseInducedSubgraphs.html)
- [FRS97] R. J. Faudree, C. C. Rousseau and R. H. Schelp, *Problems in graph theory from Memphis*,
  The Mathematics of Paul Erdős II (1996), 7–26.
- Formal statement: [google-deepmind/formal-conjectures, ErdosProblems/614.lean](https://github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/ErdosProblems/614.lean) (Apache 2.0)
- nauty / `geng`: B. D. McKay and A. Piperno, *Practical graph isomorphism II*, J. Symbolic Comput. 60 (2014).
