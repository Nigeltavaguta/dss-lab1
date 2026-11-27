"""Turn the CSV files in ../output into the figures used in the report."""

from __future__ import annotations

import csv
import math
import os
import statistics
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "output")

# Validated categorical palette (fixed order), light surface.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X"]
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
    "legend.frameon": False, "lines.linewidth": 2, "lines.markersize": 6,
})


def read(name):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=170)
    plt.close(fig)
    print(f"  wrote {name}")


def plot_pruning():
    rows = read("e1_pruning.csv")
    if not rows:
        return
    variants = ["naive", "fc", "fc+mrv", "fc+mrv+deg", "fc+mrv+deg+mac"]
    labels = {"naive": "Naive BT", "fc": "FC", "fc+mrv": "FC + MRV",
              "fc+mrv+deg": "FC + MRV + degree", "fc+mrv+deg+mac": "MAC + MRV + degree"}
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.6), sharex=True)
    for col, dataset in enumerate(("random", "uz")):
        for row, case in enumerate(("feasible k=opt", "refute k=opt-1")):
            ax = axes[row][col]
            for i, v in enumerate(variants):
                data = defaultdict(list)
                for r in rows:
                    if r["dataset"] == dataset and r["case"] == case and r["variant"] == v:
                        data[int(r["n"])].append(int(r["nodes"]))
                ns = sorted(data)
                ax.plot(ns, [max(1, statistics.median(data[n])) for n in ns],
                        color=SERIES[i], marker=MARKERS[i], label=labels[v])
            ax.set_yscale("log")
            title = "Random G(n, 0.3)" if dataset == "random" else "UZ-inspired"
            ax.set_title(f"{title}: {'find a timetable with k = optimum' if row == 0 else 'prove k = optimum - 1 impossible'}",
                         fontsize=8.5)
            if row == 1:
                ax.set_xlabel("exams n")
            if col == 0:
                ax.set_ylabel("median nodes (log)")
    axes[0][0].legend(loc="upper left", fontsize=7.5)
    save(fig, "e1_pruning.png")


def plot_scaling():
    rows = read("e2_scaling.csv")
    if not rows:
        return
    algs = ["greedy-LF", "greedy-DSATUR", "BT-FC-MRV-deg", "B&B", "hybrid"]
    labels = {"greedy-LF": "Greedy (Welsh-Powell)", "greedy-DSATUR": "Greedy (DSATUR)",
              "BT-FC-MRV-deg": "BT + FC + MRV + degree", "B&B": "Branch-and-bound",
              "hybrid": "Hybrid B&B + tabu"}
    for metric, ylabel, fname, log in (
            ("seconds", "mean time (s, log)", "e2_time.png", True),
            ("gap", "mean slots above lower bound", "e2_gap.png", False)):
        fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2), sharey=not log)
        for col, dataset in enumerate(("uz", "random")):
            ax = axes[col]
            for i, a in enumerate(algs):
                data = defaultdict(list)
                for r in rows:
                    if r["dataset"] == dataset and r["algorithm"] == a and r[metric] != "":
                        data[int(r["n"])].append(float(r[metric]))
                ns = sorted(data)
                if not ns:
                    continue
                means = [statistics.fmean(data[n]) for n in ns]
                if log:
                    means = [max(m, 1e-5) for m in means]
                ax.plot(ns, means, color=SERIES[i], marker=MARKERS[i], label=labels[a])
            if log:
                ax.set_yscale("log")
                ax.set_xscale("log")
            ax.set_title("UZ-inspired" if dataset == "uz" else "Random G(n, p)")
            ax.set_xlabel("exams n" + (" (log)" if log else ""))
            if col == 0:
                ax.set_ylabel(ylabel)
        axes[0].legend(fontsize=7, loc="upper left" if log else "upper left")
        save(fig, fname)


def plot_greedy():
    crown = read("e3_crown.csv")
    if crown:
        fig, ax = plt.subplots(figsize=(5.2, 3.0))
        ks = [int(r["k"]) for r in crown]
        for i, (key, label) in enumerate((("natural", "Greedy, interleaved order"),
                                          ("dsatur", "DSATUR"),
                                          ("chi", "Optimum χ = 2"))):
            ax.plot(ks, [int(r[key]) for r in crown], color=SERIES[i],
                    marker=MARKERS[i], markersize=4, label=label)
        ax.set_xlabel("crown graph size k (2k exams)")
        ax.set_ylabel("slots used")
        ax.legend(fontsize=8)
        save(fig, "e3_crown.png")
    ratio = read("e3_greedy_ratio.csv")
    if ratio:
        orders = ["natural", "random", "largest_first", "dsatur"]
        labels = ["Natural", "Random", "Welsh-Powell", "DSATUR"]
        ps = sorted({r["p"] for r in ratio}, key=float)
        fig, ax = plt.subplots(figsize=(5.6, 3.0))
        width = 0.2
        for i, o in enumerate(orders):
            means = []
            for p in ps:
                vals = [int(r[o]) / int(r["chi"]) for r in ratio if r["p"] == p]
                means.append(statistics.fmean(vals))
            xs = [j + (i - 1.5) * width for j in range(len(ps))]
            ax.bar(xs, means, width * 0.9, color=SERIES[i], label=labels[i])
        ax.axhline(1, color=INK2, linewidth=1, linestyle="--")
        ax.set_xticks(range(len(ps)))
        ax.set_xticklabels([f"p = {p}" for p in ps])
        ax.set_ylabel("mean slots / χ")
        ax.set_ylim(0.9, None)
        ax.legend(fontsize=7.5, ncol=4, loc="upper left")
        save(fig, "e3_ratio.png")


