# Additive (lucky) colouring of bipartite graphs

**Status:** Open. Computer-verified: every connected bipartite graph on at most 15 vertices has
$\eta \le 2$.

## Statement

Give each vertex a label $\ell(v) \in \{1, \dots, k\}$ and let $S(v)$ be the sum of the labels
of the neighbours of $v$. The labelling is *additive* if $S(u) \ne S(v)$ for every edge $uv$.
$\eta(G)$ is the least such $k$.

**Conjecture (Czerwiński, Grytczuk, Żelazny 2009).** $\eta(G) \le \chi(G)$. For bipartite
graphs this says $\eta \le 2$; as of 2014 it was not even known whether $\eta$ is bounded on
bipartite graphs (Bartnicki et al., Graphs Combin. 30 (2014)).

## Computation

`computations/additive.c` reads graph6 and decides $\eta \le 2$ by backtracking over labels
in $\{1, 2\}$. An edge is checked as soon as both endpoints have all their neighbours
labelled.

```
cc -O2 -o additive computations/additive.c
geng -cbq 15 | ./additive
```

| n | connected bipartite graphs | with $\eta > 2$ |
|---|---|---|
| 1–11 | 30,614 | 0 |
| 12 | 212,780 | 0 |
| 13 | 2,241,730 | 0 |
| 14 | 31,193,324 | 0 |
| 15 | 575,252,112 | 0 |

(n = 15 was run in 4 parts with `geng -cbq 15 i/4`.) A bipartite graph with $\eta = 3$ would
disprove the conjecture; none exists on at most 15 vertices.
