/* Digital anomalies with k = 2 (Seraj, arXiv:2512.06056): positive integers x, y, B >= 2 with
 *   x / y = y + x / B^2   and   B <= x < B^2.
 * Clearing denominators: x (B^2 - y) = y^2 B^2, so with t = B^2 - y:  x = y^2 B^2 / t.
 * (Direct search over y; no reformulation is trusted: the defining equation is checked exactly.)
 * Bounds used only to limit the loop: x < B^2 forces y^2 + y < B^2, so y < B. */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned __int128 u128;
int main(int argc, char **argv) {
    long N = atol(argv[1]); long found = 0;
    for (long B = 2; B <= N; B++) {
        u128 B2 = (u128)B * B;
        for (long y = 1; y < B; y++) {
            u128 t = B2 - y;
            u128 num = (u128)y * y * B2;
            if (num % t) continue;
            u128 x = num / t;
            if (x < (u128)B || x >= B2) continue;
            /* exact check of x/y = y + x/B^2  <=>  x * B^2 == y^2 * B^2 + x * y */
            if (x * B2 != (u128)y * y * B2 + x * (u128)y) { printf("BUG\n"); return 1; }
            printf("anomaly: x=%llu y=%ld B=%ld\n", (unsigned long long)x, y, B); found++;
        }
    }
    printf("searched B <= %ld, found %ld\n", N, found);
    return 0;
}
