# Orienteering: the knapsack+TSP synthesis problem from the report. Cities
# have values; pick a subset and a route visiting them, starting and ending
# at the depot (city 0), that fits a travel budget and maximizes total
# value collected. Held-Karp's DP with an extra value dimension.

def orienteering_dp(dist, values, budget):
    n = len(dist)
    INF = float("inf")
    # dp[(mask, j)] = cheapest travel cost to start at depot, visit exactly
    # the cities in mask, end at j. Same state space as Held-Karp.
    dp = {(1, 0): 0.0}
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
                if new_cost < dp.get((new_mask, k), INF):
                    dp[(new_mask, k)] = new_cost

    best_value, best_mask = 0, 1
    for (mask, j), cost in dp.items():
        if cost + dist[j][0] <= budget:
            value = sum(values[i] for i in range(n) if mask & (1 << i))
            if value > best_value:
                best_value, best_mask = value, mask
    visited = [i for i in range(n) if best_mask & (1 << i)]
    return best_value, visited


if __name__ == "__main__":
    # Tiny demo: a depot plus 5 cities, each with a value; budget too small
    # to visit all of them, so the DP has to choose which are worth it.
    import datasets
    _, dist = datasets.tsp_instance(6, seed=3, size=50)
    values = [0, 40, 10, 25, 60, 15]  # depot has no value
    for budget in (80, 130, 200):
        value, visited = orienteering_dp(dist, values, budget)
        print(f"budget={budget}: best value={value}, cities visited={visited}")
