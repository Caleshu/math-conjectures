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

- [Erdős Problem 63](Conjectures/Erdos63/) — Solved (Liu–Montgomery 2020); statement formalized
