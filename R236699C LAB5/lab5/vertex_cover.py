# Minimum Vertex Cover: exact branch-and-bound, and the matching-based
# 2-approximation. Graphs are adj: list of sets, same convention as lab4.


def edge_list(adj):
    n = len(adj)
    return [(u, v) for u in range(n) for v in adj[u] if v > u]


def approx_vertex_cover(adj):
    # Picked edges form a maximal matching (each discard removes every
    # edge touching the chosen pair) - 2-approximation, proof in report.
    remaining = set(edge_list(adj))
    cover = set()
    while remaining:
        u, v = next(iter(remaining))
        cover.add(u)
        cover.add(v)
        remaining = {(a, b) for (a, b) in remaining if a not in (u, v) and b not in (u, v)}
    return cover, len(cover)


def min_vertex_cover_bb(adj):
    # Branch on "include u" / "include v" for an uncovered edge; prune once
    # partial depth reaches the best cover found. Seeded with the
    # 2-approximation's size for a tighter initial bound than n.
    edges = edge_list(adj)
    approx_cover, approx_size = approx_vertex_cover(adj)
    best = [approx_size]
    best_cover = [set(approx_cover)]
    nodes = [0]

    def first_uncovered(covered):
        for (u, v) in edges:
            if u not in covered and v not in covered:
                return u, v
        return None

    def rec(covered, depth):
        nodes[0] += 1
        if depth >= best[0]:
            return
        edge = first_uncovered(covered)
        if edge is None:
            best[0] = depth
            best_cover[0] = set(covered)
            return
        u, v = edge
        rec(covered | {u}, depth + 1)
        rec(covered | {v}, depth + 1)

    rec(set(), 0)
    if best_cover[0] is None:
        return set(), approx_size, nodes[0]
    return best_cover[0], best[0], nodes[0]


def is_vertex_cover(adj, cover):
    return all(u in cover or v in cover for u, v in edge_list(adj))
