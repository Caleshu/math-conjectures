/*
 * Independent check of Erdős 614 straight from the ORIGINAL definition (no complement,
 * no reformulation): reads all graphs G on n vertices (graph6), and for each k reports
 * the minimum number of edges of a G in which every (k+2)-subset S contains a vertex
 * with at least k neighbours inside S.
 *
 * Usage:  geng -q n | ./direct n
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int n;
static unsigned adj[16];

static int parse_g6(const char *s) {
    int nn = s[0] - 63, e = 0, bit = 0, val = 0;
    const char *p = s + 1;
    memset(adj, 0, sizeof adj);
    for (int j = 1; j < nn; j++)
        for (int i = 0; i < j; i++) {
            if (bit == 0) { val = *p++ - 63; bit = 6; }
            bit--;
            if ((val >> bit) & 1) { adj[i] |= 1u << j; adj[j] |= 1u << i; e++; }
        }
    return e;
}

/* does every (k+2)-subset S have a vertex v in S with |N(v) ∩ S| >= k ? */
static int good(int k) {
    int s = k + 2;
    if (s > n) return 1; /* vacuous */
    for (unsigned S = 0; S < (1u << n); S++) {
        if (__builtin_popcount(S) != s) continue;
        int ok = 0;
        for (unsigned T = S; T; T &= T - 1) {
            int v = __builtin_ctz(T);
            if (__builtin_popcount(adj[v] & S) >= k) { ok = 1; break; }
        }
        if (!ok) return 0;
    }
    return 1;
}

int main(int argc, char **argv) {
    n = atoi(argv[1]);
    int best[16];
    for (int k = 0; k < 16; k++) best[k] = 1 << 30;
    char line[256];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\r\n")] = 0;
        int e = parse_g6(line);
        for (int k = 1; k + 2 <= n; k++)
            if (e < best[k] && good(k)) best[k] = e;
    }
    printf("n=%d\n", n);
    for (int k = 1; k + 2 <= n; k++) printf("k=%d  f=%d\n", k, best[k]);
    return 0;
}
