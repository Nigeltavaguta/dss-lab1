# Instance generators for the three problems, all seeded for repeatability.
import math
import random


def knapsack_instance(n, seed, max_value=100, max_weight=50):
    rng = random.Random(seed)
    values = [rng.randint(1, max_value) for _ in range(n)]
    weights = [rng.randint(1, max_weight) for _ in range(n)]
    capacity = sum(weights) // 2
    return values, weights, capacity


# Coin systems: USD-style is canonical (greedy always matches DP). The
# second set is the classic non-canonical counterexample.
CANONICAL_COINS = [1, 5, 10, 25]
NON_CANONICAL_COINS = [1, 3, 4]


def tsp_instance(n, seed, size=100):
    rng = random.Random(seed)
    points = [(rng.uniform(0, size), rng.uniform(0, size)) for _ in range(n)]
    dist = [[math.dist(points[i], points[j]) for j in range(n)] for i in range(n)]
    return points, dist
