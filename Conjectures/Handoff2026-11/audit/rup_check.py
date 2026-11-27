"""Minimal forward DRUP checker (independent of any SAT solver).

Soundness: every added lemma L is checked to be RUP w.r.t. the current clause database D:
unit propagation on D plus the negation of L must reach a conflict, which implies D |= L.
By induction every lemma is a logical consequence of the input CNF F. Deletion lines are
IGNORED (keeping extra clauses never makes a non-implied lemma pass, so this is still sound,
merely slower). The run succeeds only if the empty clause is derived, or unit propagation
on D alone already conflicts; this proves F unsatisfiable.

usage: python3 rup_check.py formula.cnf proof.drup
"""
import sys

def read_cnf(path):
    cls = []
    for line in open(path):
        if line.startswith(("c", "p")) or not line.strip(): continue
        lits = list(map(int, line.split()))
        assert lits[-1] == 0, "each clause line must end with 0"
        cls.append(lits[:-1])
    return cls

class DB:
    def __init__(self):
        self.clauses = []
        self.watch = {}          # literal -> list of clause indices watching it
        self.units = []          # unit clauses (literals)
        self.empty = False
    def add(self, c):
        c = list(dict.fromkeys(c))           # dedupe literals
        if any(-l in c for l in c): return    # tautology: harmless, skip
        if not c: self.empty = True; return
        if len(c) == 1: self.units.append(c[0]); return
        k = len(self.clauses); self.clauses.append(c)
        self.watch.setdefault(c[0], []).append(k); self.watch.setdefault(c[1], []).append(k)
    def propagate(self, assumptions):
        """Return True iff unit propagation from units + assumptions reaches a conflict."""
        val = {}
        queue = []
        def assign(l):
            v = val.get(abs(l))
            if v is None:
                val[abs(l)] = l > 0; queue.append(l); return True
            return v == (l > 0)
        for l in self.units + assumptions:
            if not assign(l): return True
        def value(l):
            v = val.get(abs(l)); return None if v is None else (v == (l > 0))
        qi = 0
        while qi < len(queue):
            l = queue[qi]; qi += 1
            falsified = -l
            ws = self.watch.get(falsified, [])
            i = 0
            while i < len(ws):
                k = ws[i]; c = self.clauses[k]
                if c[0] == falsified: c[0], c[1] = c[1], c[0]   # make c[1] the falsified watch
                if value(c[0]) is True: i += 1; continue
                # look for a replacement watch
                moved = False
                for j in range(2, len(c)):
                    if value(c[j]) is not False:
                        c[1], c[j] = c[j], c[1]
                        self.watch.setdefault(c[1], []).append(k)
                        ws[i] = ws[-1]; ws.pop(); moved = True; break
                if moved: continue
                if value(c[0]) is False: return True              # conflict
                if not assign(c[0]): return True                   # unit c[0]
                i += 1
        return False

def main(cnf, proof):
    db = DB()
    for c in read_cnf(cnf): db.add(c)
    print("input clauses:", len(db.clauses) + len(db.units))
    if db.empty or db.propagate([]): print("VERIFIED: input refuted by unit propagation alone"); return 0
    n_add = n_del = 0
    for line in open(proof):
        t = line.split()
        if not t: continue
        if t[0] == "d": n_del += 1; continue
        lits = list(map(int, t)); assert lits[-1] == 0; lits = lits[:-1]
        if not db.propagate([-l for l in lits]):
            print(f"FAILED: lemma #{n_add + 1} is not RUP: {lits}"); return 1
        n_add += 1
        db.add(lits)
        if not lits or db.propagate([]):
            print(f"VERIFIED: refutation complete after {n_add} lemmas ({n_del} deletions ignored)"); return 0
    print(f"NOT VERIFIED: proof ended after {n_add} lemmas without deriving a conflict"); return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