def plot_bnb():
    rows = read("e4_bnb_ablation.csv")
    if not rows:
        return
    configs = ["LB + greedy UB", "greedy UB only", "LB only", "neither"]
    cases = []
    for r in rows:
        key = (r["dataset"], r["n"], r["p"])
        if key not in cases:
            cases.append(key)
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    width = 0.2
    for i, c in enumerate(configs):
        vals = []
        for d, n, p in cases:
            nodes = [max(1, int(r["nodes"])) for r in rows if r["config"] == c and
                     (r["dataset"], r["n"], r["p"]) == (d, n, p)]
            vals.append(math.exp(statistics.fmean(math.log(x) for x in nodes)))
        xs = [j + (i - 1.5) * width for j in range(len(cases))]
        ax.bar(xs, vals, width * 0.9, color=SERIES[i], label=c)
    ax.set_yscale("log")
    ax.set_xticks(range(len(cases)))
    ax.set_xticklabels([f"{'Rand' if d == 'random' else 'UZ'} n={n}" + (f"\np={p}" if p else "")
                        for d, n, p in cases], fontsize=8)
    ax.set_ylabel("geometric mean nodes (log)")
    ax.legend(fontsize=7.5, ncol=4, loc="upper left")
    save(fig, "e4_bnb.png")


def plot_trace():
    rows = read("e5_trace.csv")
    if not rows:
        return
    instances = []
    for r in rows:
        if r["instance"] not in instances:
            instances.append(r["instance"])
    solvers = ["hybrid", "B&B", "DSATUR + tabu"]
    labels = {"hybrid": "Hybrid", "B&B": "B&B alone", "DSATUR + tabu": "DSATUR + tabu only"}
    fig, axes = plt.subplots(1, len(instances), figsize=(7.4, 3.0))
    for ax, inst in zip(axes, instances):
        sel = [r for r in rows if r["instance"] == inst]
        tmax = 20.0
        lb = int(sel[0]["lower_bound"])
        top = max(int(r["slots"]) for r in sel)
        for i, s in enumerate(solvers):
            pts = [(float(r["time"]), int(r["slots"])) for r in sel if r["solver"] == s]
            if not pts:
                continue
            xs = [max(p[0], 0.01) for p in pts] + [tmax]
            ys = [p[1] for p in pts] + [pts[-1][1]]
            ax.step(xs, ys, where="post", color=SERIES[i], label=labels[s],
                    linewidth=2.4 if s == "hybrid" else 1.8)
        ax.axhline(lb, color=INK2, linestyle="--", linewidth=1)
        ax.text(0.012, lb + 0.2, f"LB = {lb}", fontsize=7, color=INK2)
        ax.set_xscale("log")
        ax.set_xlim(0.01, tmax)
        ax.set_xticks([0.01, 0.1, 1, 10])
        ax.set_xticklabels(["0.01", "0.1", "1", "10"])
        ax.minorticks_off()
        ax.set_ylim(lb - 0.8, top + 0.8)
        ax.set_title(inst, fontsize=8.5)
        ax.set_xlabel("time (s, log)")
    axes[0].set_ylabel("best timetable length")
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(OUT, "e5_trace.png"), dpi=170)
    plt.close(fig)
    print("  wrote e5_trace.png")

