# Open-problems project: handoff for Claude Code

Context: a search for niche, tractable open problems (for an ambitious undergraduate), followed by attempts to solve them.
Everything below was produced in one long Claude session (Nov 26, 2026). **Nothing here has been peer-reviewed.**
Treat every "proved" as "proved by me, needs independent checking".

Two write-ups live as Claude Docs (not in this folder):
- Doc 1 (graph theory + inscribed-squares audit): https://claude.ai/artifact/JwhgQaGr3KzfR7cR9fn46H
- Doc 2 (all fields, Rounds 1–5): https://claude.ai/artifact/139SkxwiKysQWRxYnxZnx6

## Folder layout

| Folder | Topic | Key entry points |
|---|---|---|
| `audit/` | Inscribed squares in hypercube Hamiltonian cycles | `README.md` (has a command table) |
| `round2/` | Digital anomalies search; Kuca V(2,n) even terms | `anomaly_k.c`, `kuca.c`, `k2.txt` |
| `round3/` | Litt's game checker; knight-move sequence; RUNS sequence | `litt.c`, `brute.py`, `knight.c`, `runs.c` |
| `solve/` | Digital anomalies theorem (k = 2); knight-sequence experiments | `anomaly_family.py`, `verify_all.py`, `kappa_search.c`, `kn3.c` |
| `kuca/` | First proof of V(2,5), V(2,9) | `brent.c`, `proof.c` |
| `vab/` | General prover for V(a,b) and U(a,b); sweep outputs | `aproof.c`, `V/`, `U/`, `compare.py` |
| `big/` | Large-budget runs (U(4,7), V(4,25)) | `U_4_7.txt`, `V_4_25.txt` |

Build everything with `gcc -O3 -march=native`; Python scripts need `sympy`, `python-sat`, `ortools` where noted.

## Results

### A. Inscribed squares in hypercube Hamiltonian cycles (Sagols & Morales-Luna, arXiv:1009.3304)
The question: does every Hamiltonian cycle of Q_n contain an "inscribed square", i.e. two opposite edges of some 4-cycle?
- n ≤ 6: yes. There is a hand proof via a counting lemma on equi-independent sets.
- n = 7: yes. A SAT instance shows Q_7 has no square-free 2-factor. The proof is a DRUP certificate (`audit/q7_glucose4.drup`), checked only by my own RUP checker (`rup_check.py`). **drat-trim was not run, so run it.**
- n = 8, 9, 10: **counterexamples**, i.e. square-free Hamiltonian cycles (`solution_Q{8,9,10}_ham.txt`, verified by `check_cycle.py`).
- α₌(Q_n) = 2, 4, 10, 20, 44 for n = 3..7, by exhaustive search (`eqindep.c`).

### B. Digital anomalies (Seraj, arXiv:2512.06056)
Definition: x/y = y + x/B^k, where x has k base-B digits.
- Seraj's Conjecture 4.6 (only two solutions with k = 2) is **false**. For example (20808, 144, 204). There are 25 solutions with B ≤ 200,000 (`round2/k2.txt`).
- **Theorem (new): there are infinitely many k = 2 anomalies.** Let κ₄(N) = ∏ p^⌈v_p(N)/4⌉. If c = κ₄(m²−1) < m, then B = cm, y = c², x = c⁴m²/(m²−1) is an anomaly. The Chebyshev iterates m₀ = 2, m_{r+1} = 2m_r² − 1 satisfy c < m for every r ≥ 1, because m_r² − 1 = 3·4^r·(m₀⋯m_{r−1})².
  - All members are verified exactly to 72 digits.
  - 161 values of m ≤ 10⁷ work; they explain 13 of the 25 small solutions.
  - A complete proof is in Doc 2, Round 4.
- k ≥ 3: still open. The analogous construction gives nothing for m ≤ 10⁷ at k = 3, and under abc it can give only finitely many solutions for each k ≥ 3.
- Next: classify all k = 2 solutions (the 12 with non-square y), and write the note for Seraj.

### C. Kuca's V(a,b) and Finch's U(a,b) additive sequences (Kuca, Acta Arith. 2018, arXiv:1804.09594)
Definitions:
- V: each new term is the least integer greater than the last with exactly one representation as a sum of two earlier terms, not necessarily distinct.
- U (Ulam): the same, but the two summands must be distinct.

Method (`vab/aproof.c`, computer-assisted proof):
1. Simulate exactly to 600,000.
2. Assume the known even set E is complete. Then the odd terms come from a finite shift register.
3. Find the exact cycle with Brent's algorithm.
4. Check that every even w ≤ 2u₀ + 4P has a representation count other than 1.
5. For every residue class mod P, give either a periodic witness pair or an exact count other than 1. This closes the induction for all w.

Validation: the prover reproduces U(2,5) (period 126), U(4,5), V(2,7), and U(4, b ≡ 1 mod 4) (Cassaigne–Finch).

