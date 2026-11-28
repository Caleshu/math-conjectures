# MathResearchLab experiment 27edf7eb-d86d-45ea-b97f-6f4d057b9a5e
# Audit terminal comparisons and search their complement up to isomorphism
# sha256(code) = f633a86ae0f8cf8eb06ba42a77933de88c4b0eefd27ae9b3980554f11dac9ac3
# parameters: {"trace_file": "E-52ac69.terminals.jsonl", "phase": "both"}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os, time
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import networkx as nx
import sympy as sp

params = json.load(open(os.environ['MRL_PARAMS']))
start = time.monotonic()
deadline = start + 75
edges = list(combinations(range(11), 2))
bits = {e: 1 << i for i, e in enumerate(edges)}
full = (1 << len(edges)) - 1
target = Fraction(11950)
progress = {'comparisons_completed': 0, 'coverage_cubes_completed': 0, 'nodes': 0}

class Partial(Exception):
    pass

class Finding(Exception):
    def __init__(self, data):
        self.data = data

def tick():
    if time.monotonic() >= deadline:
        raise Partial()

def edge_mask(es):
    return sum(bits[tuple(sorted(e))] for e in es)

def graph(mask):
    g = nx.Graph()
    g.add_nodes_from(range(11))
    g.add_edges_from(e for e in edges if mask & bits[e])
    return g

def electrical(g, score=False):
    n = len(g)
    deg = [g.degree(i) for i in range(n)]
    lap = sp.diag(*deg)
    for i, j in g.edges():
        lap[i, j] = lap[j, i] = -1
    z = sp.zeros(n)
    z[:n-1, :n-1] = lap[:n-1, :n-1].inv()
    pairs = list(combinations(range(n), 2))
    if not score:
        return Fraction(sum(z[i,i] + z[j,j] - 2*z[i,j] for i,j in pairs))
    s = z * sp.Matrix(deg)
    volume = sum(deg)
    h = [[s[i]-s[j]+volume*(z[j,j]-z[i,j]) for j in range(n)] for i in range(n)]
    for j in range(n):
        if h[j][j] != 0:
            raise ArithmeticError('diagonal hitting time')
        for i in range(n):
            if i != j and deg[i]*h[i][j]-sum(h[x][j] for x in g[i]) != deg[i]:
                raise ArithmeticError('failed hitting-time equation')
    return Fraction(3*sum(max(h[i][j], h[j][i]) for i,j in pairs))

def contains(a, b, d, p):
    # Map required edges of a to d, and forbidden edges outside b to nonedges of p.
    if a.bit_count() > d.bit_count() or b.bit_count() < p.bit_count():
        return False
    if not (a & ~d or p & ~b):
        return True
    def neighbors(mask):
        adj = [0]*11
        for i,j in edges:
            if mask & bits[i,j]:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
        return adj
    need, ban, have, absent = map(neighbors, (a, full ^ b, d, full ^ p))
    choices = [[j for j in range(11) if need[i].bit_count() <= have[j].bit_count() and ban[i].bit_count() <= absent[j].bit_count()] for i in range(11)]
    order = sorted(range(11), key=lambda i: (len(choices[i]), -need[i].bit_count()-ban[i].bit_count()))
    assigned = []
    def match(depth, used):
        tick()
        if depth == 11:
            return True
        i = order[depth]
        for j in choices[i]:
            if used & (1 << j):
                continue
            if any(((need[i] >> u) & 1 and not ((have[j] >> v) & 1)) or ((ban[i] >> u) & 1 and not ((absent[j] >> v) & 1)) for u,v in assigned):
                continue
            assigned.append((i,j))
            if match(depth+1, used | (1 << j)):
                return True
            assigned.pop()
        return False
    return match(0, 0)

def records(path):
    with path.open() as stream:
        for line_no, line in enumerate(stream, 1):
            tick()
            r = json.loads(line)
            a, b = int(r['lo']), int(r['hi'])
            lo, hi = r.get('min_m', 14), r.get('max_m', 35)
            kind = r['kind']
            if not (0 <= a <= full and 0 <= b <= full and a & ~b == 0 and type(lo) is int and type(hi) is int and lo <= hi and kind in ('empty','upper','equal')):
                raise ValueError('invalid domain at line '+str(line_no))
            value = None if kind == 'empty' else Fraction(str(r['value']))
            if value is not None and value > target:
                raise ValueError('line '+str(line_no)+' asserts a score larger than the threshold; its assertion alone cannot close this domain')
            yield line_no, a, b, max(14,lo), min(35,hi), kind, value

def witness(reason, g, score, rec=None):
    bridge = next(nx.bridges(g))
    finding = {'status': reason, 'edges': sorted(tuple(sorted(e)) for e in g.edges()), 'bridge': bridge, 'm': g.number_of_edges(), 'diameter': nx.diameter(g), 'three_HT': str(score), 'above_threshold': score > target}
    if rec is not None:
        finding.update(line=rec[0], assertion=rec[5], asserted_value=str(rec[6]) if rec[6] is not None else None)
    raise Finding(finding)

