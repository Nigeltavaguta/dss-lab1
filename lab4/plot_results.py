# Reads the CSVs benchmark.py produces and makes the plots the report uses.
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_pruning(path="output/pruning.csv", out="output/pruning.png"):
    ns, naive, fcmrv = [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n"]))
            naive.append(int(row["naive_nodes"]))
            fcmrv.append(int(row["fcmrv_nodes"]))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(ns, naive, "o-", label="naive backtracking")
    ax.plot(ns, fcmrv, "o-", label="forward checking + MRV")
    ax.set_yscale("log")
    ax.set_xlabel("n (vertices)")
    ax.set_ylabel("nodes explored")
    ax.set_title("Pruning: nodes explored to decide k-colorability")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_exact_vs_greedy(path="output/exact_vs_greedy.csv", out="output/exact_vs_greedy.png"):
    ns, bb, greedy = [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n"]))
            bb.append(int(row["bb_colors"]))
            greedy.append(int(row["greedy_colors"]))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(ns, bb, "o-", label="branch and bound (exact)")
    ax.plot(ns, greedy, "o-", label="greedy (Welsh-Powell)")
    ax.set_xlabel("n (vertices)")
    ax.set_ylabel("colors used")
    ax.set_title("Solution quality: exact vs. greedy")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_quality_vs_time(path="output/exact_vs_greedy.csv", out="output/quality_vs_time.png"):
    exact_time, exact_colors, greedy_time, greedy_colors = [], [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            exact_time.append(float(row["bb_s"]))
            exact_colors.append(int(row["bb_colors"]))
            greedy_time.append(float(row["greedy_s"]))
            greedy_colors.append(int(row["greedy_colors"]))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.scatter(exact_time, exact_colors, label="branch and bound (exact)", marker="o")
    ax.scatter(greedy_time, greedy_colors, label="greedy (Welsh-Powell)", marker="s")
    ax.set_xscale("log")
    ax.set_xlabel("runtime (seconds, log scale)")
    ax.set_ylabel("colors used (lower is better)")
    ax.set_title("Coloring quality vs. runtime")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_worst_case(path="output/worst_case.csv", out="output/worst_case.png"):
    ns, nodes, secs = [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n"]))
            nodes.append(int(row["nodes"]))
            secs.append(float(row["seconds"]))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    ax1.plot(ns, nodes, "o-", color="tab:red")
    ax1.set_yscale("log")
    ax1.set_xlabel("n (vertices)")
    ax1.set_ylabel("nodes explored")
    ax1.set_title("B&B nodes on dense random graphs (p=0.5)")
    ax2.plot(ns, secs, "o-", color="tab:red")
    ax2.set_yscale("log")
    ax2.set_xlabel("n (vertices)")
    ax2.set_ylabel("time (s)")
    ax2.set_title("B&B wall-clock time")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_greedy_order(path="output/greedy_order.csv", out="output/greedy_order.png"):
    ns, bad, good = [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n"]))
            bad.append(int(row["interleaved_order_colors"]))
            good.append(int(row["grouped_order_colors"]))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(ns, bad, "o-", label="adversarial (interleaved) order")
    ax.plot(ns, good, "o-", label="grouped order")
    ax.axhline(2, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("n (crown graph half-size)")
    ax.set_ylabel("colors used by greedy")
    ax.set_title("Greedy coloring: order determines quality, chi = 2 always")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    plot_pruning()
    plot_exact_vs_greedy()
    plot_quality_vs_time()
    plot_worst_case()
    plot_greedy_order()
