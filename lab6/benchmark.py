"""Generate the CSV tables used in the Lab 6 report."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from randomized import (karger_trials_for_failure, miller_rabin, planted_cut_graph,
                        randomized_quicksort, repeat_karger)
from simulation import (estimate_pi, five_d_integral, mm1_simulation,
                        midpoint_5d, rare_event_loss, variance_reduction)

OUT = Path("output")


def write_csv(name, rows):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return path


def run_all():
    # Randomized Quicksort: average over independent pivot seeds.
    rows = []
    for n in (100, 250, 500, 1000, 2000):
        data = list(range(n))
        total = 0
        repetitions = 20
        for seed in range(repetitions):
            _, count = randomized_quicksort(data, seed)
            total += count
        harmonic = sum(1 / k for k in range(1, n + 1))
        # Expected key comparisons for randomized Quicksort on distinct keys.
        theory = 2 * (n + 1) * harmonic - 4 * n
        rows.append({"n": n, "repetitions": repetitions, "mean_comparisons": total / repetitions,
                     "expected_comparisons": theory})
    write_csv("quicksort.csv", rows)

    # Miller-Rabin tests on known primes and composites.
    cases = [(1000003, True), (1000033, True), (999983, True),
             (1000005, False), (561, False), (1105, False), (3215031751, False)]
    rows = []
    for n, expected in cases:
        for rounds in (1, 2, 5, 10, 20):
            predicted = miller_rabin(n, rounds, seed=42)
            rows.append({"n": n, "known_prime": expected, "rounds": rounds,
                         "reported_prime": predicted, "correct": predicted == expected,
                         "worst_case_false_prime_bound": 4 ** (-rounds)})
    write_csv("miller_rabin.csv", rows)

    # Karger success rate on a graph whose minimum cut is exactly three.
    edges, exact_cut = planted_cut_graph(n=10, cut_size=3)
    best, cuts = repeat_karger(10, edges, trials=5000, seed=900)
    rows = [{"n": 10, "exact_min_cut": exact_cut, "trials": len(cuts),
             "successful_trials": sum(c == exact_cut for c in cuts),
             "observed_success_rate": sum(c == exact_cut for c in cuts) / len(cuts),
             "single_trial_lower_bound": 2 / (10 * 9),
             "trials_for_99pct_bound": karger_trials_for_failure(10, 0.01), "best_cut": best}]
    write_csv("karger.csv", rows)

    # Pi estimates and Wilson intervals.
    rows = [estimate_pi(n, seed=2026) for n in (1000, 5000, 20000, 100000, 500000)]
    write_csv("pi_convergence.csv", rows)

    # Queueing model, with analytical M/M/1 reference values.
    rows = [mm1_simulation(lam=0.8, mu=1.0, customers=n, seed=1406)
            for n in (10000, 50000, 200000)]
    write_csv("mm1_queue.csv", rows)

    # Stylized one-period net loss in millions of dollars. A $1m loss is four
    # standard deviations above the $0.4m mean. Shift sampling to $1.075m.
    rare = rare_event_loss(samples=500000, mu=0.4, sigma=0.15,
                           threshold=1.0, shift=1.075, seed=601)
    rare["analytical_probability"] = 0.5 * math.erfc(4 / math.sqrt(2))
    write_csv("rare_event.csv", [rare])

    # Variance reduction on integral exp(u) du.
    write_csv("variance_reduction.csv", [variance_reduction(samples=100000, seed=603)])

    # MC versus tensor midpoint quadrature for an exactly known 5-D integral.
    exact = (math.e - 1) ** 5
    mc = five_d_integral(samples=100000, seed=605)
    rows = []
    for m in (2, 4, 6, 8, 10, 12):
        estimate = midpoint_5d(m)
        rows.append({"method": "tensor_midpoint", "work_parameter": m, "function_evaluations": m ** 5,
                     "estimate": estimate, "absolute_error": abs(estimate - exact),
                     "ci_low": "", "ci_high": ""})
    rows.append({"method": "Monte_Carlo", "work_parameter": mc["samples"],
                 "function_evaluations": mc["samples"], "estimate": mc["mc_estimate"],
                 "absolute_error": mc["mc_abs_error"], "ci_low": mc["mc_ci_low"],
                 "ci_high": mc["mc_ci_high"]})
    write_csv("integral_5d.csv", rows)

    print("Wrote randomized algorithm and Monte Carlo benchmark CSVs to output/")


if __name__ == "__main__":
    run_all()
