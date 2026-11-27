# Inscribed-squares audit (Sagols & Morales-Luna, arXiv:1009.3304)

Requirements: Python 3, `pip install python-sat ortools`, and a C compiler.
Vertices are integers; bit k is coordinate k (0 = least significant).

| File | What it shows | Command |
| --- | --- | --- |
| verify20.py | The 20-set in Q_6 is balanced and independent (no solver) | `python3 verify20.py` |
| eqindep.c | Exact alpha_eq by exhaustive search (no solver), n <= 7 | `gcc -O2 eqindep.c -o eqindep && ./eqindep 6 11` (NONE means alpha_eq(Q_6) <= 20); `./eqindep 7 23` (about 10^10 nodes) |
| alpha6_proof.py, alpha6_k11.cnf, alpha6_k11.drup | SAT refutation of an 11+11 set in Q_6, with a DRUP proof | `python3 rup_check.py alpha6_k11.cnf alpha6_k11.drup` |
| crosscheck.py | alpha_eq by SAT for n <= 6; recounts the paper's auxiliary graph Q'_n | `python3 crosscheck.py 7` |
| q7_proof.py, q7_2factor_sym.cnf, q7_glucose4.drup | No square-free 2-factor in Q_7 (with symmetry normalisation) | `python3 rup_check.py q7_2factor_sym.cnf q7_glucose4.drup` |
| validate_cnf.py | Decodes every clause of the Q_7 CNF and checks that it is valid | `python3 validate_cnf.py q7_2factor_sym.cnf` |
| rup_check.py | A minimal forward-RUP proof checker (my own; drat-trim is the standard alternative) | see above |
| sqfree_sat.py | Square-free 2-factor / Hamiltonian-cycle search with lazy connectivity cuts | `python3 sqfree_sat.py 8 ham` |
| solution_Q{8,9,10}_ham.txt | Square-free Hamiltonian cycles (one edge per line) | `python3 check_cycle.py solution_Q8_ham.txt` |
| solution_Q*_sequence.txt | The same cycles as vertex and transition sequences | |
| check_cycle.py | Standalone checker: one Hamiltonian cycle, zero opposite-edge pairs (all pairs tested) | as above |
| local_q3.py, local_q4.c | Local configuration enumeration; shows that subcube averaging cannot settle n = 7 | |
| hypercube_check.py | The first CP-SAT exploration (alpha_eq and the direct Hamiltonian search for n <= 6) | |

Independent re-checks I could not run here: drat-trim on the two DRUP proofs.
