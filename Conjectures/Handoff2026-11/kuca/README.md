Kuca's conjecture, cases n = 5 and n = 9 (computer-assisted proof)
brent.c   gcc -O3 -march=native -o brent brent.c; ./brent 9 3e10   -> period and preperiod of the odd-term register
proof.c   gcc -O3 -march=native -o proof proof.c; ./proof 9 803114720 82663673   (needs ~250 MB, ~45 s)
          ./proof 5 694 2079
          Steps: exact simulation to 4n^2+200; recurrence; periodicity window check; every even w up to
          2u0+4P has >=2 representations; witness pair for every even residue mod P (covers all larger w).
period.c, evencheck.c, triple.c, period2.c: exploratory tools (simple period search; triple-overlap counts).
