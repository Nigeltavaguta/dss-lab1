"""Hybrid solver: greedy construction, tabu search, then branch-and-bound
with local-search polishing of every incumbent.

Phase 1 (construct): DSATUR and Welsh-Powell, and if both fail, a few
          random orders. The shortest feasible timetable becomes the first
          upper bound UB.
Phase 2 (improve):   TabuCol removes slots one at a time until it fails or
          reaches the lower bound LB.
Phase 3 (prove):     Branch-and-bound starts from the tabu timetable as its
          incumbent. Whenever B&B finds a better timetable, a short tabu
          run tries to shorten it further before the search continues.
          If the B&B search finishes within the time budget, the result is
          proven optimal. Otherwise the solver reports the remaining gap
          UB - LB.

Every phase stops as soon as UB = LB, since that proves optimality.
"""

from __future__ import annotations

import time

from .bounds import lower_bound
from .branch_bound import branch_and_bound
from .greedy import greedy
from .local_search import local_search
from .model import SolveResult, slots_used


def hybrid(inst, time_limit=10.0, seed=0, ls_share=0.4, polish_time=0.3):
    start = time.perf_counter()
    lb = lower_bound(inst)
    trace = []
    phases = {}

    def now():
        return time.perf_counter() - start

    def result(assignment, optimal):
        k = slots_used(assignment)
        return SolveResult("hybrid", assignment, k, nodes, now(), "solved",
                           optimal, lb, extra={"trace": trace, "phases": phases,
                                               "gap": k - lb})

    nodes = 0
    best = None
    for order in ("dsatur", "largest_first"):
        g = greedy(inst, order)
        if g.status == "solved" and (best is None or g.slots < slots_used(best)):
            best = g.assignment
    tries = 0
    while best is None and tries < 20:
        g = greedy(inst, "random", seed=seed * 100 + tries)
        tries += 1
        if g.status == "solved":
            best = g.assignment
    if best is None:
        return SolveResult("hybrid", None, None, 0, now(), "failed", False, lb)
    phases["greedy"] = slots_used(best)
    trace.append((now(), slots_used(best)))
    if slots_used(best) <= lb:
        return result(best, True)

    ls_start = now()
    ls = local_search(inst, best, lb, time_limit * ls_share, seed)
    nodes += ls.nodes
    for t, k in ls.extra["trace"][1:]:
        trace.append((ls_start + t, k))
    if ls.slots < slots_used(best):
        best = ls.assignment
    phases["tabu"] = slots_used(best)
    if slots_used(best) <= lb:
        return result(best, True)

    offset = now()

    def polish(assignment, ub):
        r = local_search(inst, assignment, lb, polish_time, seed)
        return r.assignment if r.slots < ub else None

    remaining = max(0.0, time_limit - offset)
    bb = branch_and_bound(inst, initial=best, time_limit=remaining,
                          on_improve=polish, lb=lb)
    nodes += bb.nodes
    for t, k in bb.extra["trace"][1:]:
        trace.append((offset + t, k))
    if bb.assignment is not None and slots_used(bb.assignment) < slots_used(best):
        best = bb.assignment
    phases["bnb"] = slots_used(best)
    return result(best, bb.optimal)
