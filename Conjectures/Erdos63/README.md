# Erdős Problem 63

**Status:** Solved (affirmatively) — see below. Formalized statement in `Main.lean`; proof not yet written here.

## Statement

Does every graph with infinite chromatic number contain a cycle of length $2^n$ for
infinitely many $n$?

Conjectured by Mihók and Erdős.

## Known results

- Solved affirmatively, following the work of Liu and Montgomery [LiMo20], who solved
  the Erdős–Hajnal odd cycle problem.
- A formal Lean 4 proof exists:
  [plby/lean-proofs — Erdos63.lean](https://github.com/plby/lean-proofs/blob/8822f7ddef30fadbd92e1c6ab4ed897af356af5e/src/latest/ErdosProblems/Erdos63.lean#L46)

## Progress

- [x] Formal statement in Lean (`Main.lean`)
- [ ] Partial results
- [ ] Full proof

## Notes

The formal statement is adapted from
[google-deepmind/formal-conjectures](https://github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/ErdosProblems/63.lean)
(Apache 2.0), rewritten to use only core Mathlib (`Walk.IsCycle` instead of `cycleLengths`).

## References

- [erdosproblems.com/63](https://www.erdosproblems.com/63)
- [dBEr51] N. G. de Bruijn and P. Erdős, *A colour problem for infinite graphs and a problem
  in the theory of relations*, Indag. Math. (1951), 369–373.
- [ErHa66] P. Erdős and A. Hajnal, *On chromatic number of graphs and set-systems*,
  Acta Math. Acad. Sci. Hungar. (1966), 61–99.
- [LiMo20] H. Liu and R. Montgomery, *A solution to Erdős and Hajnal's odd cycle problem*,
  arXiv:2010.15802 (2020).
- [Re24] C. Reiher, *Graphs of large girth*, arXiv:2403.13571 (2024).
