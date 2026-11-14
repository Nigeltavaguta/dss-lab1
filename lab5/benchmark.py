import csv
import time
from pathlib import Path

from datasets import random_graph, euclidean_points, dist_matrix, subset_sum_instance
from vertex_cover import approx_vertex_cover, min_vertex_cover_bb
from subset_sum import exact_subset_sum, fptas_subset_sum
from metric_tsp import tsp_held_karp, two_approx_tsp, tour_length


def bench_vertex_cover(out="output/vertex_cover.csv", sizes=range(4, 21), p=0.3, seed=7):
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "exact", "exact_nodes", "exact_s", "approx", "approx_s", "ratio"])
        for n in sizes:
            g = random_graph(n, p, seed + n)
            t0 = time.perf_counter()
            _, exact_size, nodes = min_vertex_cover_bb(g)
            t_exact = time.perf_counter() - t0

            t0 = time.perf_counter()
            _, approx_size = approx_vertex_cover(g)
            t_approx = time.perf_counter() - t0

            ratio = approx_size / exact_size if exact_size else 1.0
            w.writerow([n, exact_size, nodes, f"{t_exact:.6f}", approx_size, f"{t_approx:.6f}", round(ratio, 4)])
    return path


def bench_fptas(out="output/fptas.csv", n=40, seed=11, epsilons=(0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01)):
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    weights, target = subset_sum_instance(n, seed)
    exact = exact_subset_sum(weights, target)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["epsilon", "exact", "fptas", "ratio", "guarantee", "states", "seconds"])
        for eps in epsilons:
            t0 = time.perf_counter()
            approx = fptas_subset_sum(weights, target, eps)
            t = time.perf_counter() - t0
            ratio = approx / exact
            w.writerow([eps, exact, approx, round(ratio, 5), round(1 - eps, 5), "-", f"{t:.6f}"])
    return path


def bench_tsp(out="output/tsp.csv", sizes=range(4, 11), seed=13):
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "exact", "exact_s", "approx", "approx_s", "ratio"])
        for n in sizes:
            pts = euclidean_points(n, seed + n)
            d = dist_matrix(pts)

            t0 = time.perf_counter()
            _, exact_len = tsp_held_karp(d)
            t_exact = time.perf_counter() - t0

            t0 = time.perf_counter()
            _, approx_len = two_approx_tsp(d)
            t_approx = time.perf_counter() - t0

            ratio = approx_len / exact_len if exact_len else 1.0
            w.writerow([n, round(exact_len, 3), f"{t_exact:.6f}", round(approx_len, 3), f"{t_approx:.6f}", round(ratio, 4)])
    return path


if __name__ == "__main__":
    print(bench_vertex_cover())
    print(bench_fptas())
    print(bench_tsp())
