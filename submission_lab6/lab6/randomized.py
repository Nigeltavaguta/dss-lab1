"""Randomized algorithms used in the Lab 6 experiments."""

from __future__ import annotations

import math
import random


def randomized_quicksort(values, seed=0):
    """Return a sorted copy and its comparison count using random pivots."""
    a = list(values)
    rng = random.Random(seed)
    comparisons = 0
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        pivot_index = rng.randrange(lo, hi + 1)
        a[pivot_index], a[hi] = a[hi], a[pivot_index]
        pivot = a[hi]
        i = lo
        for j in range(lo, hi):
            comparisons += 1
            if a[j] <= pivot:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        # Process the smaller side immediately; defer the larger side.
        left, right = (lo, i - 1), (i + 1, hi)
        if left[1] - left[0] > right[1] - right[0]:
            left, right = right, left
        if right[0] < right[1]:
            stack.append(right)
        if left[0] < left[1]:
            stack.append(left)
    return a, comparisons


def miller_rabin(n, rounds=20, seed=0):
    """Probabilistic primality test; false-prime probability <= 4**(-rounds)."""
    if rounds < 1:
        raise ValueError("rounds must be positive")
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False
    if n % 2 == 0:
        return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    rng = random.Random(seed)
    for _ in range(rounds):
        a = rng.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def karger_min_cut(n, edges, seed=0):
    """One Karger contraction trial on an undirected multigraph edge list."""
    if n < 2:
        return 0
    rng = random.Random(seed)
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    remaining = list(edges)
    components = n
    while components > 2:
        valid = [(u, v) for u, v in remaining if find(u) != find(v)]
        if not valid:
            break
        u, v = rng.choice(valid)
        ru, rv = find(u), find(v)
        if size[ru] < size[rv]:
            ru, rv = rv, ru
        parent[rv] = ru
        size[ru] += size[rv]
        components -= 1
    return sum(find(u) != find(v) for u, v in edges)


def repeat_karger(n, edges, trials=100, seed=0):
    """Return best cut and all trial results."""
    cuts = [karger_min_cut(n, edges, seed + i) for i in range(trials)]
    return min(cuts), cuts


def karger_trials_for_failure(n, delta):
    """Sufficient trials from the basic 2/(n(n-1)) success bound."""
    if n < 2 or not 0 < delta < 1:
        raise ValueError("require n >= 2 and 0 < delta < 1")
    p = 2 / (n * (n - 1))
    return math.ceil(math.log(delta) / math.log1p(-p))


def planted_cut_graph(n=10, cut_size=3):
    """Two internally complete groups joined by cut_size edges; known min cut."""
    if n < 4 or cut_size < 1:
        raise ValueError("require n >= 4 and cut_size >= 1")
    split = n // 2
    edges = []
    for group in (range(split), range(split, n)):
        group = list(group)
        edges.extend((group[i], group[j]) for i in range(len(group)) for j in range(i + 1, len(group)))
    for i in range(cut_size):
        edges.append((i % split, split + (i % (n - split))))
    return edges, cut_size
