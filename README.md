# Math Conjectures

Conjectures I'm working on, each with an informal write-up and a formal statement in
[Lean 4](https://lean-lang.org) using [Mathlib](https://github.com/leanprover-community/mathlib4).

## Layout

```
Conjectures/<Name>/README.md   informal statement, motivation, progress, notes
Conjectures/<Name>/Main.lean   formal statement (and eventually the proof)
Playground.lean                scratch space
templates/conjecture/          template for new conjectures
scripts/new-conjecture.sh      creates a new conjecture folder
```

## Adding a conjecture

```sh
scripts/new-conjecture.sh MyConjecture "My Conjecture"
```

## Building

```sh
lake exe cache get   # download prebuilt Mathlib (first time only)
lake build
```

Unproven conjectures use `sorry`, which Lean reports as a warning, not an error.

## Conjectures

- [Erdős Problem 64 (Erdős–Gyárfás conjecture)](Conjectures/Erdos64/) — Open; statement formalized
- [Erdős Problem 614](Conjectures/Erdos614/) — Open; formula proved (Lean-verified) for k+2 ≤ n ≤ (3k+2)/2, extending Erdős–Reid–Schelp–Staton / Pikhurko–Thomason; fails for all n ≥ 2k+1
- [Altitude of the hypercube](Conjectures/AltitudeQ4/) — f(Q_d) = d fails at d = 4: Lean-verified edge-ordering of Q_4 with no increasing path of length 4, so f(Q_4) ≤ 3
- [Inscribed squares in hypercube Hamiltonian cycles (Sagols–Morales-Luna)](Conjectures/HypercubeSquares/) — **False**; Lean-verified square-free Hamiltonian cycle of Q_8 (also Q_9, Q_10); true for n ≤ 6
