# Altitude of the hypercube

**Status:** The question "is $f(Q_d) = d$?" has answer **no** at $d = 4$: $f(Q_4) \le 3$,
Lean-verified (`AltitudeQ4.lean`). The general question of how $f(Q_d)$ grows is open.

## Statement

An *edge-ordering* of a graph $G$ labels its edges $1, \dots, |E|$ bijectively. An
*increasing path* traverses edges with strictly increasing labels. The *altitude* $f(G)$
is the minimum, over all edge-orderings, of the length (in edges) of the longest
increasing path.

**Question (folklore).** Is $f(Q_d) = d$ for the $d$-dimensional hypercube?

Source: De Silva, Molla, Pfender, Retter, Tait, *Increasing paths in edge-ordered graphs:
the hypercube and random graph*, Electron. J. Combin. 23(2) (2016), arXiv:1502.03146.
They say $f(Q_d) = d$ has been conjectured, citing only a web page.

## Known

- $d / \ln d \le f(Q_d) \le d$. The upper bound orders edges in blocks by direction
  ($f(G) \le \chi'(G)$).

## Result

`AltitudeQ4.lean` gives an explicit labeling of the 32 edges of $Q_4$ and proves by
`decide` (kernel evaluation, plain Lean core, no Mathlib):

- `labels_bijective`: the labels are a bijection from the edges to $1..32$.
- `no_increasing_path_4`: no path of 5 distinct vertices has increasing labels.
  So $f(Q_4) \le 3 < 4$.
- `exists_increasing_path_3`: this labeling does have an increasing path with 3 edges.
- `exists_increasing_closed_walk_4`: an increasing closed walk with 4 edges exists, so the
  distinctness condition matters.

The matching lower bound $f(Q_4) \ge 3$ (so $f(Q_4) = 3$) comes from a SAT computation and
is not formalized here.

## Progress

- [x] $f(Q_4) \le 3$, Lean-verified
- [ ] $f(Q_4) \ge 3$ formalized or independently re-checked
- [ ] $f(Q_3)$ exactly
- [ ] Behaviour of $f(Q_d)$ for larger $d$
