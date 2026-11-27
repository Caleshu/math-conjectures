# MathResearchLab experiment fd5f7d08-9f16-4af5-b3bf-02712691c6e0
# Square-free Hamiltonian cycles in Q_n (enumeration + CP-SAT)
# sha256(code) = d6b8073ba095b4e9d1e9c0f7623e80c09dd5ad9a1e050ccfc0d8c35449cc58b5
# parameters: {"enumerate_n": [2, 3, 4], "cpsat_n": [2, 3, 4, 5, 6, 7], "sanity_n": [2, 3, 4, 5, 6, 7], "min_squares_n": [2, 3, 4], "time_limit_s": 600, "workers": 8, "seed": 0}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 900, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 7205, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/MathResearchLab/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

"""Inscribed squares in Hamiltonian cycles of the hypercube Q_n.

Conjecture (Sagols & Morales-Luna, arXiv:1009.3304, Conj. 5.1): every Hamiltonian cycle of Q_n
(n >= 2) contains two opposite edges of some 4-cycle of Q_n ("an inscribed square").

This script searches for a counterexample, i.e. a *square-free* Hamiltonian cycle.

Methods
- "enumerate": exhaustive DFS over all Hamiltonian cycles through vertex 0 (each undirected cycle
  counted once). Feasible for n <= 4. Reports the number of cycles, how many are square-free, and
  the minimum number of inscribed squares over all cycles.
- "cpsat": exact constraint model in OR-Tools CP-SAT. Boolean x_e per edge; AddCircuit on the
  directed arcs forces a single Hamiltonian cycle; for every 4-cycle (a,b,c,d) we forbid
  x_ab & x_cd and x_bc & x_da. FEASIBLE = counterexample (independently re-verified below);
  INFEASIBLE = no square-free Hamiltonian cycle exists for that n, *conditional on solver
  correctness*. This is a finite computational result, not a proof for general n.

Validation built in: "sanity_n" re-solves without the square constraints (must be FEASIBLE with a
valid Hamiltonian cycle), and "min_squares_n" minimises the number of inscribed squares with CP-SAT;
for n <= 4 the optimum is cross-checked against exhaustive enumeration.

Parameters (params.json): {"enumerate_n": [2,3,4], "cpsat_n": [2,3,4,5,6], "sanity_n": [...],
                           "min_squares_n": [2,3,4,5], "time_limit_s": 600, "workers": 8, "seed": 0}
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time


# ------------------------------------------------------------------------------------------
# Hypercube structure
# ------------------------------------------------------------------------------------------
def edges(n: int) -> list[tuple[int, int]]:
    return [(v, v ^ (1 << i)) for v in range(1 << n) for i in range(n) if v < v ^ (1 << i)]


def squares(n: int) -> list[tuple[int, int, int, int]]:
    """All 4-cycles (a, b, c, d) in cyclic order: a, a^i, a^i^j, a^j with a having bits i,j = 0."""
    out = []
    for i, j in itertools.combinations(range(n), 2):
        for a in range(1 << n):
            if a & (1 << i) or a & (1 << j):
                continue
            b, c, d = a ^ (1 << i), a ^ (1 << i) ^ (1 << j), a ^ (1 << j)
            out.append((a, b, c, d))
    return out


def ekey(u: int, v: int) -> tuple[int, int]:
    return (u, v) if u < v else (v, u)


def inscribed_squares(cycle: list[int], n: int, sq: list | None = None) -> list[tuple]:
    """Squares whose opposite edge pair (either pair) both lie on the cycle."""
    on = {ekey(cycle[k], cycle[(k + 1) % len(cycle)]) for k in range(len(cycle))}
    found = []
    for a, b, c, d in sq or squares(n):
        if (ekey(a, b) in on and ekey(c, d) in on) or (ekey(b, c) in on and ekey(d, a) in on):
            found.append((a, b, c, d))
    return found


def is_hamiltonian_cycle(cycle: list[int], n: int) -> bool:
    N = 1 << n
    if len(cycle) != N or len(set(cycle)) != N or set(cycle) != set(range(N)):
        return False
    return all(bin(cycle[k] ^ cycle[(k + 1) % N]).count("1") == 1 for k in range(N))


# ------------------------------------------------------------------------------------------
# Exhaustive enumeration (small n)
# ------------------------------------------------------------------------------------------
def enumerate_cycles(n: int):
    N = 1 << n
    if n == 1:
        return
    path = [0]
    used = [False] * N
    used[0] = True

    def dfs():
        v = path[-1]
        if len(path) == N:
            if bin(v).count("1") == 1:  # adjacent to 0
                # count each undirected cycle once: require second vertex < last vertex
                if path[1] < path[-1]:
                    yield list(path)
            return
        for i in range(n):
            w = v ^ (1 << i)
            if not used[w]:
                used[w] = True
                path.append(w)
                yield from dfs()
                path.pop()
                used[w] = False

    yield from dfs()


def run_enumeration(n: int) -> dict:
    t0 = time.time()
    sq = squares(n)
    total = 0
    square_free = []
    min_sq = None
    hist: dict[int, int] = {}
    for cyc in enumerate_cycles(n):
        total += 1
        k = len(inscribed_squares(cyc, n, sq))
        hist[k] = hist.get(k, 0) + 1
        min_sq = k if min_sq is None else min(min_sq, k)
        if k == 0 and len(square_free) < 5:
            square_free.append(cyc)
    return {"n": n, "method": "exhaustive_enumeration", "hamiltonian_cycles": total,
            "square_free_cycles_found": len(square_free) if square_free else 0,
            "square_free_examples": square_free, "min_inscribed_squares": min_sq,
            "inscribed_square_histogram": {str(k): v for k, v in sorted(hist.items())},
            "seconds": round(time.time() - t0, 3)}


# ------------------------------------------------------------------------------------------
# CP-SAT search for a square-free Hamiltonian cycle
# ------------------------------------------------------------------------------------------
def _base_model(n: int):
    """Hamiltonian-cycle model shared by all CP-SAT modes."""
    from ortools.sat.python import cp_model

    N = 1 << n
    E = edges(n)
    m = cp_model.CpModel()
    x = {e: m.NewBoolVar(f"x_{e[0]}_{e[1]}") for e in E}
    arcs, arc_lit = [], {}
    for u, v in E:
        a, b = m.NewBoolVar(f"a_{u}_{v}"), m.NewBoolVar(f"a_{v}_{u}")
        arc_lit[(u, v)], arc_lit[(v, u)] = a, b
        arcs += [(u, v, a), (v, u, b)]
        m.Add(a + b == x[(u, v)])
    m.AddCircuit(arcs)
    for v in range(N):
        m.Add(sum(x[ekey(v, v ^ (1 << i))] for i in range(n)) == 2)
    m.Add(x[(0, 1)] == 1)
    return m, x, arc_lit


def _extract_cycle(solver, arc_lit, N):
    succ = {u: v for (u, v), lit in arc_lit.items() if solver.Value(lit)}
    cyc = [0]
    while len(cyc) < N:
        cyc.append(succ[cyc[-1]])
    return cyc


def _solver(time_limit_s, workers, seed):
    from ortools.sat.python import cp_model

    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = float(time_limit_s)
    s.parameters.num_search_workers = int(workers)
    s.parameters.random_seed = int(seed)
    return s


def model_sanity(n: int, time_limit_s: float, workers: int, seed: int) -> dict:
    """Without the square-free constraints the model must be FEASIBLE and yield a valid
    Hamiltonian cycle; otherwise an INFEASIBLE verdict below would be meaningless."""
    from ortools.sat.python import cp_model

    m, x, arc_lit = _base_model(n)
    s = _solver(time_limit_s, workers, seed)
    st = s.Solve(m)
    ok = st in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    cyc = _extract_cycle(s, arc_lit, 1 << n) if ok else None
    return {"n": n, "status": s.StatusName(st), "valid_hamiltonian_cycle": bool(cyc and is_hamiltonian_cycle(cyc, n)),
            "inscribed_squares_in_witness": len(inscribed_squares(cyc, n)) if cyc else None}


def cpsat_min_squares(n: int, time_limit_s: float, workers: int, seed: int) -> dict:
    """Minimise the number of inscribed squares. For n <= 4 this must match enumeration."""
    from ortools.sat.python import cp_model

    t0 = time.time()
    m, x, arc_lit = _base_model(n)
    sq = squares(n)
    ys = []
    for a, b, c, d in sq:
        y = m.NewBoolVar("")
        # y = 1 iff (ab & cd) or (bc & da)
        p1, p2 = m.NewBoolVar(""), m.NewBoolVar("")
        m.AddMultiplicationEquality(p1, [x[ekey(a, b)], x[ekey(c, d)]])
        m.AddMultiplicationEquality(p2, [x[ekey(b, c)], x[ekey(d, a)]])
        m.AddMaxEquality(y, [p1, p2])
        ys.append(y)
    m.Minimize(sum(ys))
    s = _solver(time_limit_s, workers, seed)
    st = s.Solve(m)
    out = {"n": n, "status": s.StatusName(st), "seconds": round(time.time() - t0, 3)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        cyc = _extract_cycle(s, arc_lit, 1 << n)
        out.update({"best_value": int(s.ObjectiveValue()), "lower_bound": int(s.BestObjectiveBound()),
                    "proved_optimal": st == cp_model.OPTIMAL, "witness_cycle": cyc,
                    "witness_independently_counted": len(inscribed_squares(cyc, n, sq)),
                    "witness_is_hamiltonian": is_hamiltonian_cycle(cyc, n)})
    return out


def run_cpsat(n: int, time_limit_s: float, workers: int, seed: int) -> dict:
    from ortools.sat.python import cp_model

    t0 = time.time()
    N = 1 << n
    E = edges(n)
    m = cp_model.CpModel()
    x = {e: m.NewBoolVar(f"x_{e[0]}_{e[1]}") for e in E}
    arcs = []
    arc_lit = {}
    for u, v in E:
        a = m.NewBoolVar(f"a_{u}_{v}")
        b = m.NewBoolVar(f"a_{v}_{u}")
        arc_lit[(u, v)], arc_lit[(v, u)] = a, b
        arcs.append((u, v, a))
        arcs.append((v, u, b))
        m.Add(a + b == x[(u, v)])
    m.AddCircuit(arcs)  # single directed Hamiltonian circuit over all N nodes (no self loops given)
    for v in range(N):  # redundant degree constraint, helps propagation
        m.Add(sum(x[ekey(v, v ^ (1 << i))] for i in range(n)) == 2)
    sq = squares(n)
    for a, b, c, d in sq:
        m.AddBoolOr([x[ekey(a, b)].Not(), x[ekey(c, d)].Not()])
        m.AddBoolOr([x[ekey(b, c)].Not(), x[ekey(d, a)].Not()])
    # Symmetry breaking (valid: Aut(Q_n) is transitive on edges/directions): the cycle uses edge {0,1}.
    if n >= 2:
        m.Add(x[(0, 1)] == 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = int(workers)
    solver.parameters.random_seed = int(seed)
    status = solver.Solve(m)
    name = solver.StatusName(status)
    out = {"n": n, "method": "cp_sat", "vertices": N, "edges": len(E), "four_cycles": len(sq),
           "solver_status": name, "wall_seconds": round(time.time() - t0, 3),
           "solver_wall_time": round(solver.WallTime(), 3), "branches": solver.NumBranches(),
           "conflicts": solver.NumConflicts(),
           "solver_settings": {"max_time_in_seconds": time_limit_s, "num_search_workers": workers,
                               "random_seed": seed, "symmetry_breaking": "edge {0,1} fixed in cycle"}}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {u: v for (u, v), lit in arc_lit.items() if solver.Value(lit)}
        cyc = [0]
        while len(cyc) < N:
            cyc.append(succ[cyc[-1]])
        ok = is_hamiltonian_cycle(cyc, n)
        ins = inscribed_squares(cyc, n, sq)
        out.update({"counterexample_candidate": cyc, "independent_check_hamiltonian": ok,
                    "independent_check_inscribed_squares": len(ins),
                    "conclusion": ("COUNTEREXAMPLE (verified by independent checker)" if ok and not ins
                                   else "solver returned a solution that FAILED independent verification — investigate")})
    elif status == cp_model.INFEASIBLE:
        out["conclusion"] = (f"No square-free Hamiltonian cycle of Q_{n} exists (CP-SAT proved infeasibility). "
                             "Finite computational result; relies on solver correctness.")
    else:
        out["conclusion"] = f"Inconclusive: solver stopped with status {name} (time limit {time_limit_s}s)."
    return out


def main() -> None:
    params = json.load(open(os.environ.get("MRL_PARAMS", "params.json")))
    enum_n = params.get("enumerate_n", [2, 3, 4])
    cp_n = params.get("cpsat_n", [2, 3, 4, 5])
    tl = params.get("time_limit_s", 300)
    workers = params.get("workers", 8)
    seed = params.get("seed", 0)
    results = {"enumeration": [], "cpsat": [], "cross_checks": []}
    for n in enum_n:
        if n > 4:
            print(f"skip enumeration for n={n}: infeasible size", flush=True)
            continue
        r = run_enumeration(n)
        print(f"[enumerate] n={n}: {r['hamiltonian_cycles']} cycles, square-free={r['square_free_cycles_found']}, "
              f"min squares={r['min_inscribed_squares']} ({r['seconds']}s)", flush=True)
        results["enumeration"].append(r)
    for n in cp_n:
        r = run_cpsat(n, tl, workers, seed)
        print(f"[cp-sat] n={n}: {r['solver_status']} in {r['wall_seconds']}s — {r['conclusion']}", flush=True)
        results["cpsat"].append(r)
    for e in results["enumeration"]:
        c = next((c for c in results["cpsat"] if c["n"] == e["n"]), None)
        if c:
            agree = (e["square_free_cycles_found"] == 0) == (c["solver_status"] == "INFEASIBLE")
            results["cross_checks"].append({"n": e["n"], "enumeration_vs_cpsat_agree": agree})
    for n in params.get("sanity_n", cp_n):
        r = model_sanity(n, tl, workers, seed)
        print(f"[sanity] n={n}: model without square constraints -> {r['status']}, "
              f"valid witness={r['valid_hamiltonian_cycle']}", flush=True)
        results.setdefault("model_sanity", []).append(r)
    for n in params.get("min_squares_n", []):
        r = cpsat_min_squares(n, tl, workers, seed)
        print(f"[min-squares] n={n}: {r['status']} best={r.get('best_value')} bound={r.get('lower_bound')} "
              f"witness recount={r.get('witness_independently_counted')} ({r['seconds']}s)", flush=True)
        results.setdefault("min_squares", []).append(r)
        e = next((e for e in results["enumeration"] if e["n"] == n), None)
        if e and r.get("proved_optimal"):
            results["cross_checks"].append({"n": n, "min_squares_enumeration": e["min_inscribed_squares"],
                                            "min_squares_cpsat": r["best_value"],
                                            "agree": e["min_inscribed_squares"] == r["best_value"]})
    results["summary"] = {
        "counterexample_found": any("counterexample_candidate" in c and c.get("independent_check_inscribed_squares") == 0
                                    and c.get("independent_check_hamiltonian") for c in results["cpsat"]) or
        any(e["square_free_cycles_found"] for e in results["enumeration"]),
        "n_settled_no_counterexample": sorted({e["n"] for e in results["enumeration"] if e["square_free_cycles_found"] == 0} |
                                              {c["n"] for c in results["cpsat"] if c["solver_status"] == "INFEASIBLE"}),
        "n_inconclusive": [c["n"] for c in results["cpsat"] if c["solver_status"] not in ("INFEASIBLE", "OPTIMAL", "FEASIBLE")],
        "model_sanity_passed": all(r["valid_hamiltonian_cycle"] for r in results.get("model_sanity", [])),
        "cross_checks_passed": all(c.get("agree", c.get("enumeration_vs_cpsat_agree")) for c in results["cross_checks"]),
        "nature": "finite computational verification for specific n; not a proof of the general conjecture",
    }
    json.dump(results, open("result.json", "w"), indent=2)
    print(json.dumps(results["summary"]), flush=True)


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main()
