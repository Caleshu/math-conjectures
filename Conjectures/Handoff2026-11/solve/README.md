Round 4 code
anomaly_family.py  Chebyshev family of k=2 digital anomalies, exact Fraction check up to r=6 (needs sympy).
verify_all.py      Independent sympy search m<=1e5 with kappa4(m^2-1)<m; exact check of each anomaly;
                   cross-check against round2/k2.txt (exhaustive list, B<=200000).
kappa_search.c     Sieve: count m<=M with kappa4(m^2-1)<m (k=2) and kappa6(m^3-1)<m (k=3).
                   gcc -O2 -o kappa_search kappa_search.c -lm; ./kappa_search 10000000
kn2.c, kn3.c       Knight's-move sequence A394166: record terms; how the smallest missing number is placed;
                   computational check of the submask lemma.
