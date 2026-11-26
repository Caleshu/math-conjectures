/*
 * Exhaustive search for Erdős Problem 614 (complement formulation).
 *
 * Reads graphs in graph6 format (e.g. from nauty's `geng`) on stdin. For each graph H,
 * computes the set of sizes s such that some s-vertex set S has min degree >= 2 in H[S].
 *
 * For each m it reports the maximum number of edges of an input graph that has NO such
 * set of size m, plus one witness graph (graph6).  Since
 *     f(n,k) = C(n,2) - g(n,k+2),   g(n,m) = max{ e(H) : no m-set S with delta(H[S]) >= 2 },
 * feeding ALL graphs on n vertices gives exact values of f(n,k).
 *
 * Usage:  geng -q n | ./sizes n
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 16

static int n;
static unsigned adj[MAXN];

static int parse_g6(const char *s) {
    int nn = s[0] - 63, k = 0, bit = 0;
    const char *p = s + 1;
    memset(adj, 0, sizeof adj);
    int val = 0;
    for (int j = 1; j < nn; j++)
        for (int i = 0; i < j; i++) {
            if (bit == 0) { val = *p++ - 63; bit = 6; }
            bit--;
            if ((val >> bit) & 1) { adj[i] |= 1u << j; adj[j] |= 1u << i; k++; }
        }
    return k; /* number of edges */
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s n\n", argv[0]); return 1; }
    n = atoi(argv[1]);
    int best[MAXN + 1];
    char wit[MAXN + 1][64];
    for (int m = 0; m <= n; m++) { best[m] = -1; wit[m][0] = 0; }

    char line[256];
    long count = 0;
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\r\n")] = 0;
        if (line[0] - 63 != n) { fprintf(stderr, "bad n\n"); return 1; }
        int e = parse_g6(line);
        count++;
        unsigned sizes = 0; /* bit s set iff some s-set has min degree >= 2 */
        unsigned full = (n == 32) ? 0xffffffffu : ((1u << n) - 1);
        for (unsigned S = 1; S <= full; S++) {
            int s = __builtin_popcount(S);
            if (s < 3 || (sizes >> s & 1)) continue;
            int ok = 1;
            for (unsigned T = S; T; T &= T - 1) {
                int v = __builtin_ctz(T);
                if (__builtin_popcount(adj[v] & S) < 2) { ok = 0; break; }
            }
            if (ok) sizes |= 1u << s;
        }
        for (int m = 0; m <= n; m++)
            if (!(sizes >> m & 1) && e > best[m]) { best[m] = e; strcpy(wit[m], line); }
    }
    fprintf(stderr, "read %ld graphs\n", count);
    int N2 = n * (n - 1) / 2;
    printf("n=%d\n", n);
    for (int m = 3; m <= n; m++)
        printf("m=%d k=%d  g=%d  f=%d  witness_H=%s\n", m, m - 2, best[m], N2 - best[m], wit[m]);
    return 0;
}
