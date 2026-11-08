# Exam timetabling as graph coloring: exams are vertices, a conflict edge
# means two exams share a student, a color is a time slot. Graphs are
# represented as adj: list of sets, adj[v] = neighbors of v.

import itertools


def naive_backtracking(adj, k):
    # Try to k-color the graph in vertex-index order, no lookahead: just
    # try colors 0..k-1 at each vertex and check against already-colored
    # neighbors. Backtracks on conflict, nothing smarter than that.
    n = len(adj)
    color = [-1] * n
    nodes = [0]

    def ok(v, c):
        return all(color[u] != c for u in adj[v] if color[u] != -1)

    def rec(v):
        if v == n:
            return True
        for c in range(k):
            nodes[0] += 1
            if ok(v, c):
                color[v] = c
                if rec(v + 1):
                    return True
                color[v] = -1
        return False

    if rec(0):
        return color[:], nodes[0]
    return None, nodes[0]


def backtracking_fc_mrv(adj, k):
    # Same decision problem, two real improvements:
    #   - forward checking: after coloring v, remove that color from every
    #     uncolored neighbor's domain; if a domain goes empty, fail this
    #     branch immediately instead of discovering it several levels down
    #   - MRV: always branch on the uncolored vertex with the smallest
    #     remaining domain (most constrained first), which tends to hit
    #     failures earlier and prune more of the tree
    n = len(adj)
    color = [-1] * n
    domains = [set(range(k)) for _ in range(n)]
    nodes = [0]

    def select_var(uncolored):
        return min(uncolored, key=lambda v: (len(domains[v]), -len(adj[v])))

    def rec(uncolored):
        if not uncolored:
            return True
        v = select_var(uncolored)
        remaining = uncolored - {v}
        for c in sorted(domains[v]):
            nodes[0] += 1
            color[v] = c
            removed = []  # (neighbor, color) pairs we trimmed, to undo
            dead = False
            for u in adj[v]:
                if u in remaining and c in domains[u]:
                    domains[u].discard(c)
                    removed.append(u)
                    if not domains[u]:
                        dead = True
                        break
            if not dead and rec(remaining):
                return True
            for u in removed:
                domains[u].add(c)
            color[v] = -1
        return False

    if rec(set(range(n))):
        return color[:], nodes[0]
    return None, nodes[0]


def greedy_clique_lower_bound(adj):
    # chi(G) >= omega(G) (clique number), and omega is itself NP-hard to
    # get exactly, so this is a cheap greedy clique used only to seed a
    # valid lower bound for the branch-and-bound search below.
    n = len(adj)
    order = sorted(range(n), key=lambda v: -len(adj[v]))
    clique = []
    for v in order:
        if all(v in adj[u] for u in clique):
            clique.append(v)
    return len(clique)


def branch_and_bound_chromatic(adj):
    # Finds the exact chromatic number by trying k = lower_bound, lower_bound+1, ...
    # and asking "is this k enough" with the FC+MRV search above, which is
    # itself already pruning aggressively. The real B&B idea sits on top: a
    # clique lower bound lets us skip straight past k values we already
    # know cannot work, rather than starting from k=1 every time.
    lb = max(1, greedy_clique_lower_bound(adj))
    total_nodes = 0
    for k in range(lb, len(adj) + 1):
        coloring, nodes = backtracking_fc_mrv(adj, k)
        total_nodes += nodes
        if coloring is not None:
            return k, coloring, total_nodes
    return len(adj), list(range(len(adj))), total_nodes


def greedy_coloring(adj, order=None):
    # Welsh-Powell by default: color vertices highest-degree-first, each
    # one gets the smallest color not already used by a colored neighbor.
    n = len(adj)
    if order is None:
        order = sorted(range(n), key=lambda v: -len(adj[v]))
    color = [-1] * n
    for v in order:
        used = {color[u] for u in adj[v] if color[u] != -1}
        c = 0
        while c in used:
            c += 1
        color[v] = c
    return color, (max(color) + 1 if color else 0)
