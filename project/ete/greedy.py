"""Greedy (sequential) colouring heuristics.

Each exam, taken in some order, receives the lowest-numbered slot that is
allowed for its lecturer, unused by its conflicting neighbours and still has
a free venue large enough. Orders:

* ``"natural"``: exam index order (used for the adversarial crown example);
* ``"largest_first"``: Welsh-Powell, decreasing degree;
* ``"dsatur"``: Brelaz's DSATUR, most distinct neighbouring slots first;
* ``"random"``: a seeded random permutation;
* or an explicit list of exam indices.
"""

from __future__ import annotations

import random
import time

from .model import SolveResult, VenueState, slots_used


def _first_fit(inst, v, color, used_by_neighbours, venues):
    for c in range(inst.num_slots):
        if c in used_by_neighbours:
            continue
        if c not in inst.allowed[v]:
            continue
        if not venues.can_add(c, inst.sizes[v]):
            continue
        return c
    return -1


def greedy(inst, order="dsatur", seed=0):
    start = time.perf_counter()
    n = inst.n
    color = [-1] * n
    venues = VenueState(inst, inst.num_slots)
    failed = 0

    if order == "dsatur":
        saturation = [set() for _ in range(n)]
        uncolored = set(range(n))
        while uncolored:
            v = max(uncolored, key=lambda u: (len(saturation[u]), len(inst.adj[u]), -u))
            uncolored.discard(v)
            c = _first_fit(inst, v, color, saturation[v], venues)
            if c < 0:
                failed += 1
                continue
            color[v] = c
            venues.add(c, inst.sizes[v])
            for u in inst.adj[v]:
                saturation[u].add(c)
    else:
        if order == "natural":
            seq = list(range(n))
        elif order == "largest_first":
            seq = sorted(range(n), key=lambda v: (-len(inst.adj[v]), v))
        elif order == "random":
            seq = list(range(n))
            random.Random(seed).shuffle(seq)
        else:
            seq = list(order)
        for v in seq:
            used = {color[u] for u in inst.adj[v] if color[u] >= 0}
            c = _first_fit(inst, v, color, used, venues)
            if c < 0:
                failed += 1
                continue
            color[v] = c
            venues.add(c, inst.sizes[v])

    seconds = time.perf_counter() - start
    name = f"greedy-{order if isinstance(order, str) else 'custom'}"
    if failed:
        return SolveResult(name, color, None, seconds=seconds, status="failed",
                           extra={"unplaced": failed})
    return SolveResult(name, color, slots_used(color), seconds=seconds)
