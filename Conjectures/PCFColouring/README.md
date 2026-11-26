# Proper conflict-free colouring at maximum degree 4

**Status:** Open. Computer-verified for all connected graphs with $\Delta \le 4$ on at most
12 vertices.

## Statement

A *proper conflict-free (pcf) colouring* is a proper vertex colouring in which every
non-isolated vertex has a colour appearing exactly once in its neighbourhood. $\chi_{pcf}$ is
the least number of colours needed.

**Conjecture (Caro, Petruševski, Škrekovski).** Every connected graph with $\Delta \ge 3$ has
$\chi_{pcf} \le \Delta + 1$. For $\Delta = 4$ this says 5 colours suffice. Known: true for
$\Delta = 3$ (Liu–Reed); for $\Delta = 4$ the best general bound is 7 (even pcf
7-choosable, arXiv:2508.20521).

## Computation

`computations/pcf.c` reads graph6 from `nauty`'s `geng` and decides $\chi_{pcf} \le K$ by
backtracking. A vertex is checked once all its neighbours are coloured, and colours are
introduced in order for symmetry breaking.

```
cc -O2 -o pcf computations/pcf.c
geng -cq -D4 12 | ./pcf 5
```

| n | connected graphs with $\Delta \le 4$ | needing 6 colours |
|---|---|---|
| 3–10 | 103,998 | 0 |
| 11 | 739,335 | 0 |
| 12 | 6,800,637 | 0 |

Sanity check: the checker reports that $C_5$ needs 5 colours (it rejects 4), and it finds
graphs with $\Delta \le 4$ that need 5 colours (2, 2, 11, 28 of them for n = 5, 6, 7, 8).
