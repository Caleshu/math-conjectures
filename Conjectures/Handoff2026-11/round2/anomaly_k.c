/* Digital anomalies x/y = y + x/B^k with B^(k-1) <= x < B^k; exact check with 128-bit integers.
   x = y^2 B^k / (B^k - y); x < B^k forces y^2 + y < B^k. */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
typedef unsigned __int128 u128;
int main(int argc, char **argv) {
    int k = atoi(argv[1]); long N = atol(argv[2]); long found = 0;
    for (long B = 2; B <= N; B++) {
        u128 Bk = 1; for (int i = 0; i < k; i++) Bk *= B;
        u128 Bk1 = Bk / B;
        long ymax = (long)sqrtl((long double)Bk) + 1;
        for (long y = 1; y <= ymax; y++) {
            u128 t = Bk - y; if ((u128)y * y + y >= Bk) break;
            u128 num = (u128)y * y * Bk;
            if (num % t) continue;
            u128 x = num / t;
            if (x < Bk1 || x >= Bk) continue;
            if (x * Bk != (u128)y * y * Bk + x * (u128)y) { printf("BUG\n"); return 1; }
            printf("k=%d anomaly: x=%llu y=%ld B=%ld\n", k, (unsigned long long)x, y, B); found++;
        }
    }
    printf("k=%d: searched B <= %ld, found %ld\n", k, N, found);
    return 0;
}
