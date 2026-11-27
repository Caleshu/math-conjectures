# Inscribed squares in Hamiltonian cycles of the hypercube

**Status:** **False.** A square-free Hamiltonian cycle of $Q_8$ is checked in Lean
(`not_conjecture` in `Counterexample.lean`). Square-free cycles of $Q_9$ and $Q_{10}$ are in
`computations/counterexamples/`.

## Counterexample

A Hamiltonian cycle of $Q_8$ with **no inscribed square**. Vertex $k$ is the point of $\{0,1\}^8$ whose
coordinate $i$ is bit $i$ of $k$, and the cycle visits:

<details><summary>The 256 vertices in cycle order (returning to 0)</summary>

```
0, 8, 9, 11, 27, 19, 147, 145, 177, 185, 57, 41, 33, 161, 163, 131
139, 143, 207, 223, 221, 157, 149, 21, 23, 55, 119, 103, 111, 239, 238, 206
204, 220, 252, 248, 184, 186, 187, 155, 219, 91, 90, 122, 120, 121, 113, 97
96, 100, 102, 230, 166, 164, 165, 181, 245, 241, 240, 224, 160, 168, 40, 104
72, 76, 68, 84, 20, 16, 17, 1, 65, 69, 71, 199, 198, 214, 222, 218
216, 88, 80, 112, 48, 176, 180, 148, 150, 22, 30, 62, 63, 59, 123, 107
105, 109, 77, 13, 141, 140, 172, 188, 189, 191, 175, 167, 39, 38, 6, 70
66, 64, 192, 200, 136, 138, 170, 174, 46, 110, 106, 98, 114, 115, 243, 179
183, 182, 190, 254, 126, 118, 86, 87, 83, 81, 209, 217, 249, 251, 255, 247
215, 151, 135, 133, 129, 128, 144, 208, 212, 213, 197, 205, 201, 73, 89, 25
29, 61, 53, 49, 51, 35, 99, 67, 75, 79, 78, 94, 92, 93, 85, 117
116, 244, 246, 242, 250, 234, 232, 233, 225, 193, 195, 211, 210, 82, 18, 2
3, 7, 15, 47, 45, 44, 36, 52, 54, 50, 58, 42, 43, 171, 235, 203
202, 74, 10, 14, 12, 28, 156, 152, 153, 137, 169, 173, 237, 253, 125, 127
95, 31, 159, 158, 142, 134, 130, 194, 226, 227, 231, 229, 101, 37, 5, 4
132, 196, 228, 236, 108, 124, 60, 56, 24, 26, 154, 146, 178, 162, 34, 32
```
</details>

**Why it disproves the conjecture.** The conjecture says every Hamiltonian cycle of $Q_n$ ($n \ge 2$) has two
edges in the same direction $i$ whose endpoints differ in exactly one further coordinate, that is, two opposite
edges of a 4-cycle. In the list above, consecutive vertices (and the last and first) differ in exactly one bit, and
all 256 vertices occur once, so it is a Hamiltonian cycle. Checking all $\binom{256}{2}$ pairs of its edges finds
no such pair. This is checked by the Lean kernel (`not_conjecture` in `Counterexample.lean`) and independently by
`computations/check_square_free_cycle.py`.

## Statement

Let $H$ be a Hamiltonian cycle in the $n$-dimensional hypercube $Q_n$. $H$ has an
*inscribed square* if it contains two opposite edges of some 4-cycle of $Q_n$.
Equivalently, $H$ uses two edges of the same direction $i$ whose endpoints differ in
exactly one other coordinate.

**Conjecture (Sagols & Morales-Luna, 2010).** For every $n \ge 2$, every Hamiltonian
cycle of $Q_n$ has an inscribed square.

Source: F. Sagols, G. Morales-Luna, *Parity balance of the i-th dimension edges in
Hamiltonian cycles of the hypercube*, arXiv:1009.3304 (2010), Conjecture 5.1.

## Result

**Theorem (`not_conjecture`).** The conjecture is false: $Q_8$ has a Hamiltonian cycle
with no inscribed square.

| n | square-free Hamiltonian cycle? | how we know |
|---|---|---|
| 2–5 | none | exhaustive search, `computations/square_free_search.c` |
| 6 | none | CP-SAT search (shortlist notes) |
| 7 | none (claimed) | SAT refutation with a DRUP proof (audit zip; not re-checked with drat-trim here) |
| 8 | **yes** | Lean kernel check + `check_square_free_cycle.py` |
| 9, 10 | **yes** | `check_square_free_cycle.py` |

So if the $n = 7$ claim holds, the conjecture is true exactly for $n \le 7$ among the cases
checked so far. Whether square-free cycles exist for every $n \ge 8$ is open.

## Files

- `Main.lean`: definitions (`cube`, `flip`, `HasInscribedSquare`) and the statement
  `Conjecture`.
- `Cert.lean`: a general certificate theorem. A list of natural numbers (bit $i$ is
  coordinate $i$) that passes the Boolean check `goodCycle` gives a Hamiltonian cycle of
  `cube n` with no inscribed square (`exists_of_goodCycle`). The square test uses a
  bitmask of edge codes, so the kernel check is fast.
- `Counterexample.lean`: the $Q_8$ cycle, `q8_good : goodCycle 8 … = true` by
  `decide +kernel` (no `native_decide`), and `not_conjecture : ¬ Conjecture`.
- `computations/check_square_free_cycle.py`: a standalone checker written from the
  definition. It checks one Hamiltonian cycle and counts inscribed squares.
  `python3 computations/check_square_free_cycle.py computations/counterexamples/Q8_edges.txt`
- `computations/counterexamples/Q{8,9,10}_{edges,sequence}.txt`: the cycles, as edge
  lists and as vertex and transition sequences.
- `computations/square_free_search.c`: exhaustive backtracking for small $n$.

The counterexample cycles come from an outside SAT-based audit
(`inscribed_squares_audit.zip`). They were re-verified here independently: by the Lean
kernel ($Q_8$) and by a new Python checker that shares no code with the audit ($Q_8$–$Q_{10}$).

## Background

- **Reformulation.** For each direction $i$, take the direction-$i$ edges of $H$ and delete
  coordinate $i$. This gives a set $S_i \subseteq V(Q_{n-1})$. $H$ is square-free exactly
  when every $S_i$ is independent, and $\sum |S_i| = 2^n$.
- **Parity balance.** Sagols–Morales-Luna prove that half of the direction-$i$ edges are
  even and half are odd. Their claimed $n \le 7$ proof used the values
  $\alpha_=(Q_6) = 16$ and $\alpha_=(Q_7) = 40$. In fact $\alpha_=(Q_6) = 20$ and
  $\alpha_=(Q_7) \ge 44$, so that counting argument does not cover $n = 7$.

## Progress

- [x] Formal statement (`Main.lean`)
- [x] Disproof, Lean-verified (`Counterexample.lean`)
- [ ] Independent check of the $n = 7$ DRUP refutation (drat-trim)
- [ ] Square-free cycles for all $n \ge 8$ (e.g. a recursive construction)
