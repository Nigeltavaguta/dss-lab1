"""Tabu search (TabuCol, Hertz and de Werra 1987; Galinier and Hao 1999)
adapted to exam timetabling.

To shorten a timetable of length k to k-1, the exams in the last slot are
moved into slots 0..k-2. These moves may create student or lecturer
conflicts and leave some exams without a venue, which the search then tries
to remove. The objective is (conflicting pairs) + (exams that cannot be
seated in a slot, i.e. exams minus a maximum exam-to-venue matching).
Lecturer availability is never relaxed: a move must go to a slot that is
open to the exam's lecturer.

Each iteration makes the best move of a conflicting or unseated exam to another slot.
After an exam leaves slot c, moving it back to c is forbidden (tabu) for
0.6 * (number of conflicting exams) + rand(0..9) iterations. A tabu move is
still allowed if it gives the best objective value seen so far (the
aspiration criterion).
"""

from __future__ import annotations

import bisect
import random
import time

from .bounds import lower_bound
from .model import SolveResult, VenueState, slots_used


def _matched(load, caps_asc):
    """Size of a maximum exam-to-venue matching for one slot (ascending)."""
    i = 0
    for cap in caps_asc:
        if i < len(load) and load[i] <= cap:
            i += 1
    return i


class _SlotPenalty:
    """Venue overflow per slot: exams that cannot be seated."""

    def __init__(self, inst, k):
        self.unlimited = inst.venues is None
        self.caps_asc = sorted(inst.caps_desc) if not self.unlimited else []
        self.values = inst.cap_values or []
        self.loads = [[] for _ in range(k)]
        self.pen = [0] * k
        self.tau = [float("inf")] * k

    def refresh(self, c):
        if self.unlimited:
            return
        load = self.loads[c]
        m = _matched(load, self.caps_asc)
        self.pen[c] = len(load) - m
        # tau: the largest size whose addition still raises the matching
        # (so adds no penalty). Monotone in size, so binary search works.
        lo, hi, best = 0, len(self.values) - 1, 0
        while lo <= hi:
            mid = (lo + hi) // 2
            trial = load[:]
            bisect.insort(trial, self.values[mid])
            if _matched(trial, self.caps_asc) > m:
                best = self.values[mid]
                lo = mid + 1
            else:
                hi = mid - 1
        self.tau[c] = best

    def add_cost(self, c, size):
        return 0 if size <= self.tau[c] else 1

    def remove_gain(self, c, size):
        if self.unlimited or self.pen[c] == 0:
            return 0
        load = self.loads[c][:]
        del load[bisect.bisect_left(load, size)]
        return self.pen[c] - (len(load) - _matched(load, self.caps_asc))

    def add(self, c, size):
        if not self.unlimited:
            bisect.insort(self.loads[c], size)

    def remove(self, c, size):
        if not self.unlimited:
            load = self.loads[c]
            del load[bisect.bisect_left(load, size)]


def tabucol(inst, assignment, k, rng, max_iters=20000, deadline=None):
    """Try to repair ``assignment`` into a conflict-free timetable on k slots.

    The objective is (conflicting pairs) + (exams without a venue). Lecturer
    availability stays a hard constraint. Returns (timetable or None, iterations).
    """
    n, adj, sizes, allowed = inst.n, inst.adj, inst.sizes, inst.allowed
    slot = [c if 0 <= c < k else -1 for c in assignment]
    pen = _SlotPenalty(inst, k)
    gamma = [[0] * k for _ in range(n)]
    for v in range(n):
        if slot[v] >= 0:
            pen.add(slot[v], sizes[v])
            for u in adj[v]:
                gamma[u][slot[v]] += 1
    for c in range(k):
        pen.refresh(c)

    displaced = sorted((v for v in range(n) if slot[v] < 0), key=lambda v: -sizes[v])
    for v in displaced:
        options = [c for c in range(k) if c in allowed[v]]
        if not options:
            return None, 0
        cost = {c: gamma[v][c] + pen.add_cost(c, sizes[v]) for c in options}
        low = min(cost.values())
        c = rng.choice([c for c in options if cost[c] == low])
        slot[v] = c
        pen.add(c, sizes[v])
        pen.refresh(c)
        for u in adj[v]:
            gamma[u][c] += 1

    f = sum(gamma[v][slot[v]] for v in range(n)) // 2 + sum(pen.pen)
    best_f = f
    tabu = [[0] * k for _ in range(n)]
    it = 0
    while f > 0 and it < max_iters:
        it += 1
        if deadline is not None and (it & 31) == 0 and time.perf_counter() > deadline:
            break
        best_delta = None
        moves = []
        candidates = 0
        for v in range(n):
            gv = gamma[v]
            cur = slot[v]
            gc = gv[cur]
            if gc == 0 and pen.pen[cur] == 0:
                continue
            candidates += 1
            sz = sizes[v]
            av = allowed[v]
            tv = tabu[v]
            base = gc + pen.remove_gain(cur, sz)
            for c in range(k):
                if c == cur or c not in av:
                    continue
                d = gv[c] + (0 if sz <= pen.tau[c] else 1) - base
                if tv[c] > it and f + d >= best_f:
                    continue
                if best_delta is None or d < best_delta:
                    best_delta = d
                    moves = [(v, c)]
                elif d == best_delta:
                    moves.append((v, c))
        if not moves:
            continue
        v, c = rng.choice(moves)
        old = slot[v]
        for u in adj[v]:
            gamma[u][old] -= 1
            gamma[u][c] += 1
        pen.remove(old, sizes[v])
        pen.add(c, sizes[v])
        pen.refresh(old)
        pen.refresh(c)
        slot[v] = c
        f += best_delta
        tabu[v][old] = it + int(0.6 * candidates) + rng.randint(0, 9)
        best_f = min(best_f, f)
    return (slot if f == 0 else None), it


def local_search(inst, assignment, lb=None, time_limit=5.0, seed=0,
                 max_iters=20000):
    """Shorten a feasible timetable one slot at a time with TabuCol."""
    start = time.perf_counter()
    deadline = start + time_limit
    rng = random.Random(seed)
    if lb is None:
        lb = lower_bound(inst)
    best = assignment[:]
    k = slots_used(best)
    trace = [(0.0, k)]
    iterations = 0
    while k > lb and time.perf_counter() < deadline:
        sol, its = tabucol(inst, best, k - 1, rng, max_iters, deadline)
        iterations += its
        if sol is None:
            break
        best = sol
        k = slots_used(sol)
        trace.append((time.perf_counter() - start, k))
    return SolveResult("tabu", best, k, iterations, time.perf_counter() - start,
                       "solved", k <= lb, lb, extra={"trace": trace})
