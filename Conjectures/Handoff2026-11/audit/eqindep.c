/* Exhaustive, solver-free computation for the equi-independence number of Q_n (n <= 6).
 *
 * alpha_eq(Q_n) = 2k  iff k is the largest integer such that some A subset of EVEN
 * with |A| = k has |N(A)| <= 2^(n-1) - k.  (Then B = any k odd vertices outside N(A);
 * same-parity vertices are never adjacent, so A u B is independent and balanced.)
 *
 * Usage: ./eqindep n k   -> decides whether some A (|A|=k, A subset EVEN) has |N(A)| <= 2^(n-1)-k,
 *                           prints a witness or "NONE", and the number of search nodes.
 * Symmetry (sound): translation by an even vector maps EVEN onto EVEN, preserves adjacency and |N(A)|,
 * and can move any element of A to 0, so we may assume 0 is in A.
 * Pruning (sound): N(A) only grows when A grows, so a branch is cut once |N(A)| exceeds the bound.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static int n, k, bound, ne;
static int even[64];             /* even-weight vertices, in increasing order        */
static uint64_t nbr[64];         /* neighbourhood (a set of odd vertices) as bitmask */
static long long nodes = 0;
static int chosen[64];

static int dfs(int start, int depth, uint64_t N) {
    nodes++;
    if (__builtin_popcountll(N) > bound) return 0;
    if (depth == k) {
        printf("witness A = {");
        for (int t = 0; t < k; t++) printf(" %d", chosen[t]);
        printf(" }  |N(A)| = %d\n", __builtin_popcountll(N));
        return 1;
    }
    for (int idx = start; idx < ne; idx++) {
        if (ne - idx < k - depth) break;
        chosen[depth] = even[idx];
        if (dfs(idx + 1, depth + 1, N | nbr[idx])) return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) { fprintf(stderr, "usage: %s n k\n", argv[0]); return 2; }
    n = atoi(argv[1]); k = atoi(argv[2]);
    if (n < 2 || n > 7) { fprintf(stderr, "n must be 2..7 (64-bit masks)\n"); return 2; }
    int V = 1 << n, half = V / 2;
    bound = half - k;
    /* index odd vertices 0..half-1 */
    int oddidx[128]; int no = 0;
    for (int v = 0; v < V; v++) if (__builtin_popcount(v) & 1) oddidx[v] = no++;
    ne = 0;
    for (int v = 0; v < V; v++) if (!(__builtin_popcount(v) & 1)) {
        uint64_t m = 0;
        for (int i = 0; i < n; i++) m |= 1ULL << oddidx[v ^ (1 << i)];
        even[ne] = v; nbr[ne] = m; ne++;
    }
    /* force vertex 0 (index 0) into A */
    chosen[0] = 0;
    int found = (k == 0) ? 1 : dfs(1, 1, nbr[0]);
    if (!found) printf("NONE: every A subset of EVEN with |A| = %d has |N(A)| > %d\n", k, bound);
    printf("n=%d k=%d bound=%d search nodes=%lld\n", n, k, bound, nodes);
    return 0;
}
