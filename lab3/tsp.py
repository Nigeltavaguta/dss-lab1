# TSP: exact DP (Held-Karp), nearest-neighbor greedy, and 2-opt local
# search starting from the greedy tour. dist is a full n x n matrix.

def tsp_held_karp(dist):
    n = len(dist)
    if n == 1:
        return 0, [0]
    # dp[(mask, j)] = cheapest way to start at 0, visit exactly the cities
    # in mask, and end at j. mask always includes city 0 and city j.
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
    best_cost, best_end = min(
        (dp[(full, j)] + dist[j][0], j) for j in range(1, n)
    )
    path = [0]
    mask, j = full, best_end
    rev = []
    while j != 0:
        rev.append(j)
        mask, j = mask ^ (1 << j), parent[(mask, j)]
    path = [0] + rev[::-1]
    return best_cost, path


def tour_length(dist, tour):
    n = len(tour)
    return sum(dist[tour[i]][tour[(i + 1) % n]] for i in range(n))


def tsp_nearest_neighbor(dist, start=0):
    n = len(dist)
    unvisited = set(range(n)) - {start}
    tour = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda c: dist[current][c])
        tour.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return tour, tour_length(dist, tour)


def tsp_two_opt(dist, tour):
    # Repeatedly reverse a segment if doing so shortens the tour, until no
    # single reversal helps. Local search, not exact - can still land in a
    # local optimum worse than Held-Karp's true best.
    n = len(tour)
    tour = tour[:]
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                delta = (dist[a][c] + dist[b][d]) - (dist[a][b] + dist[c][d])
                if delta < -1e-9:
                    tour[i + 1 : j + 1] = tour[i + 1 : j + 1][::-1]
                    improved = True
    return tour, tour_length(dist, tour)
