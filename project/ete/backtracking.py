"""Backtracking solvers for the decision problem "is there a timetable that
uses only slots 0..k-1?".

``naive_backtracking`` is chronological backtracking. Exams are taken in
index order, and each assignment is checked only against the exams already
placed.

``backtracking`` adds the pruning techniques one at a time, so their effect
can be measured separately:

* ``fc``: forward checking. After placing exam v in slot c, remove c from
  the domains of v's unassigned neighbours. Also remove c from any
  unassigned exam that no longer fits in slot c's remaining venues. Fail as
  soon as a domain is empty.
* ``mrv``: choose the unassigned exam with the fewest remaining slots.
* ``degree``: break MRV ties by the number of unassigned neighbours.
* ``mac``: maintain arc consistency. For "not equal" constraints this
  propagates every domain that becomes a single value to its neighbours,
  repeatedly.

The node count is the number of (exam, slot) assignments tried.
"""

from __future__ import annotations

import sys
import time

from .bounds import lower_bound
from .model import SolveResult, VenueState, slots_used

sys.setrecursionlimit(20000)


class SearchLimit(Exception):
    """Raised when a node or time budget is exhausted."""


class Budget:
    def __init__(self, node_limit=None, time_limit=None):
        self.node_limit = node_limit
        self.time_limit = time_limit
        self.start = time.perf_counter()
        self.nodes = 0

    def tick(self):
        self.nodes += 1
        if self.node_limit is not None and self.nodes > self.node_limit:
            raise SearchLimit
        if (self.time_limit is not None and (self.nodes & 255) == 0
                and time.perf_counter() - self.start > self.time_limit):
            raise SearchLimit

    def elapsed(self):
        return time.perf_counter() - self.start


def naive_backtracking(inst, k, node_limit=None, time_limit=None):
    n, adj, allowed, sizes = inst.n, inst.adj, inst.allowed, inst.sizes
    color = [-1] * n
    venues = VenueState(inst, k)
    budget = Budget(node_limit, time_limit)

    def consistent(v, c):
        if c not in allowed[v]:
            return False
        for u in adj[v]:
            if color[u] == c:
                return False
        return venues.can_add(c, sizes[v])

    def rec(v):
        if v == n:
            return True
        for c in range(k):
            budget.tick()
            if consistent(v, c):
                color[v] = c
                venues.add(c, sizes[v])
                if rec(v + 1):
                    return True
                venues.remove(c, sizes[v])
                color[v] = -1
        return False

    return _finish("naive", inst, k, rec, (0,), color, budget)


def backtracking(inst, k, fc=True, mrv=True, degree=True, mac=False,
                 node_limit=None, time_limit=None):
    if mrv and not fc:
        raise ValueError("MRV needs the domains maintained by forward checking")
    n, adj, sizes = inst.n, inst.adj, inst.sizes
    color = [-1] * n
    domains = [set(c for c in inst.allowed[v] if c < k) for v in range(n)]
    unassigned = set(range(n))
    udeg = [len(adj[v]) for v in range(n)]
    venues = VenueState(inst, k)
    budget = Budget(node_limit, time_limit)
    limited_rooms = inst.venues is not None

    def select():
        if not mrv:
            return min(unassigned)
        if degree:
            return min(unassigned, key=lambda v: (len(domains[v]), -udeg[v], v))
        return min(unassigned, key=lambda v: (len(domains[v]), v))

    def consistent(v, c):
        for u in adj[v]:
            if color[u] == c:
                return False
        return venues.can_add(c, sizes[v])

    def remove(u, c, removed):
        domains[u].discard(c)
        removed.append((u, c))
        return bool(domains[u])

    def forward_check(v, c, removed):
        for u in adj[v]:
            if color[u] < 0 and c in domains[u]:
                if not remove(u, c, removed):
                    return False
        if limited_rooms:
            cap = venues.max_addable(c)
            for u in unassigned:
                if c in domains[u] and sizes[u] > cap:
                    if not remove(u, c, removed):
                        return False
        return True

    def propagate(v, removed):
        # Arc consistency for x != y: a variable with a single value d forces
        # d out of every neighbour's domain. Repeat until nothing changes.
        queue = [u for u in adj[v] if color[u] < 0 and len(domains[u]) == 1]
        done = set()
        while queue:
            u = queue.pop()
            if u in done:
                continue
            done.add(u)
            (d,) = tuple(domains[u])
            for w in adj[u]:
                if color[w] < 0 and d in domains[w]:
                    if not remove(w, d, removed):
                        return False
                    if len(domains[w]) == 1:
                        queue.append(w)
        return True

    def rec():
        if not unassigned:
            return True
        v = select()
        for c in sorted(domains[v]):
            budget.tick()
            if not fc and not consistent(v, c):
                continue
            if fc and not venues.can_add(c, sizes[v]):
                continue
            color[v] = c
            unassigned.discard(v)
            venues.add(c, sizes[v])
            for u in adj[v]:
                udeg[u] -= 1
            removed = []
            ok = True
            if fc:
                ok = forward_check(v, c, removed)
                if ok and mac:
                    ok = propagate(v, removed)
            if ok and rec():
                return True
            for u, d in removed:
                domains[u].add(d)
            for u in adj[v]:
                udeg[u] += 1
            venues.remove(c, sizes[v])
            unassigned.add(v)
            color[v] = -1
        return False

    name = "bt" + ("+fc" if fc else "") + ("+mrv" if mrv else "") + \
        ("+deg" if degree and mrv else "") + ("+mac" if mac else "")
    if any(not d for d in domains):
        return SolveResult(name, None, None, status="infeasible", extra={"k": k})
    return _finish(name, inst, k, rec, (), color, budget)


def _finish(name, inst, k, rec, args, color, budget):
    try:
        found = rec(*args)
        status = "solved" if found else "infeasible"
    except SearchLimit:
        found, status = False, "limit"
    seconds = budget.elapsed()
    nodes = min(budget.nodes, budget.node_limit) if budget.node_limit else budget.nodes
    if found:
        return SolveResult(name, color[:], slots_used(color), nodes, seconds,
                           status, extra={"k": k})
    return SolveResult(name, None, None, nodes, seconds, status, extra={"k": k})


def min_slots_backtracking(inst, solver=backtracking, node_limit=None,
                           time_limit=None, **options):
    """Find the minimum number of slots by trying k = LB, LB+1, ...

    This is the "iterative deepening on k" approach: every k below the answer
    must be refuted completely, which is where pruning matters most.
    """
    start = time.perf_counter()
    lb = lower_bound(inst)
    total = 0
    for k in range(lb, inst.num_slots + 1):
        remaining = None if time_limit is None else time_limit - (time.perf_counter() - start)
        if remaining is not None and remaining <= 0:
            break
        res = solver(inst, k, node_limit=node_limit, time_limit=remaining, **options)
        total += res.nodes
        if res.status == "solved":
            return SolveResult(f"min-{res.algorithm}", res.assignment, res.slots,
                               total, time.perf_counter() - start, "solved",
                               optimal=True, lower_bound=lb)
        if res.status == "limit":
            break
    return SolveResult("min-bt", None, None, total, time.perf_counter() - start,
                       "limit", lower_bound=lb)
