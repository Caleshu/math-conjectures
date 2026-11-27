Round 3 code (exact computations; finite ranges only, not proofs)

litt.c    Litt's game, Basdevant et al. Conjecture 2. gcc -O2 -o litt litt.c; ./litt L NMAX
          Checks every ordered pair with [A|A]>[B|B]: P(A)<P(B) for n>=n0, P(A)=P(B) for n<n0, 2P(B)<1.
          Counts are __int128 (exact for NMAX<=125). Results: L<=8 n<=120, L=9 n<=80, L=10 n<=60, no violations.
brute.py  Brute-force cross-check: python3 brute.py L N
knight.c  OEIS A394166: ./knight NTERMS LOG2CAP  (e.g. ./knight 100000 31)
runs.c    OEIS A306211 generations: ./runs CAP  (e.g. ./runs 1500000000; needs CAP bytes of RAM)
