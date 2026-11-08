# Runs the pruning comparison, the exact-vs-greedy comparison, and the
# greedy adversarial-order demo, writing CSVs to output/.
import csv
import time
from pathlib import Path

from datasets import random_graph, timetabling_instance, crown_graph
from graph_coloring import (
    naive_backtracking, backtracking_fc_mrv, branch_and_bound_chromatic,
    greedy_coloring, greedy_clique_lower_bound,
)


def bench_pruning(out="output/pruning.csv", sizes=(8, 10, 12, 14, 16, 18), p=0.4, seed=1):
    # Same decision problem (is this graph k-colorable, k fixed just above
    # the clique lower bound so it's a genuinely hard instance), naive
    # search vs forward-checking+MRV, same vertex/edge set both times.
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "k", "naive_nodes", "fcmrv_nodes", "reduction_factor", "naive_s", "fcmrv_s"])
        for n in sizes:
            g = random_graph(n, p, seed)
            lb = max(2, greedy_clique_lower_bound(g))
            k = lb  # tightest k we expect might still be feasible - hardest case

            t0 = time.perf_counter()
            _, naive_nodes = naive_backtracking(g, k)
            t_naive = time.perf_counter() - t0

            t0 = time.perf_counter()
            _, fcmrv_nodes = backtracking_fc_mrv(g, k)
            t_fcmrv = time.perf_counter() - t0

            reduction = naive_nodes / fcmrv_nodes if fcmrv_nodes else float("inf")
            w.writerow([n, k, naive_nodes, fcmrv_nodes, round(reduction, 2),
                        f"{t_naive:.6f}", f"{t_fcmrv:.6f}"])
    return path


def bench_exact_vs_greedy(out="output/exact_vs_greedy.csv", sizes=(6, 8, 10, 12, 14, 16, 18, 20), p=0.35, seed=2):
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "bb_colors", "bb_nodes", "bb_s", "greedy_colors", "greedy_s", "gap"])
        for n in sizes:
            g = random_graph(n, p, seed)

            t0 = time.perf_counter()
            bb_k, _, bb_nodes = branch_and_bound_chromatic(g)
            t_bb = time.perf_counter() - t0

            t0 = time.perf_counter()
            _, greedy_k = greedy_coloring(g)
            t_greedy = time.perf_counter() - t0

            w.writerow([n, bb_k, bb_nodes, f"{t_bb:.6f}", greedy_k, f"{t_greedy:.6f}", greedy_k - bb_k])
    return path


def bench_timetabling(out="output/timetabling.csv", seed=3):
    # Real-world-inspired: exams conflict because students share them,
    # not uniform-random edges. Several sizes of this specific structure.
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    configs = [
        (10, 30, 3), (14, 40, 3), (18, 50, 3), (22, 60, 3), (26, 70, 3),
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["num_exams", "num_students", "exams_per_student", "bb_colors", "bb_nodes", "bb_s", "greedy_colors", "greedy_s"])
        for num_exams, num_students, epp in configs:
            g = timetabling_instance(num_exams, num_students, epp, seed)

            t0 = time.perf_counter()
            bb_k, _, bb_nodes = branch_and_bound_chromatic(g)
            t_bb = time.perf_counter() - t0

            t0 = time.perf_counter()
            _, greedy_k = greedy_coloring(g)
            t_greedy = time.perf_counter() - t0

            w.writerow([num_exams, num_students, epp, bb_k, bb_nodes, f"{t_bb:.6f}", greedy_k, f"{t_greedy:.6f}"])
    return path


def bench_worst_case(out="output/worst_case.csv", sizes=(20, 22, 24, 26, 28, 30, 32, 35), p=0.5, seed=5):
    # Dense random graphs where the greedy clique lower bound does not
    # match the true chromatic number, forcing B&B to actually search
    # several k values instead of confirming the first one it tries.
    # Node counts here show genuine exponential growth - the practical
    # ceiling for exact search, as opposed to the pruning benchmark above
    # (same algorithm, easier instances) or the timetabling instances
    # (structured, usually easy for this clique bound).
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "lower_bound", "chi", "nodes", "seconds"])
        for n in sizes:
            g = random_graph(n, p, seed)
            lb = greedy_clique_lower_bound(g)
            t0 = time.perf_counter()
            k, _, nodes = branch_and_bound_chromatic(g)
            t = time.perf_counter() - t0
            w.writerow([n, lb, k, nodes, f"{t:.4f}"])
    return path


def bench_greedy_order(out="output/greedy_order.csv", sizes=(2, 4, 6, 8, 10, 15, 20, 30)):
    # The crown-graph adversarial-order demo: same graph (chi=2 always),
    # two different vertex orders fed to the same greedy routine.
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "chi", "interleaved_order_colors", "grouped_order_colors"])
        for n in sizes:
            g = crown_graph(n)
            interleaved = list(range(2 * n))
            grouped = [2 * i for i in range(n)] + [2 * i + 1 for i in range(n)]
            _, k_bad = greedy_coloring(g, order=interleaved)
            _, k_good = greedy_coloring(g, order=grouped)
            w.writerow([n, 2, k_bad, k_good])
    return path


if __name__ == "__main__":
    print(bench_pruning())
    print(bench_exact_vs_greedy())
    print(bench_timetabling())
    print(bench_worst_case())
    print(bench_greedy_order())
