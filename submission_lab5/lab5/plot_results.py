# Reads the CSVs benchmark.py produces and makes the plots the report uses.
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_vertex_cover(path="output/vertex_cover.csv", out="output/vertex_cover_ratio.png"):
    ns, exact, approx, ratio = [], [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n"]))
            exact.append(int(row["exact"]))
            approx.append(int(row["approx"]))
            ratio.append(float(row["ratio"]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    ax1.plot(ns, exact, "o-", label="exact (branch and bound)")
    ax1.plot(ns, approx, "o-", label="2-approximation (matching)")
    ax1.set_xlabel("n (vertices)")
    ax1.set_ylabel("cover size")
    ax1.set_title("Vertex cover size: exact vs. approximate")
    ax1.legend()

    ax2.plot(ns, ratio, "o-", color="tab:red")
    ax2.axhline(2.0, color="gray", linewidth=0.8, linestyle="--", label="worst-case bound (2)")
    ax2.set_xlabel("n (vertices)")
    ax2.set_ylabel("approx / exact")
    ax2.set_title("Vertex cover approximation ratio vs. n")
    ax2.set_ylim(0.9, 2.1)
    ax2.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_fptas(path="output/fptas.csv", out="output/fptas_tradeoff.png"):
    eps, ratio, guarantee, secs = [], [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            eps.append(float(row["epsilon"]))
            ratio.append(float(row["ratio"]))
            guarantee.append(float(row["guarantee"]))
            secs.append(float(row["seconds"]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    ax1.plot(eps, ratio, "o-", label="achieved ratio (fptas / exact)")
    ax1.plot(eps, guarantee, "--", color="gray", label="guaranteed floor (1 - epsilon)")
    ax1.set_xlabel("epsilon")
    ax1.set_ylabel("ratio to optimal")
    ax1.set_title("FPTAS accuracy vs. epsilon")
    ax1.invert_xaxis()
    ax1.legend()

    ax2.plot(eps, secs, "o-", color="tab:orange")
    ax2.set_xlabel("epsilon")
    ax2.set_ylabel("time (s)")
    ax2.set_yscale("log")
    ax2.invert_xaxis()
    ax2.set_title("FPTAS runtime vs. epsilon (tighter epsilon costs more)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def plot_tsp(path="output/tsp.csv", out="output/tsp_ratio.png"):
    ns, ratio = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n"]))
            ratio.append(float(row["ratio"]))

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(ns, ratio, "o-", color="tab:green")
    ax.axhline(2.0, color="gray", linewidth=0.8, linestyle="--", label="worst-case bound (2)")
    ax.set_xlabel("n (cities)")
    ax.set_ylabel("approx tour / exact tour")
    ax.set_title("Metric TSP 2-approximation ratio vs. n")
    ax.set_ylim(0.9, 2.1)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    plot_vertex_cover()
    plot_fptas()
    plot_tsp()
