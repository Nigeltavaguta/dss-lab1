# Runs all three problems across a range of sizes, checks the algorithms
# agree where they should, and writes CSVs to output/.
import csv
import time
from pathlib import Path

from datasets import knapsack_instance, tsp_instance, CANONICAL_COINS, NON_CANONICAL_COINS
from knapsack import knapsack_2d, knapsack_1d, knapsack_branch_and_bound, fractional_knapsack_greedy
from coin_change import coin_change_dp, coin_change_greedy, coin_change_bfs
from tsp import tsp_held_karp, tsp_nearest_neighbor, tsp_two_opt, tour_length


def bench_knapsack(out="output/knapsack.csv", sizes=(10, 14, 18, 20, 22), seed=1):
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "dp2d_value", "dp1d_value", "bb_value", "bb_nodes",
                    "frac_greedy_value", "dp2d_s", "dp1d_s", "bb_s", "agree"])
        for n in sizes:
            values, weights, capacity = knapsack_instance(n, seed)

            t0 = time.perf_counter(); v2d = knapsack_2d(values, weights, capacity); t_2d = time.perf_counter() - t0
            t0 = time.perf_counter(); v1d = knapsack_1d(values, weights, capacity); t_1d = time.perf_counter() - t0
            t0 = time.perf_counter(); vbb, nodes = knapsack_branch_and_bound(values, weights, capacity); t_bb = time.perf_counter() - t0
            vfrac = fractional_knapsack_greedy(values, weights, capacity)

            agree = (v2d == v1d == vbb)
            w.writerow([n, v2d, v1d, vbb, nodes, round(vfrac, 2),
                        f"{t_2d:.6f}", f"{t_1d:.6f}", f"{t_bb:.6f}", agree])
    return path


def bench_coin_change(out="output/coin_change.csv", amounts=range(1, 201, 5)):
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["coin_system", "amount", "dp_count", "greedy_count", "bfs_count", "greedy_optimal"])
        for label, coins in (("canonical", CANONICAL_COINS), ("non_canonical", NON_CANONICAL_COINS)):
            for amount in amounts:
                dp_c = coin_change_dp(coins, amount)
                greedy_c = coin_change_greedy(coins, amount)
                bfs_c = coin_change_bfs(coins, amount)
                w.writerow([label, amount, dp_c, greedy_c, bfs_c, dp_c == greedy_c])
    return path


def bench_tsp(out="output/tsp.csv", exact_sizes=range(4, 13), approx_sizes=(20, 50, 100), seed=7):
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "optimal", "nn_length", "two_opt_length",
                    "nn_ratio", "two_opt_ratio", "log2n_plus_1_bound"])
        import math
        for n in exact_sizes:
            _, dist = tsp_instance(n, seed)
            opt, _ = tsp_held_karp(dist)
            _, nn_len = tsp_nearest_neighbor(dist)
            _, two_opt_len = tsp_two_opt(dist, tsp_nearest_neighbor(dist)[0])
            bound = math.log2(n) + 1 if n > 1 else 1
            w.writerow([n, round(opt, 3), round(nn_len, 3), round(two_opt_len, 3),
                        round(nn_len / opt, 4) if opt else "", round(two_opt_len / opt, 4) if opt else "",
                        round(bound, 4)])
        for n in approx_sizes:
            _, dist = tsp_instance(n, seed)
            _, nn_len = tsp_nearest_neighbor(dist)
            _, two_opt_len = tsp_two_opt(dist, tsp_nearest_neighbor(dist)[0])
            w.writerow([n, "", round(nn_len, 3), round(two_opt_len, 3), "", "", ""])
    return path


if __name__ == "__main__":
    print(bench_knapsack())
    print(bench_coin_change())
    print(bench_tsp())
