# Altitude of the hypercube

**Status:** The question "is $f(Q_d) = d$?" has answer **no for every $d \ge 4$**:
$f(Q_d) \le d - \lfloor d/4 \rfloor$, **Lean-verified for all $d$** (`Product.lean`,
theorems `altitude_le` and `altitude_lt`; standard axioms only). Small values:
$f(Q_2) = 2$, $f(Q_3) = 3$, $f(Q_4) = 3$.

## Statement

An *edge-ordering* of a graph $G$ labels its edges $1, \dots, |E|$ bijectively. An
*increasing path* traverses edges with strictly increasing labels. The *altitude* $f(G)$
is the minimum, over all edge-orderings, of the length (in edges) of the longest
increasing path.

**Question (folklore).** Is $f(Q_d) = d$ for the $d$-dimensional hypercube?

Source: De Silva, Molla, Pfender, Retter, Tait, *Increasing paths in edge-ordered graphs:
the hypercube and random graph*, Electron. J. Combin. 23(2) (2016), arXiv:1502.03146.
They say $f(Q_d) = d$ has been conjectured, citing only a web page. The known bounds were
$d / \log d \lesssim f(Q_d) \le d$; the upper bound orders edges in blocks by direction.

## Results

### 1. $f(Q_4) \le 3$ (Lean-verified)

`AltitudeQ4.lean` gives an explicit labeling of the 32 edges of $Q_4$ and proves by
`decide` (plain Lean core, no Mathlib):

- `labels_bijective`: the labels are a bijection from the edges to $1..32$.
- `no_increasing_path_4`: no path of 5 distinct vertices has increasing labels.
- `exists_increasing_path_3`: this labeling does have an increasing path with 3 edges.
- `exists_increasing_closed_walk_4`: an increasing closed walk with 4 edges exists, so the
  distinctness condition matters.

### 2. Product bound: $f(G \,\square\, H) \le f(G) + f(H)$

**Lemma.** For graphs $G, H$, $f(G \square H) \le f(G) + f(H)$.

*Proof.* Fix orderings of $G$ and $H$ achieving $f(G)$ and $f(H)$. Order the edges of
$G \square H$ as follows. First come all *$G$-edges* $\{(g,h),(g',h)\}$, sorted by the label
of $gg'$ in $G$, with ties between different copies $G \times \{h\}$ broken arbitrarily.
Then come all *$H$-edges* $\{(g,h),(g,h')\}$, sorted the same way by the label of $hh'$.

Take an increasing path $P$. Every $G$-edge comes before every $H$-edge, so $P$ is an initial
segment of $G$-edges followed by a final segment of $H$-edges. The $G$-segment is connected
and uses only $G$-edges, so it stays in one copy $G \times \{h\}$. Within one copy the
order is the order of $G$, so the segment is an increasing path of $G$ and has at most $f(G)$
edges. The $H$-segment likewise has at most $f(H)$ edges. $\square$

**Lean.** `Product.lean` formalizes this for cubes: `altLE_add : AltLE a ka → AltLE b kb →
AltLE (a + b) (ka + kb)`, where a vertex of $Q_{a+b}$ is a number $< 2^{a+b}$ split into its low
$a$ bits and high $b$ bits. Base cases: `altLE_zero`, `altLE_one`, and `altLE_four` (reusing
the $Q_4$ labeling).

**Corollary.** $f(Q_{4k+r}) \le 3k + r$ for $0 \le r < 4$, i.e.
$f(Q_d) \le d - \lfloor d/4 \rfloor$. Use $Q_{4k+r} = Q_4^{\,\square k} \square Q_1^{\,\square r}$
with $f(Q_4) \le 3$ and $f(Q_1) = 1$. In particular $f(Q_d) < d$ for every $d \ge 4$.

Computational check (`computations/alt_prod.c`): the ordering "Q₄-directions by the Q₄
labels, then one block per remaining direction" has longest increasing path exactly
$d - 1$ for $d = 4, \dots, 8$. `computations/alt_prod44.c` orders $Q_8 = Q_4 \square Q_4$
and gets exactly $6$.

### 3. Small values

| $d$ | $f(Q_d)$ | how |
|---|---|---|
| 1 | 1 | trivial |
| 2 | 2 | exhaustive (`alt_exact 2 1`) |
| 3 | 3 | exhaustive: no ordering of $Q_3$ avoids an increasing 3-edge path (`alt_exact 3 2`, 44,337 nodes; re-checked by independent Python code) |
| 4 | 3 | upper bound Lean-verified; lower bound by restricting any ordering of $Q_4$ to a $Q_3$ subcube |
| 5 | 3 or 4 | $\le 4$ by the product bound. Simulated annealing (`alt_sa.c`, 4 runs) never found an ordering with no increasing 4-edge path: best 130 such paths. |

Lower bounds are monotone: $f(Q_d) \ge f(Q_3) = 3$ for $d \ge 3$, because an ordering of
$Q_d$ restricted to a subcube is an ordering of that subcube.

## Open

- Is $f(Q_5) = 4$? If $f(Q_5) = 3$, the corollary improves to $f(Q_d) \le 3d/5 + O(1)$.
- What is the right growth rate? Now $d/\log d \lesssim f(Q_d) \le 3d/4 + O(1)$. Any $Q_m$
  with $f(Q_m)/m < 3/4$ lowers the constant.

## Files

- `AltitudeQ4.lean`: the $Q_4$ certificate (plain Lean core).
- `Product.lean`: the product lemma and `altitude_le : ∀ d, AltLE d (d - d / 4)`. Here an
  edge-ordering is a symmetric labeling injective on edges (equivalent to a bijection onto
  $1..|E|$), and an increasing path is a list of distinct vertices with consecutive ones
  adjacent and labels strictly increasing.
- `computations/alt_exact.c`: exact backtracking. `./alt_exact d L` decides whether $Q_d$
  has an ordering with no increasing path of $L+1$ edges.
- `computations/alt_prod.c`, `alt_prod44.c`: build the product orderings and compute their
  longest increasing paths exactly.
- `computations/alt_sa.c`: simulated annealing for good orderings.