def visit(d, p, m, path, rec):
    tick()
    progress['nodes'] += 1
    if d.bit_count() > m or p.bit_count() < m:
        return
    if d.bit_count() == m:
        p = d
    elif p.bit_count() == m:
        d = p
    lower = graph(d)
    connected = nx.is_connected(lower)
    if connected:
        if nx.diameter(lower) <= 2 or not nx.has_bridges(lower):
            return
    elif not nx.is_connected(graph(p)):
        return
    if rec is None:
        for _,a,b,lo,hi,kind,_ in records(path):
            if kind != 'empty' and lo <= m <= hi and contains(a,b,d,p):
                return
    elif rec[5] == 'upper' and connected and d != p:
        if 6*m*electrical(lower) <= rec[6]:
            return
    if d == p:
        score = electrical(lower, True)
        if rec is None:
            witness('UNCOVERED_JOIN', lower, score)
        if rec[5] == 'empty' or (rec[5] == 'upper' and score > rec[6]) or (rec[5] == 'equal' and score != rec[6]):
            witness('INVALID_TERMINAL_COMPARISON', lower, score, rec)
        return
    optional = p ^ d
    bit = optional & -optional
    visit(d, p ^ bit, m, path, rec)
    visit(d | bit, p, m, path, rec)

def audit():
    # P3 has maximum directed times 3, 4, 3 on its three pairs.
    if electrical(nx.path_graph(3), True) != 30:
        raise ArithmeticError('P3 sanity check')
    p3 = edge_mask([(0,1),(1,2)])
    copy = edge_mask([(5,8),(8,10)])
    disjoint = edge_mask([(5,8),(9,10)])
    if not contains(p3,p3,copy,copy) or contains(p3,p3,disjoint,disjoint):
        raise ArithmeticError('relabelled interval sanity check')
    name = params.get('trace_file')
    if not name:
        return {'status':'TRACE_UNAVAILABLE'}
    path = Path(name).resolve()
    if not path.is_relative_to(Path.cwd().resolve()):
        raise ValueError('trace must be in working directory')
    if not path.is_file():
        return {'status':'TRACE_UNAVAILABLE'}
    phase = params.get('phase','both')
    if phase not in ('comparisons','coverage','both'):
        raise ValueError('unknown phase')
    if phase != 'coverage':
        for rec in records(path):
            line,a,b,lo,hi,_,_ = rec
            for m in range(max(lo,a.bit_count()), min(hi,b.bit_count())+1):
                progress['current'] = {'phase':'comparisons','line':line,'m':m}
                visit(a,b,m,path,rec)
            progress['comparisons_completed'] += 1
    if phase != 'comparisons':
        for index, tree in enumerate(nx.nonisomorphic_trees(11)):
            d = edge_mask(tree.edges())
            for u,v in sorted(tree.edges()):
                cut = tree.copy()
                cut.remove_edge(u,v)
                side = nx.node_connected_component(cut,u)
                p = d | edge_mask((i,j) for i,j in edges if (i in side) == (j in side))
                for m in range(14,min(35,p.bit_count())+1):
                    progress['current'] = {'phase':'coverage','tree':index,'mandatory_mask':d,'bridge':[u,v],'m':m}
                    visit(d,p,m,path,None)
                    progress['coverage_cubes_completed'] += 1
    return {'status': 'CERTIFIED' if phase == 'both' else 'PHASE_COMPLETE', 'phase':phase}

try:
    out = audit()
except Partial:
    out = {'status':'PARTIAL_TIME_LIMIT'}
except Finding as f:
    out = f.data
except (ValueError, KeyError, TypeError, OSError, ArithmeticError) as error:
    out = {'status':'INPUT_OR_CHECKER_ERROR','detail':str(error)}
out['progress'] = progress
out['summary'] = {'CERTIFIED':'All eligible joins are covered and every terminal comparison passed.', 'PHASE_COMPLETE':'The selected phase finished. Certification requires both phases.', 'TRACE_UNAVAILABLE':'The actual terminal records were not supplied. No comparison or coverage verdict is available.', 'PARTIAL_TIME_LIMIT':'Audit incomplete at the reported location.', 'UNCOVERED_JOIN':'No scored terminal contains this join under any relabelling. The separate above_threshold field reports the exact score comparison.', 'INVALID_TERMINAL_COMPARISON':'The stated terminal assertion fails on the displayed graph. The separate above_threshold field reports the exact score comparison.', 'INPUT_OR_CHECKER_ERROR':'The input or an internal check prevented a replay verdict.'}[out['status']]
with open('result.json','w') as stream:
    json.dump(out,stream)
