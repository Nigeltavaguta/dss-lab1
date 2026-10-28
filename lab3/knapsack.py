# 0-1 knapsack: 2D DP, 1D DP, branch and bound, plus the fractional greedy
# (which is optimal for the fractional version, not the 0-1 version - see
# report for the counterexample).

def knapsack_2d(values, weights, capacity):
    n = len(values)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if wi <= w:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - wi] + vi)
    return dp[n][capacity]


def knapsack_1d(values, weights, capacity):
    # Same recurrence as knapsack_2d, but only one row is ever live at a
    # time. Iterating w backwards stops a row from overwriting a value it
    # still needs this round, which is what makes O(W) space safe here.
    dp = [0] * (capacity + 1)
    for vi, wi in zip(values, weights):
        for w in range(capacity, wi - 1, -1):
            dp[w] = max(dp[w], dp[w - wi] + vi)
    return dp[capacity]


def knapsack_branch_and_bound(values, weights, capacity):
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i] / weights[i], reverse=True)
    values = [values[i] for i in order]
    weights = [weights[i] for i in order]

    def bound(i, value, weight):
        # Fractional relaxation from item i onward: an upper bound on what
        # any completion of this partial solution could still reach.
        if weight >= capacity:
            return value
        bound_value = value
        bound_weight = weight
        while i < n and bound_weight + weights[i] <= capacity:
            bound_value += values[i]
            bound_weight += weights[i]
            i += 1
        if i < n:
            bound_value += (capacity - bound_weight) * values[i] / weights[i]
        return bound_value

    best = 0
    nodes_explored = 0
    # DFS with a cutoff: only descend into a branch if its relaxed bound
    # could still beat the best complete solution found so far.
    stack = [(0, 0, 0)]  # (item index, accumulated value, accumulated weight)
    while stack:
        i, value, weight = stack.pop()
        nodes_explored += 1
        if value > best:
            best = value
        if i == n or bound(i, value, weight) <= best:
            continue
        # exclude item i
        stack.append((i + 1, value, weight))
        # include item i, if it fits
        if weight + weights[i] <= capacity:
            stack.append((i + 1, value + values[i], weight + weights[i]))
    return best, nodes_explored


def fractional_knapsack_greedy(values, weights, capacity):
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i] / weights[i], reverse=True)
    remaining = capacity
    total = 0.0
    for i in order:
        if remaining <= 0:
            break
        take = min(weights[i], remaining)
        total += values[i] * (take / weights[i])
        remaining -= take
    return total
