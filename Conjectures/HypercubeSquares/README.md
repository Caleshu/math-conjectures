# Inscribed squares in Hamiltonian cycles of the hypercube

**Status:** Open (n ≤ 6 checked by computer; n = 7 is the smallest open case)

## Statement

Let $H$ be a Hamiltonian cycle in the $n$-dimensional hypercube $Q_n$. $H$ has an
*inscribed square* if it contains two opposite edges of some 4-cycle of $Q_n$.
Equivalently, $H$ uses two edges of the same direction $i$ whose endpoints differ in
exactly one other coordinate.

**Conjecture (Sagols & Morales-Luna, 2010).** For every $n \ge 2$, every Hamiltonian
cycle of $Q_n$ has an inscribed square.

Formal statement: `hamiltonian_cycle_has_inscribed_square` in `Main.lean`.

## Source

F. Sagols, G. Morales-Luna, *Parity balance of the i-th dimension edges in Hamiltonian
cycles of the hypercube*, arXiv:1009.3304 (2010), Conjecture 5.1.

## Reformulation

For each direction $i$, let $S_i \subseteq V(Q_{n-1})$ be the set of direction-$i$
edges of $H$, each projected by deleting coordinate $i$. Then $H$ is square-free
exactly when every $S_i$ is an independent set in $Q_{n-1}$. The sizes satisfy
$\sum_i |S_i| = 2^n$.

A local consequence: if $H$'s direction sequence contains the pattern $a\,b\,a$ (three
consecutive edges), the first and third edges are opposite sides of a square. So a
square-free $H$ has a direction sequence with no $aba$ pattern, cyclically. That
condition alone isn't enough to give a contradiction.

## Known results

- Sagols–Morales-Luna prove *parity balance*: half of the direction-$i$ edges of $H$ are
  even and half are odd. So each $S_i$ is a balanced independent set. If some $|S_i|$
  exceeds the balanced independence number $\alpha_=(Q_{n-1})$, then $H$ has a square.
- They also prove the conjecture for any $H$ with more than $2^{n-2}$ edges in one direction.
- They claim $n \le 7$ using $\alpha_=(Q_3..Q_7) = 2,4,10,16,40$. That table appears to be
  wrong: CP-SAT gives $\alpha_=(Q_6) = 20$ and $\alpha_=(Q_7) \ge 44$. Then
  $7 \cdot 20 = 140 \ge 128$, so the counting argument does not settle $n = 7$.
  (Source: the "Obscure Open Problems in Graph Theory: A Verified Shortlist" notes, problem 1.)

## Computations

`computations/square_free_search.c` is an exhaustive backtracking search for square-free
Hamiltonian cycles. It prunes each partial path as soon as it closes a square.

```
cc -O2 -o sfs computations/square_free_search.c && ./sfs 5
```

| n | square-free Hamiltonian cycles |
|---|---|
| 3 | 0 |
| 4 | 0 |
| 5 | 0 (0.06 s) |
| 6 | 0 (per the shortlist's SAT search; this program is slow at n = 6) |

## Progress

- [x] Formal statement in Lean (`Main.lean`)
- [x] Computer check for n ≤ 5 (n ≤ 6 reported independently)
- [ ] n = 7
- [ ] Full proof

## Approaches

1. Sharpen the counting: the $S_i$ are linked because $H$ is a single cycle. Look for
   constraints between $S_i$ and $S_j$ where $H$ turns from direction $i$ to direction $j$.
2. Compute $\alpha_=(Q_n)$ exactly (a vertex-isoperimetric problem within one parity class).
3. Look for a counterexample in $Q_7$/$Q_8$ with SAT plus symmetry breaking.
