# MathResearchLab experiment 7f0e1d47-0b96-4ad1-a4b3-77c86a69f3a0
# Eight-vertex neighborhoods that obstruct a one-vertex coloring extension
# sha256(code) = 5fdc58cf9933965ca1e3f9be3bd8015eede56611d382537d503d8dd9c22c648e
# parameters: {"order": 8, "seconds": 95}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

import json, os
import time
from collections import defaultdict, deque
from itertools import combinations

import networkx as nx

params = json.load(open(os.environ['MRL_PARAMS']))
if params['order'] != 8:
    raise ValueError('This experiment classifies order eight.')
deadline = time.monotonic() + min(float(params['seconds']), 100.0)

def check_time():
    if time.monotonic() >= deadline:
        raise TimeoutError

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def next_order(parents, k):
    # Delete a minimum-degree vertex from any target. Its neighbors form an
    # independent set in the parent, so the reverse operation below reaches it.
    buckets = defaultdict(list)
    for parent in parents:
        check_time()
        degrees = [parent.degree(u) for u in range(k)]
        edge_masks = [(1 << u) | (1 << w) for u, w in parent.edges()]
        for subset in range(1 << k):
            degree = subset.bit_count()
            if any(degrees[u] + ((subset >> u) & 1) < degree for u in range(k)):
                continue
            if any(subset & edge == edge for edge in edge_masks):
                continue
            candidate = parent.copy()
            candidate.add_node(k)
            candidate.add_edges_from((u, k) for u in range(k) if subset & (1 << u))
            # The invariant only selects a bucket. Every merger requires an
            # exact isomorphism test, including for disconnected graphs.
            key = tuple(sorted((candidate.degree(u), tuple(sorted(candidate.degree(w) for w in candidate[u]))) for u in candidate))
            bucket = buckets[key]
            if not any(nx.is_isomorphic(candidate, old) for old in bucket):
                bucket.append(candidate)
    return [g for bucket in buckets.values() for g in bucket]

def edge_list(g):
    return sorted((min(u, w), max(u, w)) for u, w in g.edges())

def extension_count(n, red, blue):
    # Independent witness check. S is the set of red incident edges at v.
    count = 0
    for s in range(1 << n):
        if any((s >> u) & (s >> w) & 1 for u, w in red):
            continue
        if any(((~s) >> u) & ((~s) >> w) & 1 for u, w in blue):
            continue
        count += 1
    return count

def find_bad_coloring(g):
    n = len(g)
    edges = edge_list(g)
    if not edges:
        return None
    edge_masks = [(1 << u) | (1 << w) for u, w in edges]
    # If a cut misses at most one edge, assign opposite incident colors on
    # its two sides. Flip both sides if necessary to protect the missed edge.
    for s in range(1 << (n - 1)):
        if sum((s & e) in (0, e) for e in edge_masks) <= 1:
            return None
    # Bit s of 'alive' records whether incident assignment s still works.
    assignment_count = 1 << n
    universe = (1 << assignment_count) - 1
    allowed = []
    for e in edge_masks:
        red_ok = sum(1 << s for s in range(assignment_count) if (s & e) != e)
        blue_ok = sum(1 << s for s in range(assignment_count) if (s & e) != 0)
        allowed.append((red_ok, blue_ok))
    # A surviving assignment crossing every remaining edge works for every
    # completion of the current coloring, so that branch can be discarded.
    cross_suffix = [universe] * (len(edges) + 1)
    for i in reversed(range(len(edges))):
        cross_suffix[i] = cross_suffix[i + 1] & allowed[i][0] & allowed[i][1]
    def search(i, alive, blue_indices):
        if not alive:
            return blue_indices  # Color all as-yet unassigned edges red.
        if alive & cross_suffix[i]:
            return None
        answer = search(i + 1, alive & allowed[i][0], blue_indices)
        if answer is not None:
            return answer
        return search(i + 1, alive & allowed[i][1], blue_indices | (1 << i))
    # Global color reversal lets us fix the first edge red.
    bits = search(1, allowed[0][0], 0)
    if bits is None:
        return None
    red = [edge for i, edge in enumerate(edges) if not (bits >> i) & 1]
    blue = [edge for i, edge in enumerate(edges) if (bits >> i) & 1]
    return red, blue

