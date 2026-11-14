# Instance generators, all seeded.
import random


def random_graph(n, p, seed):
    rng = random.Random(seed)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def euclidean_points(n, seed, width=100):
    rng = random.Random(seed)
    return [(rng.uniform(0, width), rng.uniform(0, width)) for _ in range(n)]


def dist_matrix(points):
    # Euclidean distance satisfies the triangle inequality by construction.
    n = len(points)
    return [
        [((points[i][0] - points[j][0]) ** 2 + (points[i][1] - points[j][1]) ** 2) ** 0.5 for j in range(n)]
        for i in range(n)
    ]


def subset_sum_instance(n, seed, max_weight=1000):
    rng = random.Random(seed)
    weights = [rng.randint(1, max_weight) for _ in range(n)]
    target = int(sum(weights) * rng.uniform(0.3, 0.6))
    return weights, target
