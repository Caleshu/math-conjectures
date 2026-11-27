/* V(2,n): a1=2, a2=n; a_{m+1} = least integer > a_m with exactly one representation as a sum of two
   (not necessarily distinct) earlier terms (unordered). Report all even terms up to N. */
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    long n = atol(argv[1]), N = atol(argv[2]);
    unsigned char *r = calloc(2*N+2, 1); long *t = malloc(sizeof(long)*N); long m = 0;
    #define ADD(a) do { for (long i = 0; i < m; i++) { long s = t[i] + (a); if (s <= N && r[s] < 2) r[s]++; } \
                        if (2*(a) <= N && r[2*(a)] < 2) r[2*(a)]++; t[m++] = (a); } while (0)
    ADD(2); ADD(n);
    printf("n=%ld even terms:", n); printf(" 2"); if (n % 2 == 0) printf(" %ld", n);
    for (long c = n + 1; c <= N; c++) if (r[c] == 1) { ADD(c); if (c % 2 == 0) printf(" %ld", c); }
    printf("   (searched to %ld, %ld terms)\n", N, m);
    return 0;
}
