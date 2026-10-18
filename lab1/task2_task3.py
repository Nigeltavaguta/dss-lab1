import csv
import math
import os

N_MIN_EXP = 1
N_MAX_EXP = 20
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def simulate(n, a, b, f, memo):
    # T(n) = a*T(n/b) + f(n), T(1) = 1
    if n <= 1:
        return 1
    if n in memo:
        return memo[n]
    ops_here = f(n)
    sub = simulate(n // b, a, b, f, memo)
    total = ops_here + a * sub
    memo[n] = total
    return total


def log2_floor_safe(n):
    return int(math.log2(n)) if n > 1 else 0


RECURRENCES = {
    1: dict(a=2, b=2, f=lambda n: n),
    2: dict(a=2, b=2, f=lambda n: n * n),
    3: dict(a=4, b=2, f=lambda n: n),
    4: dict(a=1, b=2, f=lambda n: log2_floor_safe(n)),
}


# closed forms from Task 1
def theory_1(n):
    k = math.log2(n)
    return n * k + n


def theory_2(n):
    return 2 * n * n - n


def theory_3(n):
    return 2 * n * n - n


def theory_4(n):
    k = math.log2(n)
    return 1 + k * (k + 1) / 2


THEORY = {1: theory_1, 2: theory_2, 3: theory_3, 4: theory_4}

# leading term only (drop lower-order parts) - this is the g(n) in
# T(n) = Theta(g(n)). Dividing the empirical count by g(n) is more
# informative than dividing by the exact theory: that ratio is 1.0 by
# construction here, but empirical/g(n) actually converges to a
# non-trivial constant, which is the thing a Theta bound is claiming.
def g_1(n):
    return n * math.log2(n)


def g_2(n):
    return n * n


def g_3(n):
    return n * n


def g_4(n):
    k = math.log2(n)
    return k * k if k > 0 else 1


G = {1: g_1, 2: g_2, 3: g_3, 4: g_4}


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ns = [2 ** e for e in range(N_MIN_EXP, N_MAX_EXP + 1)]

    results = {rid: {"empirical": [], "theory": []} for rid in RECURRENCES}

    for rid, params in RECURRENCES.items():
        memo = {}
        for n in ns:
            emp = simulate(n, params["a"], params["b"], params["f"], memo)
            th = THEORY[rid](n)
            results[rid]["empirical"].append(emp)
            results[rid]["theory"].append(th)

    csv_path = os.path.join(OUTPUT_DIR, "recurrence_counts.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        header = ["n"]
        for rid in RECURRENCES:
            header += [f"R{rid}_empirical", f"R{rid}_theory", f"R{rid}_ratio"]
        writer.writerow(header)
        for i, n in enumerate(ns):
            row = [n]
            for rid in RECURRENCES:
                emp = results[rid]["empirical"][i]
                th = results[rid]["theory"][i]
                ratio = emp / th if th else float("nan")
                row += [emp, th, ratio]
            writer.writerow(row)
    print(f"wrote {csv_path}")

    import matplotlib.pyplot as plt

    for rid in RECURRENCES:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.plot(ns, results[rid]["empirical"], "o-", label="empirical (simulated)", markersize=3)
        ax.plot(ns, results[rid]["theory"], "--", label="theoretical closed form")
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xlabel("n")
        ax.set_ylabel("operation count")
        ax.set_title(f"Recurrence {rid}: empirical vs theoretical")
        ax.legend()
        fig.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"recurrence_{rid}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"wrote {out_path}")

    # empirical/theory is exactly 1.0 here (abstract simulation), so no
    # point plotting that
    for rid in RECURRENCES:
        g_ratios = [e / G[rid](n) for e, n in zip(results[rid]["empirical"], ns)]
        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.plot(ns, g_ratios, "o-", markersize=3)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("n")
        ax.set_ylabel("T(n) / g(n)")
        ax.set_title(f"Recurrence {rid}: empirical count over leading term g(n)")
        fig.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"g_ratio_{rid}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    run()
