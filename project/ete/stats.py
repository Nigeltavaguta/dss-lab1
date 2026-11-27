"""Small statistics helpers (standard library only).

* ``mean_ci``: mean with a Student-t 95% confidence interval.
* ``bootstrap_ci``: percentile bootstrap CI for any statistic (seeded).
* ``wilcoxon``: two-sided Wilcoxon signed-rank test for paired samples.
  Zero differences are dropped and tied ranks are averaged. The p-value is
  exact for n <= 20 without ties, otherwise it uses the normal
  approximation with tie correction and a continuity correction.
"""

from __future__ import annotations

import math
import random
import statistics

# Two-sided 95% Student-t critical values, by degrees of freedom.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
        14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
        20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}


def t_critical(df):
    if df in _T95:
        return _T95[df]
    keys = sorted(_T95)
    for k in keys:
        if k > df:
            return _T95[k]   # conservative: the next smaller df's value
    return 1.960


def mean_ci(values):
    values = list(values)
    n = len(values)
    m = statistics.fmean(values)
    if n < 2:
        return m, m, m
    half = t_critical(n - 1) * statistics.stdev(values) / math.sqrt(n)
    return m, m - half, m + half


def bootstrap_ci(values, stat=statistics.median, reps=2000, seed=1, alpha=0.05):
    values = list(values)
    rng = random.Random(seed)
    n = len(values)
    est = stat(values)
    samples = sorted(stat([values[rng.randrange(n)] for _ in range(n)])
                     for _ in range(reps))
    lo = samples[int(alpha / 2 * reps)]
    hi = samples[int((1 - alpha / 2) * reps) - 1]
    return est, lo, hi


def _ranks(abs_values):
    order = sorted(range(len(abs_values)), key=lambda i: abs_values[i])
    ranks = [0.0] * len(abs_values)
    ties = []
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and abs_values[order[j + 1]] == abs_values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        if j > i:
            ties.append(j - i + 1)
        i = j + 1
    return ranks, ties


def wilcoxon(x, y):
    """Return (W+, n_nonzero, p_value) for paired samples x and y."""
    diffs = [a - b for a, b in zip(x, y) if a != b]
    n = len(diffs)
    if n == 0:
        return 0.0, 0, 1.0
    ranks, ties = _ranks([abs(d) for d in diffs])
    w_plus = sum(r for r, d in zip(ranks, diffs) if d > 0)
    if n <= 20 and not ties:
        # Exact null distribution of W+ by dynamic programming.
        counts = {0: 1}
        for r in range(1, n + 1):
            nxt = dict(counts)
            for s, c in counts.items():
                nxt[s + r] = nxt.get(s + r, 0) + c
            counts = nxt
        total = 2 ** n
        w = int(round(w_plus))
        lo = sum(c for s, c in counts.items() if s <= w) / total
        hi = sum(c for s, c in counts.items() if s >= w) / total
        return w_plus, n, min(1.0, 2 * min(lo, hi))
    mean = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24 - sum(t ** 3 - t for t in ties) / 48
    if var == 0:
        return w_plus, n, 1.0
    z = (abs(w_plus - mean) - 0.5) / math.sqrt(var)
    p = math.erfc(max(z, 0) / math.sqrt(2))
    return w_plus, n, min(1.0, p)


def geometric_mean(values):
    values = [max(v, 1e-12) for v in values]
    return math.exp(sum(math.log(v) for v in values) / len(values))
