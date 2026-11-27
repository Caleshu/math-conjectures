"""Semantic validator for q7_2factor_sym.cnf (independent re-derivation of the edge numbering).

Edge numbering convention: iterate v = 0..2^n-1, then i = 0..n-1; if u = v XOR 2^i > v, the edge {v,u}
gets the next number, starting from 1.
An UNSAT verdict is sound if EVERY clause is satisfied by every square-free 2-factor H satisfying the
symmetry normalisation. This script checks that each clause is one of:
  (A) -a v -b v -c   with a, b, c three distinct edges at a common vertex        (degree <= 2)
  (B) OR of n-1 distinct edges at a common vertex v                               (degree >= 2)
  (C) -e v -f        with e, f opposite edges of a 4-cycle                        (square-free)
  (D) unit clauses {0,1}, {0,2}, {1,5}                                            (symmetry normalisation)
"""
import sys
n = 7
num = {}; ends = {}
for v in range(1 << n):
    for i in range(n):
        u = v ^ (1 << i)
        if u > v:
            num[(v, u)] = len(num) + 1; ends[len(num)] = (v, u)
def common_vertex(es):
    s = set(ends[es[0]])
    for e in es[1:]: s &= set(ends[e])
    return s
def opposite(e, f):
    (a, b), (c, d) = ends[e], ends[f]
    da, dc = a ^ b, c ^ d                     # directions (as bit masks)
    if da != dc: return False
    x = a ^ c                                 # with a, c the endpoints having the direction bit equal 0
    if a & da: a, b = b, a
    if c & dc: c, d = d, c
    x = a ^ c
    return bin(x).count("1") == 1 and x != da
units_ok = {num[(0, 1)], num[(0, 2)], num[(1, 5)]}
kinds = {"A": 0, "B": 0, "C": 0, "D": 0}
for line in open(sys.argv[1]):
    if line.startswith(("p", "c")): continue
    lits = list(map(int, line.split()))[:-1]
    if len(lits) == 1 and lits[0] in units_ok: kinds["D"] += 1; continue
    if len(lits) == 3 and all(l < 0 for l in lits) and len({-l for l in lits}) == 3 and common_vertex([-l for l in lits]):
        kinds["A"] += 1; continue
    if len(lits) == n - 1 and all(l > 0 for l in lits) and len(set(lits)) == n - 1 and common_vertex(lits):
        kinds["B"] += 1; continue
    if len(lits) == 2 and all(l < 0 for l in lits) and opposite(-lits[0], -lits[1]):
        kinds["C"] += 1; continue
    print("INVALID CLAUSE:", lits); sys.exit(1)
print("all clauses valid:", kinds)