Proved here, each with exactly the conjectured even terms:
- V(2,9): even terms 2, 18, 164. This is the first case of Kuca's Conjecture 3.1 (n − 1 a power of 2).
- V(4, b) for b = 9, 11, 13, 15, 17, 19, 21, 23. The even terms are 4, 2b, 4b + 4, 12b − 4, as in Kuca's Conjecture 4.1.
- V(6, b) for b = 13, 17, 19, 23, 25. The even terms are 6, 2b, 4b + 6.
- V(10, b) for b = 21, 23, 27, 29, 31, 33. The even terms are 10, 2b, 4b + 10, 8b + 10.
- U(4, b) for b ≡ 3 (mod 4): b = 11, 19, 23, 27, 35, 39, 43, 47, 51, 55. The even terms are 4, 2b + 4, 4b + 4. Hinman–Kuca–Schlesinger–Sheydvasser already did "a finite set" of these, so the overlap is unknown.
- U(6,13), U(6,17), U(8,19), U(10,23). Each matches Finch's Conjecture 5.1 set exactly.
- U(4,7): even terms 4, 18, 32, 206 (period 11,301,098, starting by u₀ = 80,188,453). This is the first "b + 1 a power of 2" case of the Finch–Cassaigne conjecture, but it might be in Finch's 1990s computations, so check.

Inconclusive because of budget (not counterexamples; the even terms up to 600,000 always match the prediction):
- V(2,17).
- V(4,25): a 20-minute Brent run with a budget of 8 × 10¹⁰ steps found no cycle.
- V(4, b ≥ 25), V(8, ·), V(12, ·).
- U(4,15), U(4,31), U(4,63).
- Most U(6+, b).

Phenomenon: some periods are short but follow huge transients. V(4,21) has period 1008, but only after about 2 × 10⁹ terms. V(10,31) has period 412 after about 9.6 × 10⁷. This supports Kuca's Observation 6.3.

Next steps:
- Get a uniform proof for one family, for example all V(6,b), in the style of Cassaigne–Finch.
- Independently re-implement `aproof.c` (a second code path) and compare periods and u₀.
- Literature check on Finch's and HKSS's tables of proved U cases.

### D. Litt's game, Conjecture 2 (Basdevant–Hénard–Maurel-Segala–Singh, C. R. Math. 2025)
The conjecture: if [A|A] > [B|B], then for all n ≥ n₀, P(Alice) < P(Bob) < 1/2.
- I checked it exactly with 128-bit counts (`round3/litt.c`, cross-checked against `brute.py`):
  - word length ℓ ≤ 8 for n ≤ 120;
  - ℓ = 9 for n ≤ 80;
  - ℓ = 10 for n ≤ 60.
- There were no violations, and the counts are equal for every n < n₀.
- Still open. Next: make the Janson–Nica–Segert (arXiv:2503.19035) error term explicit for small ℓ, then finish with a finite computation.

### E. Knight's-move sequence, OEIS A394166 (Sigrist 2026): is it a permutation?
Proved:
- The first term ≥ 2^k is a power of two, in fact one of 2^k, 2^(k+1), 2^(k+2).
- Every proper submask of a(n) appears before position n.
- If some s never appears, then eventually no two consecutive terms are both ≡ 0 mod 2^(t+2), where t is the bit length of s.

Data: in 10⁵ terms, the smallest missing number is 895. The full question is still open.

### F. Other candidates (status only; details in Doc 2)
- RUNS-transform sequence A306211: maximum term 5, or unbounded? Reproduced to 1.4 × 10⁹ terms; the maximum is 5.
- Binary Yellowstone sequence A252867: is it a permutation? Open.
- Zeckendorf game strategy; Cameron–Dey order sequences; Currie critical exponents; spectrally arbitrary 2n-conjecture; 1324 inversion monotonicity; stick numbers; symmetric rendezvous; Heesch numbers; polyomino order; Costas arrays of order 32.
- Rejected because solved or claimed solved:
  - Enots Wolley (Nichols, arXiv:2609.18054);
  - weak Bras-Amorós (Liu 2026);
  - Rupert solids (moving fast);
  - Merca-type partition conjectures;
  - others listed in Doc 2.

## Suggested first tasks for Claude Code
1. Re-run every "proved" claim from a clean build, and record the outputs, for example:
   - `cd vab && ./aproof 4 21 600000 2e9 1e9 0`
   - `cd big && ./aproof 4 7 600000 8e10 1.6e9 1`
2. Install drat-trim and check `audit/q7_glucose4.drup` and `audit/alpha6_k11.drup`.
3. Write an independent second implementation of the V/U prover (different code path, e.g. Python + numpy or Rust), and compare periods and u₀.
4. Draft two short notes:
   - the k = 2 digital-anomaly theorem, for Seraj;
   - the V(a,b) case table, for Kuca.
   Do a literature check before sending either.
5. Attack open items: the V(6,b) uniform proof; Litt's game for ℓ = 2 and 3 for all n.