def certificate(g, red, blue):
    n = len(g)
    require(set(red).isdisjoint(blue) and set(red) | set(blue) == set(edge_list(g)), 'Invalid edge partition')
    require(all(not (set(g[u]) & set(g[w])) for u, w in g.edges()), 'Neighborhood contains a triangle')
    require(extension_count(n, red, blue) == 0, 'Witness admits an extension')
    # Literal +(u+1) means vu is red. Literal -(u+1) means vu is blue.
    implications = defaultdict(list)
    for sign, edges in [(1, red), (-1, blue)]:
        for u, w in edges:
            a, b = sign * (u + 1), sign * (w + 1)
            implications[a].append(-b)
            implications[b].append(-a)
    def path(start, end):
        queue = deque([start])
        parent = {start: None}
        while queue:
            a = queue.popleft()
            if a == end:
                route = []
                while a is not None:
                    route.append(a)
                    a = parent[a]
                return route[::-1]
            for b in implications[a]:
                if b not in parent:
                    parent[b] = a
                    queue.append(b)
        return None
    for literal in range(1, n + 1):
        forward = path(literal, -literal)
        backward = path(-literal, literal)
        if forward and backward:
            return {'order': n, 'red_edges': red, 'blue_edges': blue, 'extension_count': 0, 'forced_red_to_blue': forward, 'forced_blue_to_red': backward}
    raise AssertionError('Missing implication certificate')

def sanity_checks():
    # Two five-cycles through 0 and 1. Alternating along the first rules out
    # red at vertex 0, and alternating along the second rules out blue there.
    red = [(0, 2), (1, 3), (0, 4), (1, 5), (6, 7)]
    blue = [(1, 2), (3, 4), (0, 5), (1, 6), (0, 7)]
    g = nx.Graph(red + blue)
    certificate(g, red, blue)
    found = find_bad_coloring(g)
    require(found is not None, 'Search missed the explicit positive control')
    certificate(g, *found)
    cycle = nx.cycle_graph(5)
    edges = edge_list(cycle)
    for bits in range(1 << len(edges)):
        r = [e for i, e in enumerate(edges) if bits & (1 << i)]
        b = [e for i, e in enumerate(edges) if not bits & (1 << i)]
        require(extension_count(5, r, b) > 0, 'Five-cycle control failed')
    require(find_bad_coloring(cycle) is None, 'False positive on five-cycle')
    return {'explicit_obstruction_recognized': True, 'all_32_five_cycle_colorings_extend': True}

result = {'complete': False, 'sanity': sanity_checks(), 'orders': {}, 'witnesses': [], 'literal_key': 'Vertices are numbered from 0. Literal +(u+1) means the incident edge to vertex u is red, and -(u+1) means it is blue. Each consecutive pair is an implication from one listed neighborhood edge.'}
try:
    classes = [nx.Graph()]
    for n in range(params['order'] + 1):
        stage = f'generating order {n}'
        if n:
            classes = next_order(classes, n - 1)
        stage = f'classifying order {n}'
        row = {'neighborhood_types': len(classes), 'types_checked': 0, 'obstructing_types': 0}
        result['orders'][str(n)] = row
        for g in classes:
            check_time()
            found = find_bad_coloring(g)
            if found is not None:
                result['witnesses'].append(certificate(g, *found))
                row['obstructing_types'] += 1
            row['types_checked'] += 1
    # Independent labeled enumeration checks the isomorphism generation at
    # order five. Orbit sizes must sum to the labeled triangle-free count.
    stage = 'checking the enumeration control'
    control = [nx.Graph()]
    for k in range(5):
        control = next_order(control, k)
    labeled_from_orbits = sum(120 // sum(1 for _ in nx.isomorphism.GraphMatcher(g, g).isomorphisms_iter()) for g in control)
    pairs = list(combinations(range(5), 2))
    triple_masks = [sum(1 << pairs.index(e) for e in combinations(t, 2)) for t in combinations(range(5), 3)]
    labeled_direct = sum(all((s & t) != t for t in triple_masks) for s in range(1 << len(pairs)))
    require(labeled_direct == labeled_from_orbits, 'Order-five orbit count mismatch')
    result['sanity']['order_five_labeled_counts'] = [labeled_direct, labeled_from_orbits]
    number = result['orders']['8']['obstructing_types']
    smaller = sum(result['orders'][str(k)]['obstructing_types'] for k in range(8))
    result['complete'] = True
    result['summary'] = f'Exhaustive up to isomorphism. Found {number} obstructing types at order eight and {smaller} in total at smaller orders. Each has a verified edge coloring and two implication paths.'
except TimeoutError:
    result['summary'] = f'Partial enumeration. Stopped while {stage}. Only the checked types and listed witnesses have been classified.'
with open('result.json', 'w') as output:
    json.dump(result, output, indent=2)
