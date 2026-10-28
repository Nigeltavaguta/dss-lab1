# Coin change, minimum coins for a target amount, three ways: DP, greedy
# (largest coin first - optimal for canonical systems like USD, not in
# general), and BFS (same answer as DP, found by a different route -
# shortest path in a graph where amount -> amount - coin is an edge).
from collections import deque


def coin_change_dp(coins, amount):
    INF = float("inf")
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] != INF else -1


def coin_change_greedy(coins, amount):
    remaining = amount
    count = 0
    for c in sorted(coins, reverse=True):
        if remaining <= 0:
            break
        take = remaining // c
        count += take
        remaining -= take * c
    return count if remaining == 0 else -1


def coin_change_bfs(coins, amount):
    if amount == 0:
        return 0
    seen = {0}
    frontier = deque([0])
    depth = 0
    while frontier:
        depth += 1
        next_frontier = deque()
        for a in frontier:
            for c in coins:
                nxt = a + c
                if nxt == amount:
                    return depth
                if nxt < amount and nxt not in seen:
                    seen.add(nxt)
                    next_frontier.append(nxt)
        frontier = next_frontier
    return -1
