"""Create the Lab 6 convergence and comparison figures."""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUT = Path("output")


def read_csv(name):
    with (OUT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def make_plots():
    OUT.mkdir(exist_ok=True)
    q = read_csv("quicksort.csv")
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot([int(r["n"]) for r in q], [float(r["mean_comparisons"]) for r in q], "o-", label="Measured mean")
    ax.plot([int(r["n"]) for r in q], [float(r["expected_comparisons"]) for r in q], "--", label="Expected comparisons")
    ax.set(xlabel="Input size n", ylabel="Key comparisons", title="Randomized Quicksort comparisons")
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT / "quicksort.png", dpi=170); plt.close(fig)

    k = read_csv("karger.csv")[0]
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.bar(["Observed", "Theoretical lower bound"],
           [float(k["observed_success_rate"]), float(k["single_trial_lower_bound"])],
           color=["#4c78a8", "#f58518"])
    ax.set(ylabel="Probability of finding minimum cut", title="Karger one-trial success on the test graph", ylim=(0, 0.2))
    ax.grid(axis="y", alpha=.25); fig.tight_layout(); fig.savefig(OUT / "karger.png", dpi=170); plt.close(fig)

    p = read_csv("pi_convergence.csv")
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ns = [int(r["samples"]) for r in p]
    estimates = [float(r["estimate"]) for r in p]
    low = [float(r["ci_low"]) for r in p]
    high = [float(r["ci_high"]) for r in p]
    ax.errorbar(ns, estimates, yerr=[[e-l for e,l in zip(estimates,low)], [h-e for h,e in zip(high,estimates)]], fmt="o-", capsize=3)
    ax.axhline(3.141592653589793, color="black", linestyle="--", label="π")
    ax.set_xscale("log"); ax.set(xlabel="Uniform samples (log scale)", ylabel="Estimate", title="Monte Carlo estimate of π with 95% Wilson intervals")
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT / "pi_convergence.png", dpi=170); plt.close(fig)

    d = read_csv("integral_5d.csv")
    det = [r for r in d if r["method"] == "tensor_midpoint"]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.loglog([int(r["function_evaluations"]) for r in det], [float(r["absolute_error"]) for r in det], "o-", label="Tensor midpoint")
    mc = next(r for r in d if r["method"] == "Monte_Carlo")
    ax.scatter([int(mc["function_evaluations"])], [float(mc["absolute_error"])], marker="*", s=130, label="Monte Carlo")
    ax.set(xlabel="Function evaluations", ylabel="Absolute error", title="Five-dimensional integration cost")
    ax.grid(which="both", alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT / "integral_5d.png", dpi=170); plt.close(fig)

    v = read_csv("variance_reduction.csv")[0]
    names = ["Plain MC", "Antithetic", "Control variate"]
    factors = [1.0, float(v["antithetic_reduction"]), float(v["control_reduction"])]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.bar(names, factors, color=["#777777", "#4c78a8", "#f58518"])
    ax.set(ylabel="Variance reduction factor", title="Variance reduction for ∫₀¹ exp(u) du")
    ax.grid(axis="y", alpha=.25); fig.tight_layout(); fig.savefig(OUT / "variance_reduction.png", dpi=170); plt.close(fig)

    r = read_csv("rare_event.csv")[0]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    methods = ["Crude MC", "Importance sampling", "Exact normal tail"]
    est = [float(r["crude_estimate"]), float(r["is_estimate"]), float(r["analytical_probability"])]
    low = [float(r["crude_ci_low"]), float(r["is_ci_low"]), est[2]]
    high = [float(r["crude_ci_high"]), float(r["is_ci_high"]), est[2]]
    ax.errorbar(methods, est, yerr=[[e-l for e,l in zip(est,low)], [h-e for h,e in zip(high,est)]], fmt="o", capsize=4)
    ax.set_yscale("log"); ax.set(ylabel="Estimated event probability (log scale)", title="Probability of net loss above $1 million")
    ax.grid(axis="y", which="both", alpha=.25); fig.tight_layout(); fig.savefig(OUT / "rare_event.png", dpi=170); plt.close(fig)


if __name__ == "__main__":
    make_plots()
