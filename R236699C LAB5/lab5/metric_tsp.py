# Metric TSP: exact Held-Karp DP (small n) and the double-MST
# 2-approximation. dist must satisfy the triangle inequality for the
# approximation's guarantee to hold - datasets.py builds it from
# Euclidean points, which always does.


def tour_length(dist, tour):
    n = len(tour)
    return sum(dist[tour[i]][tour[(i + 1) % n]] for i in range(n))


def tsp_held_karp(dist):
    n = len(dist)
    if n == 1:
        return [0], 0
    dp = {(1, 0): 0}
    parent = {}
    for mask in range(1, 1 << n):
        if not (mask & 1):
            continue
        for j in range(n):
            if not (mask & (1 << j)) or (mask, j) not in dp:
                continue
            cost_j = dp[(mask, j)]
            for k in range(n):
                if mask & (1 << k):
                    continue
                new_mask = mask | (1 << k)
                new_cost = cost_j + dist[j][k]
                if (new_mask, k) not in dp or new_cost < dp[(new_mask, k)]:
                    dp[(new_mask, k)] = new_cost
                    parent[(new_mask, k)] = j
    full = (1 << n) - 1
    best_cost, best_end = min((dp[(full, j)] + dist[j][0], j) for j in range(1, n))
    path, mask, j = [0], full, best_end
    rev = []
    while j != 0:
        rev.append(j)
        mask, j = mask ^ (1 << j), parent[(mask, j)]
    path = [0] + rev[::-1]
    return path, best_cost


def prim_mst(dist):
    # O(n^2) Prim's.
    n = len(dist)
    in_tree = [False] * n
    best_cost = [float("inf")] * n
    best_parent = [-1] * n
    best_cost[0] = 0
    tree_edges = []
    for _ in range(n):
        u = min((v for v in range(n) if not in_tree[v]), key=lambda v: best_cost[v])
        in_tree[u] = True
        if best_parent[u] != -1:
            tree_edges.append((best_parent[u], u))
        for v in range(n):
            if not in_tree[v] and dist[u][v] < best_cost[v]:
                best_cost[v] = dist[u][v]
                best_parent[v] = u
    return tree_edges


def two_approx_tsp(dist):
    # Double-tree: MST + DFS preorder, shortcutting past visited vertices.
    # Ratio-2 proof in report Section 3.
    n = len(dist)
    tree_edges = prim_mst(dist)
    adj = [[] for _ in range(n)]
    for u, v in tree_edges:
        adj[u].append(v)
        adj[v].append(u)
    visited = [False] * n
    order = []

    def dfs(u):
        visited[u] = True
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                dfs(v)

    dfs(0)
    return order, tour_length(dist, order)
