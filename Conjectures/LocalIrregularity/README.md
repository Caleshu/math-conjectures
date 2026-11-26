# Local Irregularity Conjecture for subcubic graphs

**Status:** Open. Computer-verified for all connected subcubic graphs on at most 16 vertices:
every decomposable one has $\mathrm{lir} \le 3$.

## Statement

A graph is *locally irregular* if adjacent vertices have different degrees. $\mathrm{lir}(G)$
is the least $k$ such that $E(G)$ splits into $k$ locally irregular subgraphs. The revised
conjecture of Sedlar and Škrekovski (2022): every connected graph that admits such a split,
except the bow-tie graph, has $\mathrm{lir}(G) \le 3$. Target: subcubic graphs.

## Computation

`computations/lir.c` reads graph6 and finds the least $k \le 6$ for which an edge
$k$-colouring with locally irregular colour classes exists. The search colours edges one at
a time, checks each vertex once all its edges are coloured, and introduces colours in order.
Graphs with no such colouring for $k \le 6$ are listed as not decomposable. For subcubic
graphs that is exact, since decomposable subcubic graphs have $\mathrm{lir} \le 4$
(Lužar et al.).

```
cc -O2 -o lir computations/lir.c
geng -cq -D3 16 | ./lir
```

| n | connected subcubic | lir=1 | lir=2 | lir=3 | lir≥4 | not decomposable |
|---|---|---|---|---|---|---|
| 10 | 1,733 | 7 | 1,628 | 92 | 0 | 6 |
| 12 | 19,430 | 13 | 18,760 | 645 | 0 | 12 |
| 14 | 262,044 | 29 | 256,541 | 5,450 | 0 | 24 |
| 15 | 1,016,740 | 45 | 999,851 | 16,810 | 0 | 34 |
| 16 | 4,101,318 | 66 | 4,043,837 | 57,363 | 0 | 52 |

(All n from 3 to 16 were run; none has lir ≥ 4.) The non-decomposable counts include the
odd paths and odd cycles, as expected.
