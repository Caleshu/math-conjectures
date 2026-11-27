Round 5: computer-assisted proofs for V(a,b) (Kuca) and U(a,b) (Finch/Ulam) sequences
aproof.c   gcc -O3 -march=native -o aproof aproof.c
           ./aproof a b N0 maxsteps maxP DIST    (DIST=0: V-sequence, DIST=1: Ulam U-sequence)
           e.g. ./aproof 4 21 600000 2e9 1e9 0   (V(4,21): period 1008 after a ~2e9 transient)
           Stages: exact simulation; Brent cycle on the odd register; even w up to 2u0+4P have r(w)!=1;
           every residue class mod P has a periodic witness pair or an exact count != 1.
V/, U/     one output file per (a,b) case, as produced by the sweeps
compare.py checks proved even-term sets against Kuca's Conjecture 4.1 formulas
sweep2.sh, sweep3.sh  the sweep drivers; vproof.c is the earlier version
