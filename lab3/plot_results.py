# Reads the CSVs benchmark.py produces and makes the plots the report uses.
import csv
import matplotlib
matplotlib.use("Agg")  # write straight to file, no display needed/assumed
import matplotlib.pyplot as plt


def plot_knapsack(path="output/knapsack.csv", out="output/knapsack_time.png"):
    ns, t2d, t1d, tbb = [], [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n"]))
            t2d.append(float(row["dp2d_s"]))
            t1d.append(float(row["dp1d_s"]))
            tbb.append(float(row["bb_s"]))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(ns, t2d, "o-", label="2D DP")
    ax.plot(ns, t1d, "o-", label="1D DP")
    ax.plot(ns, tbb, "o-", label="Branch and bound")
    ax.set_xlabel("n (items)")
    ax.set_ylabel("time (s)")
    ax.set_title("0-1 knapsack: runtime by method")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_coin_change(path="output/coin_change.csv", out="output/coin_change_gap.png"):
    data = {"canonical": ([], []), "non_canonical": ([], [])}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sysname = row["coin_system"]
            gap = int(row["greedy_count"]) - int(row["dp_count"])
            data[sysname][0].append(int(row["amount"]))
            data[sysname][1].append(gap)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for label, (xs, ys) in data.items():
        ax.plot(xs, ys, "o-", label=label, markersize=3)
    ax.set_xlabel("amount")
    ax.set_ylabel("greedy coins - optimal coins")
    ax.set_title("Coin change: how far greedy drifts from optimal")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_tsp(path="output/tsp.csv", out="output/tsp_ratios.png"):
    ns, nn_ratio, two_opt_ratio, bound = [], [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["optimal"] == "":
                continue
            ns.append(int(row["n"]))
            nn_ratio.append(float(row["nn_ratio"]))
            two_opt_ratio.append(float(row["two_opt_ratio"]))
            bound.append(float(row["log2n_plus_1_bound"]))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(ns, nn_ratio, "o-", label="nearest-neighbor / optimal")
    ax.plot(ns, two_opt_ratio, "o-", label="2-opt / optimal")
    ax.plot(ns, bound, "--", label="log2(n) + 1 bound")
    ax.axhline(1.0, color="gray", linewidth=0.8)
    ax.set_xlabel("n (cities)")
    ax.set_ylabel("tour length / optimal")
    ax.set_title("TSP heuristics vs. Held-Karp optimal")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    plot_knapsack()
    plot_coin_change()
    plot_tsp()
