import csv
import math
import os
import random
import time

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


# --- R1: merge sort ---

def merge_sort_count(arr, counter):
    n = len(arr)
    if n <= 1:
        return arr
    mid = n // 2
    left = merge_sort_count(arr[:mid], counter)
    right = merge_sort_count(arr[mid:], counter)
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        counter[0] += 1
        if left[i] <= right[j]:
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    while i < len(left):
        merged.append(left[i]); i += 1; counter[0] += 1
    while j < len(right):
        merged.append(right[j]); j += 1; counter[0] += 1
    return merged


def run_r1(n):
    arr = [random.random() for _ in range(n)]
    counter = [0]
    t0 = time.perf_counter()
    merge_sort_count(arr, counter)
    t1 = time.perf_counter()
    return counter[0], t1 - t0


# --- R2: brute-force combine instead of a merge. Note this does NOT
# count inversions (it never compares a and b, just counts the pair) -
# it's only here to cost (n/2)*(n/2) = n^2/4 comparisons per combine
# step, which is Theta(n^2) but NOT the same constant as f(n) = n^2 in
# the abstract recurrence. That mismatch is the point - see report. ---

def quadratic_combine(arr, counter):
    n = len(arr)
    if n <= 1:
        return
    mid = n // 2
    left, right = arr[:mid], arr[mid:]
    quadratic_combine(left, counter)
    quadratic_combine(right, counter)
    for a in left:
        for b in right:
            counter[0] += 1


def run_r2(n):
    arr = [random.random() for _ in range(n)]
    counter = [0]
    t0 = time.perf_counter()
    quadratic_combine(arr, counter)
    t1 = time.perf_counter()
    return counter[0], t1 - t0


# --- R3: the old pre-Karatsuba way of multiplying two n-bit numbers -
# split each into high/low halves, 4 recursive half-size multiplications,
# then combine with shifts and adds. Deliberately not memoized, this is
# meant to actually cost what the recurrence says. ---

def mult_4way(x, y, n_bits, counter):
    if n_bits <= 1:
        counter[0] += 1
        return x * y
    half = n_bits // 2
    mask = (1 << half) - 1
    x1, x0 = x >> half, x & mask
    y1, y0 = y >> half, y & mask
    ac = mult_4way(x1, y1, half, counter)
    ad = mult_4way(x1, y0, half, counter)
    bc = mult_4way(x0, y1, half, counter)
    bd = mult_4way(x0, y0, half, counter)
    counter[0] += half  # the O(n) shift/add combine
    return (ac << (2 * half)) + ((ad + bc) << half) + bd


def run_r3(n_bits):
    x = random.getrandbits(n_bits)
    y = random.getrandbits(n_bits)
    counter = [0]
    t0 = time.perf_counter()
    result = mult_4way(x, y, n_bits, counter)
    t1 = time.perf_counter()
    assert result == x * y  # just making sure the split/combine is correct
    return counter[0], t1 - t0


# --- R4: binary search over the first n elements of a side array
# (O(log n) work), then recurse with n halved.
#
# First version of this searched the FULL side array at every level
# instead of just the first n elements, so it was really simulating
# T(n) = T(n/2) + log N for a fixed N (ratio kept climbing instead of
# settling). Fixed by passing n as the search bound instead of re-slicing
# the array. Also avoids arr[:n//2]-style slicing, which was copying an
# O(n) array at every level and swamping the wall-clock numbers with
# copy cost instead of actual search cost. ---

def binsearch(sorted_arr, hi_bound, target, counter):
    lo, hi = 0, hi_bound - 1
    while lo <= hi:
        counter[0] += 1
        mid = (lo + hi) // 2
        if sorted_arr[mid] == target:
            return mid
        elif sorted_arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def recursive_probe(n, side_sorted, counter):
    if n <= 1:
        return
    target = side_sorted[random.randint(0, n - 1)]
    binsearch(side_sorted, n, target, counter)
    recursive_probe(n // 2, side_sorted, counter)


def run_r4(n):
    side_sorted = sorted(random.sample(range(n * 2), n))
    counter = [0]
    t0 = time.perf_counter()
    recursive_probe(n, side_sorted, counter)
    t1 = time.perf_counter()
    return counter[0], t1 - t0


# closed forms, same as in task2_task3.py / the report
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


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    random.seed(42)

    # R1/R4 are cheap, full 2^1..2^20 sweep. R2/R3 do real O(n^2)-scale
    # work so I capped them - see comment at the top of the file.
    ranges = {
        1: range(1, 21),
        2: range(1, 13),   # n = 4096, n^2 combine = ~16.7M comparisons
        3: range(1, 11),   # 1024-bit, unmemoized 4-way recursion
        4: range(1, 21),
    }
    runners = {1: run_r1, 2: run_r2, 3: run_r3, 4: run_r4}
    theories = {1: theory_1, 2: theory_2, 3: theory_3, 4: theory_4}

    rows = []
    for rid in (1, 2, 3, 4):
        for e in ranges[rid]:
            n = 2 ** e
            emp_ops, wall_time = runners[rid](n)
            th = theories[rid](n)
            ratio = emp_ops / th if th else float("nan")
            rows.append((rid, n, emp_ops, th, ratio, wall_time))
            print(f"R{rid} n=2^{e}={n}: ops={emp_ops} theory={th:.1f} "
                  f"ratio={ratio:.3f} time={wall_time:.6f}s")

    csv_path = os.path.join(OUTPUT_DIR, "real_implementations.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["recurrence", "n", "empirical_ops", "theory", "ratio", "wall_time_s"])
        writer.writerows(rows)
    print(f"\nwrote {csv_path}")

    import matplotlib.pyplot as plt
    from collections import defaultdict

    by_rid = defaultdict(list)
    for rid, n, emp, th, ratio, t in rows:
        by_rid[rid].append((n, emp, th, ratio, t))

    for rid, data in by_rid.items():
        ns = [d[0] for d in data]
        emps = [d[1] for d in data]
        ths = [d[2] for d in data]
        times = [d[4] for d in data]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
        ax1.plot(ns, emps, "o-", label="empirical ops (real impl.)", markersize=3)
        ax1.plot(ns, ths, "--", label="theoretical closed form")
        ax1.set_xscale("log", base=2)
        ax1.set_yscale("log")
        ax1.set_xlabel("n")
        ax1.set_ylabel("operation count")
        ax1.set_title(f"R{rid}: real op count vs theory")
        ax1.legend()

        ax2.plot(ns, times, "o-", color="tab:red")
        ax2.set_xscale("log", base=2)
        ax2.set_yscale("log")
        ax2.set_xlabel("n")
        ax2.set_ylabel("wall-clock time (s)")
        ax2.set_title(f"R{rid}: wall-clock time")

        fig.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"real_r{rid}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    run()
