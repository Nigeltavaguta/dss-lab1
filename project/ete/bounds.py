"""Lower bounds on the number of slots (timetable length).

* Clique bound: any set of pairwise-conflicting exams needs distinct slots,
  so chi(G) >= omega(G) >= |C| for every clique C found.
* Venue bound: an exam of size >= s can only use a venue of capacity >= s,
  and a venue hosts at most one exam per slot, so at least
  ceil(#exams of size >= s / #venues of capacity >= s) slots are needed,
  for every threshold s.
Both are valid for the timetable-length objective even when some slots are
unavailable to some exams.
"""

from __future__ import annotations


def greedy_clique(adj):
    """Return a large clique (list of vertices) found greedily.

    Each vertex in turn seeds a clique. The clique is then grown by repeatedly
    adding the candidate with the most neighbours among the remaining
    candidates. Time O(n * d^2) for maximum degree d.
    """
    n = len(adj)
    best = []
    for seed in range(n):
        if len(adj[seed]) + 1 <= len(best):
            continue  # cannot beat the current best
        clique = [seed]
        candidates = set(adj[seed])
        while candidates:
            v = max(candidates, key=lambda u: (len(adj[u] & candidates), -u))
            clique.append(v)
            candidates &= adj[v]
        if len(clique) > len(best):
            best = clique
    return best


def clique_bound(inst):
    return max(1, len(greedy_clique(inst.adj))) if inst.n else 0


def venue_bound(inst):
    if inst.venues is None or inst.n == 0:
        return 0
    caps = inst.caps_desc
    best = 0
    for s in set(inst.sizes):
        exams = sum(1 for x in inst.sizes if x >= s)
        rooms = sum(1 for c in caps if c >= s)
        if rooms == 0:
            return inst.num_slots + 1  # some exam fits no venue: infeasible
        best = max(best, -(-exams // rooms))
    return best


def lower_bound(inst):
    return max(clique_bound(inst), venue_bound(inst), 1 if inst.n else 0)
