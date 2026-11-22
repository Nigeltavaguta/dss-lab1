"""
Benchmarks for the Group 11 DAA presentation.

Part A — Celebrity Problem: brute force O(n^2) vs candidate elimination O(n).
         Measures exact knows() query counts and median wall-clock time.

Part B — Coin Change: how often the greedy algorithm is actually optimal,
         measured against the dynamic programming optimum.

Run:  python3 benchmark.py
Out:  results.json  (plus a printed summary)
"""

import json
import random
import statistics
import time

RNG_SEED = 20261117
REPEATS = 5


# ----------------------------------------------------------------------
# Part A — Celebrity Problem
# ----------------------------------------------------------------------

class Party:
    """An n x n acquaintance matrix that counts every knows() query."""

    def __init__(self, matrix):
        self.m = matrix
        self.n = len(matrix)
        self.queries = 0

    def knows(self, a, b):
        self.queries += 1
        return self.m[a][b] == 1


def make_party(n, celebrity=None, rng=None):
    """Random acquaintance matrix. If celebrity is None, no celebrity exists."""
    rng = rng or random.Random(RNG_SEED)
    m = [[1 if rng.random() < 0.5 else 0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        m[i][i] = 0
    if celebrity is not None:
        for j in range(n):
            m[celebrity][j] = 0          # celebrity knows nobody
        for i in range(n):
            if i != celebrity:
                m[i][celebrity] = 1      # everybody knows the celebrity
    else:
        # guarantee no celebrity: every person either knows someone
        # or is unknown to someone
        for i in range(n):
            m[i][(i + 1) % n] = 1
    return m


def brute_force(party):
    """Exactly the pseudocode both decks show: the inner loop runs to the end.
    Always 2n(n-1) queries, regardless of the input."""
    n = party.n
    for i in range(n):
        ok = True
        for j in range(n):
            if i == j:
                continue
            if party.knows(i, j):
                ok = False
            if not party.knows(j, i):
                ok = False
        if ok:
            return i
    return -1


def brute_force_early(party):
    """Same idea, but abandons person i at the first failed check.
    Reported separately: it is much faster on random input."""
    n = party.n
    for i in range(n):
        ok = True
        for j in range(n):
            if i == j:
                continue
            if party.knows(i, j) or not party.knows(j, i):
                ok = False
                break
        if ok:
            return i
    return -1


def elimination(party):
    n = party.n
    i, j = 0, n - 1
    while i < j:                          # phase 1: n - 1 queries
        if party.knows(i, j):
            i += 1
        else:
            j -= 1
    cand = i
    for k in range(n):                    # phase 2: at most 2(n - 1)
        if k == cand:
            continue
        if party.knows(cand, k) or not party.knows(k, cand):
            return -1
    return cand


def time_celebrity(matrix, algo, repeats):
    """Median of `repeats` runs, in milliseconds. Matrix build is excluded."""
    times, result, queries = [], None, None
    for _ in range(repeats):
        party = Party(matrix)
        t0 = time.perf_counter()
        result = algo(party)
        times.append((time.perf_counter() - t0) * 1000.0)
        queries = party.queries
    return statistics.median(times), queries, result


def part_a():
    rng = random.Random(RNG_SEED)
    sizes = [100, 250, 500, 1000, 2000]
    rows = []
    for n in sizes:
        reps = REPEATS if n < 1000 else 3
        # Worst case for brute force: the celebrity is the last person checked,
        # so the outer loop runs all n times. Exactly 2n(n-1) queries.
        # Elimination's cost does not depend on where the celebrity sits.
        celeb = n - 1
        matrix = make_party(n, celebrity=celeb, rng=rng)

        bf_ms, bf_q, bf_r = time_celebrity(matrix, brute_force, reps)
        ee_ms, ee_q, ee_r = time_celebrity(matrix, brute_force_early, reps)
        el_ms, el_q, el_r = time_celebrity(matrix, elimination, reps)

        assert bf_r == celeb == el_r == ee_r, f"n={n}: {bf_r} {ee_r} {el_r} {celeb}"
        rows.append({
            "n": n,
            "brute_ms": round(bf_ms, 3),
            "brute_early_ms": round(ee_ms, 3),
            "elim_ms": round(el_ms, 3),
            "brute_queries": bf_q,
            "brute_early_queries": ee_q,
            "elim_queries": el_q,
            "speedup": round(bf_ms / el_ms, 1),
            "query_ratio": round(bf_q / el_q, 1),
        })

    # sanity: both agree that a party with no celebrity has none
    no_celeb = make_party(300, celebrity=None, rng=rng)
    checks = {
        "no_celebrity_brute": brute_force(Party(no_celeb)),
        "no_celebrity_elim": elimination(Party(no_celeb)),
    }
    return rows, checks


# ----------------------------------------------------------------------
# Part B — Coin Change
# ----------------------------------------------------------------------

def greedy_coins(coins, amount):
    """Largest coin that fits, repeatedly. Returns -1 if it gets stuck."""
    count, remaining = 0, amount
    for c in sorted(coins, reverse=True):
        while remaining >= c:
            remaining -= c
            count += 1
    return count if remaining == 0 else -1


def dp_coins(coins, amount):
    """Exact minimum number of coins. Returns -1 if impossible."""
    INF = amount + 1
    dp = [0] + [INF] * amount
    for v in range(1, amount + 1):
        best = INF
        for c in coins:
            if c <= v and dp[v - c] + 1 < best:
                best = dp[v - c] + 1
        dp[v] = best
    return -1 if dp[amount] >= INF else dp[amount]


def part_b(max_amount=200):
    coin_sets = [
        ("{1, 3, 4}", [1, 3, 4]),
        ("{1, 5, 6, 9}", [1, 5, 6, 9]),
        ("{1, 7, 10}", [1, 7, 10]),
        ("{1, 2, 5, 10}", [1, 2, 5, 10]),
        ("US {1, 5, 10, 25}", [1, 5, 10, 25]),
    ]
    rows = []
    for label, coins in coin_sets:
        feasible = optimal = 0
        excess, worst, worst_v = [], 0, None
        for v in range(1, max_amount + 1):
            g, d = greedy_coins(coins, v), dp_coins(coins, v)
            if d == -1:
                continue
            feasible += 1
            if g == d:
                optimal += 1
            else:
                gap = g - d
                excess.append(gap)
                if gap > worst:
                    worst, worst_v = gap, v
        rows.append({
            "coins": label,
            "targets_tested": feasible,
            "greedy_optimal": optimal,
            "greedy_pct": round(100.0 * optimal / feasible, 1),
            "dp_pct": 100.0,
            "mean_excess_when_wrong": round(statistics.mean(excess), 2) if excess else 0.0,
            "worst_excess": worst,
            "worst_target": worst_v,
        })
    return rows


# ----------------------------------------------------------------------

def main():
    print(f"Celebrity Problem — median of {REPEATS} runs\n")
    a_rows, a_checks = part_a()
    print(f"{'n':>6} {'brute ms':>10} {'elim ms':>9} {'speedup':>9} "
          f"{'brute Q':>12} {'elim Q':>8} {'Q ratio':>9} {'early ms':>10} {'early Q':>9}")
    for r in a_rows:
        print(f"{r['n']:>6} {r['brute_ms']:>10.2f} {r['elim_ms']:>9.3f} "
              f"{r['speedup']:>8.1f}x {r['brute_queries']:>12,} "
              f"{r['elim_queries']:>8,} {r['query_ratio']:>8.1f}x "
              f"{r['brute_early_ms']:>10.3f} {r['brute_early_queries']:>9,}")
    print(f"\nNo-celebrity check (both must be -1): "
          f"brute={a_checks['no_celebrity_brute']}, "
          f"elim={a_checks['no_celebrity_elim']}")

    print(f"\n\nCoin Change — greedy vs DP optimum, targets 1..200\n")
    b_rows = part_b()
    print(f"{'coin set':>20} {'tested':>8} {'greedy ok':>10} {'greedy %':>9} "
          f"{'dp %':>6} {'avg extra':>10} {'worst':>7}")
    for r in b_rows:
        worst = f"+{r['worst_excess']}@{r['worst_target']}" if r['worst_excess'] else "—"
        print(f"{r['coins']:>20} {r['targets_tested']:>8} {r['greedy_optimal']:>10} "
              f"{r['greedy_pct']:>8.1f}% {r['dp_pct']:>5.0f}% "
              f"{r['mean_excess_when_wrong']:>10.2f} {worst:>7}")

    out = {
        "seed": RNG_SEED,
        "repeats": REPEATS,
        "celebrity": a_rows,
        "celebrity_checks": a_checks,
        "coin_change": b_rows,
    }
    with open("results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nWritten: results.json")


if __name__ == "__main__":
    main()
