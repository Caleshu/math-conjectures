# MathResearchLab experiment ee7531e6-d24b-4276-9a44-0de901e2f05e
# Enumerate consecutive 3-full integers through $10^{18}$
# sha256(code) = f837ebffa327d0ec1d2540f4d9ca84175f17b1180a3e3837100ad67ec62ab81e
# parameters: {"limit": 1000000000000000000, "sanity_limit": 5000}
# environment: {"python": "3.13.5", "platform": "macOS-27.0-arm64-arm-64bit-Mach-O", "networkx": "3.7", "sympy": "1.14.0", "ortools": "9.15.6755", "numpy": "2.5.5", "pysat": null, "isolation": "macos-sandbox-exec(no-network,write-confined)+rlimits", "limits": {"wall_timeout_s": 120, "memory_mb": 2048, "memory_enforced": false, "cpu_seconds": 965, "max_file_mb": 200, "max_open_files": 256}, "interpreter": "/Users/andrewcaleshu/Documents/myProjects/math-conjectures/platform/backend/.venv/bin/python", "host": "local", "cwd_isolated": true}

body = r'''import json, os
import heapq
import math
import time

params = json.load(open(os.environ['MRL_PARAMS']))
limit = int(params['limit'])
sanity_limit = min(limit, int(params['sanity_limit']))
deadline = time.monotonic() + 95


def check_time():
    if time.monotonic() >= deadline:
        raise TimeoutError('soft time limit reached')


def coefficient_heap(bound):
    fourth_root = math.isqrt(math.isqrt(bound))
    squarefree = bytearray([1]) * (fourth_root + 1)
    for d in range(2, math.isqrt(fourth_root) + 1):
        step = d * d
        for multiple in range(step, fourth_root + 1, step):
            squarefree[multiple] = 0
    heap = []
    for c in range(1, fourth_root + 1):
        c5 = c ** 5
        if c5 > bound:
            break
        check_time()
        if squarefree[c]:
            max_b = math.isqrt(math.isqrt(bound // c5))
            for b in range(1, max_b + 1):
                if squarefree[b] and math.gcd(b, c) == 1:
                    coefficient = b ** 4 * c5
                    heap.append((coefficient, coefficient, 1))
    heapq.heapify(heap)
    return heap


def scan(heap, bound, prefix_limit, state):
    previous = None
    count = 0
    try:
        while heap:
            if count % 8192 == 0:
                check_time()
            value, coefficient, a = heap[0]
            if previous is None:
                state['first'] = value
            else:
                if value <= previous:
                    raise ArithmeticError('duplicate or out-of-order value')
                if value == previous + 1:
                    state['pairs'].append([previous, value])
            if value <= prefix_limit:
                state['prefix'].append(value)
            previous = value
            count += 1
            next_value = coefficient * (a + 1) ** 3
            if next_value <= bound:
                heapq.heapreplace(heap, (next_value, coefficient, a + 1))
            else:
                heapq.heappop(heap)
    finally:
        state.update(count=count, last=previous, adjacent_comparisons=max(0, count - 1), streams_remaining=len(heap))


def trial_full(value):
    d = 2
    while d * d <= value:
        exponent = 0
        while value % d == 0:
            value //= d
            exponent += 1
        if exponent in (1, 2):
            return False
        d += 1
    return value == 1


state = {'pairs': [], 'prefix': []}
record = {'parameters': params, 'status': 'started', 'findings': state, 'sanity': {}, 'coverage_argument': {'author_support': 'proved_here', 'justification': 'For each prime exponent $e$ in a 3-full integer, choose $r=0,4,5$ according as $e$ is $0,1,2$ modulo $3$. Then $e-r$ is a nonnegative multiple of $3$. Assign primes with $r=4$ to $b$ and primes with $r=5$ to $c$. This gives exactly one representation $a^3 b^4 c^5$ with $b,c$ coprime and squarefree, including $1$ from $a=b=c=1$. Conversely each such product is 3-full. The coefficient loops include exactly the $b^4c^5$ within the bound. Each heap entry is the least unconsumed member of its increasing stream. Replacing or retiring the least entry therefore visits the union in increasing order until the heap is empty. Two integers differing by one must be adjacent in that order.'}}
try:
    if not 1 <= sanity_limit <= limit:
        raise ValueError('invalid bounds')
    control = {'pairs': [], 'prefix': []}
    scan([(1, 1, 1), (7, 7, 1)], 8, 8, control)
    record['sanity']['positive_control'] = control
    if control['prefix'] != [1, 7, 8] or control['pairs'] != [[7, 8]]:
        raise ArithmeticError('adjacency control failed')
    expected_prefix = [v for v in range(1, sanity_limit + 1) if trial_full(v)]
    record['sanity']['trial_division_prefix'] = expected_prefix
    heap = coefficient_heap(limit)
    record['initial_stream_count'] = len(heap)
    scan(heap, limit, sanity_limit, state)
    record['sanity']['prefix_agrees'] = state['prefix'] == expected_prefix
    if not record['sanity']['prefix_agrees'] or state['first'] != 1 or state['streams_remaining'] != 0:
        raise ArithmeticError('enumeration completion check failed')
    record['status'] = 'complete'
    record['smaller_endpoint_range'] = [1, limit - 1]
    record['summary'] = 'Exhausted all streams through %d. Found %d positive 3-full integers and %d consecutive pairs.' % (limit, state['count'], len(state['pairs']))
except TimeoutError as error:
    record.update(status='partial', summary=str(error) + '. Only the emitted prefix has been scanned.')
except Exception as error:
    record.update(status='failed', summary=type(error).__name__ + ': ' + str(error))
record['program'] = 'body = r' + chr(39) * 3 + body + chr(39) * 3 + '\nexec(body)\n'
with open('result.json', 'w') as output:
    json.dump(record, output)
'''
exec(body)
