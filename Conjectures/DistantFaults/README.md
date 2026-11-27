# Hamiltonian cycles in hypercubes with distant faulty vertices

**Status:** Open. **No counterexample for n ≤ 6** (exhaustive over all sets containing vertex 0), in both the main form
and the stronger form. The n = 7 run (main form) is in progress.

## Statement

Let F ⊆ V(Q_n) be *balanced* (equally many even and odd vertices), with every two vertices of F at Hamming distance at
least 3. **Conjecture:** Q_n − F has a Hamiltonian cycle. A stronger form requires only that vertices of the same parity
be at distance at least 4.

Source: Gregor and Škrekovski, *Long cycles in hypercubes with distant faulty vertices*, Discrete Math. Theor. Comput.
Sci. 11(1) (2009) 185–198, Conjecture 1.

## Computation

`computations/faulty.c` (`./faulty n mode`):
- It enumerates every valid balanced F with |F| ≥ 2 that contains vertex 0. This is no loss of generality, because Q_n
  is vertex-transitive.
- For each F, it searches for a Hamiltonian cycle of Q_n − F by backtracking with forced-move pruning. It makes 300
  randomized restarts of 2·10⁵ nodes each, then one run of 2·10⁸ nodes.
- Any F without a cycle found is reported as NOT HAMILTONIAN or TIMEOUT.

| n | mode 0 (distance ≥ 3) | mode 1 (same parity ≥ 4) |
|---|---|---|
| ≤ 5 | all sets, 0 failures | all sets, 0 failures |
| 6 | 2,376 sets, 0 failures | 27,528 sets, 0 failures |
| 7 | running | not run |

A failure would only be a *candidate* counterexample (it could be a timeout). No failures occurred, so every F tested
has an explicit Hamiltonian cycle.

`computations/ftest.c` contains negative and positive controls. Q₃ − {0,3} is unbalanced and correctly reported
non-Hamiltonian; Q₃ − {0,7} is reported Hamiltonian.
