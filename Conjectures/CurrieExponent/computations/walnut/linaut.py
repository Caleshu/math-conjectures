"""Build a Walnut automaton over msd_gam (Dumont-Thomas numeration of gamma: 0->01,1->2,2->02)
accepting digit tuples (x_1..x_r) (msd first, equal length) with  sum_j c_j * sum_i x_j[i] * W_j(len-1-i) = 0,
where each weight sequence W_j satisfies W(t+3) = 2W(t+2) - W(t+1) + W(t) for t >= 0.
State: (dfa states of each tape, f0,f1,f2) where f(t) = remaining-weight function of the prefix."""
import sys, itertools
from collections import deque
# DT language automaton (msd-first): state = current letter
LANG = {0: {0: 0, 1: 1}, 1: {0: 2}, 2: {0: 0, 1: 2}}
def rec(f0, f1, f2): return 2*f2 - f1 + f0
def build(weights, B):
    # weights: list of (W0,W1,W2) integer triples, already multiplied by c_j
    r = len(weights)
    start = ((0,)*r, (0, 0, 0))
    idx = {start: 0}; order = [start]; trans = {}
    q = deque([start])
    while q:
        s = q.popleft(); ls, f = s
        for digs in itertools.product((0, 1), repeat=r):
            if any(d not in LANG[l] for d, l in zip(digs, ls)): continue
            nl = tuple(LANG[l][d] for d, l in zip(digs, ls))
            f3 = rec(*f)
            nf = (f[1] + sum(d*w[0] for d, w in zip(digs, weights)),
                  f[2] + sum(d*w[1] for d, w in zip(digs, weights)),
                  f3   + sum(d*w[2] for d, w in zip(digs, weights)))
            if max(abs(x) for x in nf) > B: continue
            t = (nl, nf)
            if t not in idx: idx[t] = len(order); order.append(t); q.append(t)
            trans.setdefault(s, []).append((digs, t))
    acc = {s for s in order if s[1][0] == 0}
    # co-accessible
    rev = {}
    for s, lst in trans.items():
        for d, t in lst: rev.setdefault(t, []).append(s)
    co = set(acc); dq = deque(acc)
    while dq:
        t = dq.popleft()
        for s in rev.get(t, []):
            if s not in co: co.add(s); dq.append(s)
    keep = [s for s in order if s in co]
    return keep, trans, acc
def minimize(keep, trans, acc, r):
    alph = [d for d in itertools.product((0, 1), repeat=r)]
    K = set(keep)
    part = {s: (s in acc) for s in keep}
    while True:
        sig = {s: (part[s],) + tuple(part.get(dict(trans.get(s, [])).get(a), None) if dict(trans.get(s, [])).get(a) in K else None for a in alph) for s in keep}
        ids = {}; newp = {s: ids.setdefault(sig[s], len(ids)) for s in keep}
        if len(set(newp.values())) == len(set(part.values())): return newp
        part = newp
def write(fn, weights, B, header):
    keep, trans, acc = build(weights, B)
    r = len(weights)
    part = minimize(keep, trans, acc, r)
    K = set(keep)
    start = keep[0]
    # renumber classes so start class = 0
    cls = {}; cls[part[start]] = 0
    for s in keep: cls.setdefault(part[s], len(cls))
    rep = {}
    for s in keep: rep.setdefault(cls[part[s]], s)
    with open(fn, "w") as f:
        f.write(header + "\n" + " ".join(["{0,1}"]*r) + "\n\n")
        for c in range(len(rep)):
            s = rep[c]
            f.write(f"{c} {1 if s in acc else 0}\n")
            for d, t in trans.get(s, []):
                if t in K: f.write(" ".join(map(str, d)) + f" -> {cls[part[t]]}\n")
            f.write("\n")
    return len(keep), len(rep)
if __name__ == "__main__":
    U = (1, 2, 3)
    for B in (20, 40, 80):
        n, m = write(f"add_B{B}.txt", [U, U, tuple(-u for u in U)], B, "# msd_gam addition")
        print("B", B, "co-accessible states", n, "minimal", m)
