# Inscribed squares in Hamiltonian cycles of the hypercube

**Status:** **False.** A square-free Hamiltonian cycle of $Q_8$ is checked in Lean
(`not_conjecture` in `Counterexample.lean`). Square-free cycles of $Q_9$ and $Q_{10}$ are in
`computations/counterexamples/`.

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
