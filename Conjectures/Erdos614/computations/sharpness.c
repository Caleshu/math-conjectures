/*
 * Verifies Proposition 3 (sharpness) straight from the ORIGINAL definition, for n = 2k+1+extra.
 *
 * H = clique on Q = {0,...,k} (k+1 = m-1 vertices)
 *   + cycle 0 - c_1 - c_2 - ... - c_k - 0 of length k+1 (= m-1) through clique vertex 0
 *   + `extra` pendant vertices joined to vertex 0.
 * G = complement of H, on n = 2k+1+extra vertices.
 *
 * Checks: (1) every (k+2)-subset S of V has a vertex with >= k G-neighbours inside S;
 *         (2) e(G) = (n-k-1)(n+k-2)/2 - 1, one below the formula.
 * Usage: ./sharpness kmin kmax extra
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char **argv) {
    int kmin = atoi(argv[1]), kmax = atoi(argv[2]), extra = argc > 3 ? atoi(argv[3]) : 0;
    for (int k = kmin; k <= kmax; k++) {
        int n = 2 * k + 1 + extra;
        if (n > 32) { printf("k=%d: n=%d too large\n", k, n); continue; }
        uint32_t Hadj[32] = {0}, Gadj[32] = {0};
        #define E(a, b) do { Hadj[a] |= 1u << (b); Hadj[b] |= 1u << (a); } while (0)
        for (int a = 0; a <= k; a++) for (int b = a + 1; b <= k; b++) E(a, b);  /* clique Q */
        int prev = 0;                                                          /* cycle    */
        for (int i = 1; i <= k; i++) { int c = k + i; E(prev, c); prev = c; }
        E(prev, 0);
        for (int p = 2 * k + 1; p < n; p++) E(0, p);                           /* pendants */
        uint32_t all = (n == 32) ? 0xffffffffu : ((1u << n) - 1);
        long eH = 0;
        for (int v = 0; v < n; v++) {
            Gadj[v] = all & ~Hadj[v] & ~(1u << v);
            eH += __builtin_popcount(Hadj[v]);
        }
        eH /= 2;
        long eG = (long)n * (n - 1) / 2 - eH;
        long formula = (long)(n - k - 1) * (n + k - 2) / 2;
        /* enumerate all (k+2)-subsets with Gosper's hack */
        int s = k + 2;
        uint64_t S = (1ull << s) - 1, limit = 1ull << n, checked = 0, bad = 0;
        while (S < limit) {
            uint32_t T = (uint32_t)S;
            int ok = 0;
            for (uint32_t R = T; R; R &= R - 1) {
                int v = __builtin_ctz(R);
                if (__builtin_popcount(Gadj[v] & T) >= k) { ok = 1; break; }
            }
            if (!ok) bad++;
            checked++;
            uint64_t c = S & -S, r = S + c;
            S = (((r ^ S) >> 2) / c) | r;
        }
        printf("k=%2d n=%2d: %llu sets of size %d checked, %llu violations; e(G)=%ld, formula=%ld, diff=%ld\n",
               k, n, (unsigned long long)checked, s, (unsigned long long)bad, eG, formula, formula - eG);
    }
    return 0;
}