def plot_architecture():
    """Five-layer architecture of the engine (Section 5.1)."""
    from matplotlib.patches import FancyBboxPatch
    layers = [
        ("Input", "exams, venues, lecturers, student groups, horizon T"),
        ("Modelling", "conflict graph (C1, C2) · domains (C4) · sorted venue capacities (C3)"),
        ("Bounds", "clique bound · venue bound  →  LB"),
        ("Solver layer", "naive BT · BT+FC+MRV+degree(+MAC) · B&B · greedy · hybrid"),
        ("Evaluation", "independent validator · nodes · time · gap · statistics"),
        ("Output", "conflict-free timetable with day, session and venue"),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(layers) * 1.25)
    ax.axis("off")
    ax.grid(False)
    for i, (name, desc) in enumerate(layers):
        y = (len(layers) - 1 - i) * 1.25 + 0.15
        box = FancyBboxPatch((0.3, y), 9.4, 0.85, boxstyle="round,pad=0.02,rounding_size=0.12",
                             linewidth=1.2, edgecolor=SERIES[0],
                             facecolor="#e8f1fc" if name != "Solver layer" else "#fde9df")
        ax.add_patch(box)
        ax.text(0.55, y + 0.43, name, fontsize=9.5, fontweight="bold", va="center", color=INK)
        ax.text(2.6, y + 0.43, desc, fontsize=8.3, va="center", color=INK2)
        if i < len(layers) - 1:
            ax.annotate("", xy=(5, y - 0.37), xytext=(5, y + 0.02),
                        arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
    save(fig, "architecture.png")


def plot_conflict_graph():
    """A 24-exam UZ-inspired conflict graph coloured by the hybrid's sessions."""
    import random
    import sys
    sys.path.insert(0, os.path.dirname(HERE))
    from ete.generators import uz_instance
    from ete.hybrid import hybrid
    inst = uz_instance(24, 3)
    res = hybrid(inst, time_limit=5)
    n = inst.n
    rng = random.Random(1)
    pos = [[math.cos(2 * math.pi * i / n) * 3, math.sin(2 * math.pi * i / n) * 3] for i in range(n)]
    for _ in range(400):  # simple force-directed layout
        disp = [[0.0, 0.0] for _ in range(n)]
        for a in range(n):
            for b in range(n):
                if a == b:
                    continue
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                d = math.hypot(dx, dy) + 1e-3
                f = 0.5 / d ** 2 - (0.08 * d if b in inst.adj[a] else 0)
                disp[a][0] += dx / d * f
                disp[a][1] += dy / d * f
        for a in range(n):
            pos[a][0] += max(-0.2, min(0.2, disp[a][0]))
            pos[a][1] += max(-0.2, min(0.2, disp[a][1]))
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.axis("off")
    ax.grid(False)
    for a in range(n):
        for b in inst.adj[a]:
            if a < b:
                ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                        color="#b9b8b2", linewidth=0.8, zorder=1)
    k = res.slots
    for t in range(k):
        xs = [pos[e][0] for e in range(n) if res.assignment[e] == t]
        ys = [pos[e][1] for e in range(n) if res.assignment[e] == t]
        ax.scatter(xs, ys, s=230, color=SERIES[t % len(SERIES)], edgecolor=SURFACE,
                   linewidth=2, zorder=2, label=f"Session {t + 1}")
    for e in range(n):
        ax.text(pos[e][0], pos[e][1] - 0.42, inst.exams[e].code, fontsize=6,
                ha="center", va="top", color=INK2)
    ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.0, 0.5))
    ax.set_title(f"UZ-inspired instance: {n} exams, {inst.num_edges} conflicts, "
                 f"{k} sessions (LB = {res.lower_bound})", fontsize=9)
    save(fig, "conflict_graph.png")


def plot_calendar():
    """Seat utilisation per session of the 500-exam timetable (E7)."""
    rows = read("e7_timetable.csv")
    if not rows:
        return
    days = max(int(r["day"]) for r in rows)
    sessions = ["09:00", "14:00"]
    seats_total = None
    summary = read("e7_summary.csv")
    util = [[0.0] * days for _ in sessions]
    count = [[0] * days for _ in sessions]
    for r in rows:
        i = sessions.index(r["session"])
        j = int(r["day"]) - 1
        util[i][j] += int(r["students"])
        count[i][j] += 1
    caps = {}
    for r in rows:
        caps[r["venue"]] = int(r["capacity"])
    seats_total = sum(caps.values())
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#eef4fc", "#86b6ef", "#2a78d6", "#184f95"])
    fig, ax = plt.subplots(figsize=(6.4, 2.2))
    ax.grid(False)
    data = [[u / seats_total for u in row] for row in util]
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(sessions)):
        for j in range(days):
            if count[i][j]:
                ax.text(j, i, f"{count[i][j]}", ha="center", va="center", fontsize=8,
                        color="white" if data[i][j] > 0.55 else INK)
    ax.set_yticks(range(len(sessions)))
    ax.set_yticklabels(sessions)
    ax.set_xticks(range(days))
    ax.set_xticklabels([f"D{d + 1}" for d in range(days)], fontsize=8)
    ax.set_title("500-exam timetable: exams per session (number) and share of seats used (shade)",
                 fontsize=8.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.ax.tick_params(labelsize=7)
    save(fig, "timetable_calendar.png")


def main():
    plot_pruning()
    plot_scaling()
    plot_greedy()
    plot_bnb()
    plot_trace()
    plot_architecture()
    plot_conflict_graph()
    plot_calendar()


if __name__ == "__main__":
    main()
