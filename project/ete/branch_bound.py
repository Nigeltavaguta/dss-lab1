"""Branch-and-bound for the optimisation problem: minimise the timetable
length (number of slots).

The search is depth-first. Exams are chosen DSATUR/MRV-style: fewest live
slots first, ties broken by unassigned degree.

* Upper bound UB: the best complete timetable so far. Its initial value
  comes from DSATUR, from a timetable passed in, or from the horizon T+1.
  Each exam may use only slots 0..UB-2. A complete assignment therefore
  always improves on UB, and anything that cannot beat UB is cut off.
* Lower bound LB: max(clique bound, venue bound). When a timetable of
  length LB is found, it is optimal and the search stops.
* Forward checking: the same domain filtering as in ``backtracking``. A
  domain with no slot below the current limit is a dead end.
* Symmetry breaking: when every slot is interchangeable (no availability
  restrictions), an exam may use any slot already in use or the single
  lowest unused slot. Each set of equivalent timetables is then explored
  only once.

``on_improve(assignment, ub)`` is called on every new incumbent. If it
returns a strictly better timetable (the hybrid solver uses local search
for this), that timetable becomes the incumbent.
"""

from __future__ import annotations

import time

from .backtracking import Budget, SearchLimit
from .bounds import lower_bound
from .greedy import greedy
from .model import SolveResult, VenueState, slots_used


class _Optimal(Exception):
    pass


def branch_and_bound(inst, initial=None, use_lower_bound=True,
                     use_greedy_ub=True, node_limit=None, time_limit=None,
                     on_improve=None, lb=None):
    budget = Budget(node_limit, time_limit)
    n, adj, sizes, T = inst.n, inst.adj, inst.sizes, inst.num_slots
    if lb is None:
        lb = lower_bound(inst) if use_lower_bound else 1
    state = {"best": None, "ub": T + 1}
    trace = []

    def record(assignment):
        state["best"] = assignment[:]
        state["ub"] = slots_used(assignment)
        trace.append((budget.elapsed(), state["ub"]))

    if initial is not None:
        record(initial)
    elif use_greedy_ub:
        g = greedy(inst, "dsatur")
        if g.status == "solved":
            record(g.assignment)

    def done(status, optimal):
        best = state["best"]
        return SolveResult("bnb", best, slots_used(best) if best else None,
                           budget.nodes, budget.elapsed(), status, optimal, lb,
                           extra={"trace": trace})

    if state["best"] is not None and state["ub"] <= lb:
        return done("solved", True)

    color = [-1] * n
    domains = [set(inst.allowed[v]) for v in range(n)]
    unassigned = set(range(n))
    udeg = [len(adj[v]) for v in range(n)]
    venues = VenueState(inst, T)
    used_count = [0] * T
    used = [0]                      # number of distinct slots in use
    symmetric = inst.symmetric
    limited_rooms = inst.venues is not None

    def live(u):
        limit = state["ub"] - 1
        return sum(1 for c in domains[u] if c < limit)

    def select():
        return min(unassigned, key=lambda v: (live(v), -udeg[v], v))

    def forward_check(v, c, removed):
        limit = state["ub"] - 1
        for u in adj[v]:
            if color[u] < 0 and c in domains[u]:
                domains[u].discard(c)
                removed.append((u, c))
                if not any(d < limit for d in domains[u]):
                    return False
        if limited_rooms:
            cap = venues.max_addable(c)
            for u in unassigned:
                if c in domains[u] and sizes[u] > cap:
                    domains[u].discard(c)
                    removed.append((u, c))
                    if not any(d < limit for d in domains[u]):
                        return False
        return True

    def leaf():
        record(color)
        if on_improve is not None:
            better = on_improve(color[:], state["ub"])
            if better is not None and slots_used(better) < state["ub"]:
                record(better)
        if state["ub"] <= lb:
            raise _Optimal

    def rec():
        # Bound: after the incumbent improves, a partial timetable that
        # already uses a slot >= UB - 1 cannot lead to a better one.
        for c in range(state["ub"] - 1, T):
            if used_count[c]:
                return
        if not unassigned:
            leaf()
            return
        v = select()
        for c in sorted(domains[v]):
            if c >= state["ub"] - 1:
                break                       # bound: cannot beat the incumbent
            if symmetric and c > used[0]:
                break                       # symmetry: at most one new slot
            budget.tick()
            if not venues.can_add(c, sizes[v]):
                continue
            color[v] = c
            unassigned.discard(v)
            venues.add(c, sizes[v])
            used_count[c] += 1
            if used_count[c] == 1:
                used[0] += 1
            for u in adj[v]:
                udeg[u] -= 1
            removed = []
            if forward_check(v, c, removed):
                rec()
            for u, d in removed:
                domains[u].add(d)
            for u in adj[v]:
                udeg[u] += 1
            used_count[c] -= 1
            if used_count[c] == 0:
                used[0] -= 1
            venues.remove(c, sizes[v])
            unassigned.add(v)
            color[v] = -1

    try:
        rec()
    except _Optimal:
        return done("solved", True)
    except SearchLimit:
        return done("limit" if state["best"] is None else "solved", False)
    if state["best"] is None:
        return done("infeasible", True)
    return done("solved", True)
