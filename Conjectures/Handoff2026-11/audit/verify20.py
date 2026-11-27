"""Solver-free check of the claimed balanced independent 20-set in Q_6."""
from itertools import combinations
from collections import Counter

EVEN = "000101 001100 010001 010100 010111 011000 011101 011110 110101 111100".split()
ODD  = "000010 001011 100000 100011 100110 101001 101010 101111 110010 111011".split()

def w(s): return s.count("1")
def d(a, b): return sum(x != y for x, y in zip(a, b))

S = EVEN + ODD
assert len(set(S)) == 20, "duplicates"
assert all(len(s) == 6 and set(s) <= {"0", "1"} for s in S)
assert all(w(s) % 2 == 0 for s in EVEN) and all(w(s) % 2 == 1 for s in ODD)
adj = [(a, b) for a, b in combinations(S, 2) if d(a, b) == 1]
print("vertices:", len(S), "| even:", len(EVEN), "| odd:", len(ODD), "| adjacent pairs:", len(adj))
print("distance distribution, even-even:", sorted(Counter(d(a, b) for a, b in combinations(EVEN, 2)).items()))
print("distance distribution, odd-odd:  ", sorted(Counter(d(a, b) for a, b in combinations(ODD, 2)).items()))
print("distance distribution, even-odd: ", sorted(Counter(d(a, b) for a in EVEN for b in ODD).items()))
