"""Monte Carlo estimators and reproducible simulation experiments."""

from __future__ import annotations

import math
import random
import statistics
from itertools import product


def mean_ci(samples, z=1.96):
    mean = statistics.fmean(samples)
    if len(samples) < 2:
        return mean, float("nan"), float("nan")
    half = z * statistics.stdev(samples) / math.sqrt(len(samples))
    return mean, mean - half, mean + half


def wilson_interval(successes, trials, z=1.96):
    p = successes / trials
    denom = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return center - half, center + half


def estimate_pi(samples, seed=0):
    rng = random.Random(seed)
    hits = sum(rng.random() ** 2 + rng.random() ** 2 <= 1 for _ in range(samples))
    p = hits / samples
    lo, hi = wilson_interval(hits, samples)
    return {"samples": samples, "hits": hits, "estimate": 4 * p, "ci_low": 4 * lo, "ci_high": 4 * hi}


def mm1_simulation(lam=0.8, mu=1.0, customers=100_000, seed=0):
    """Arrival-epoch M/M/1 simulation via Lindley's waiting-time recursion."""
    if not 0 < lam < mu:
        raise ValueError("stable M/M/1 requires 0 < lambda < mu")
    rng = random.Random(seed)
    wait = 0.0
    system_times = []
    busy = 0.0
    elapsed = 0.0
    warmup = min(customers // 10, 5000)
    for i in range(customers + warmup):
        interarrival = rng.expovariate(lam)
        service = rng.expovariate(mu)
        wait = max(0.0, wait + service - interarrival)
        if i >= warmup:
            system_times.append(wait + service)
        busy += service
        elapsed += interarrival
    mean = statistics.fmean(system_times)
    batches = [system_times[i:i + max(1, customers // 40)]
               for i in range(0, len(system_times), max(1, customers // 40))]
    batch_means = [statistics.fmean(batch) for batch in batches if batch]
    half = 2.023 * statistics.stdev(batch_means) / math.sqrt(len(batch_means))
    lo, hi = mean - half, mean + half
    return {"customers": customers, "lambda": lam, "mu": mu, "utilization_theory": lam / mu,
            "W_theory": 1 / (mu - lam), "W_estimate": mean, "ci_low": lo, "ci_high": hi,
            "busy_fraction_estimate": busy / elapsed}


def rare_event_loss(samples=500_000, mu=0.0, sigma=1.0, threshold=4.0, shift=4.5, seed=0):
    """Compare crude MC with exponential-tilting IS for Gaussian portfolio loss."""
    rng = random.Random(seed)
    crude = [float((x := rng.gauss(mu, sigma)) > threshold) for _ in range(samples)]
    shifted = []
    for _ in range(samples):
        x = rng.gauss(shift, sigma)
        # f_mu(x) / f_shift(x), evaluated in log space.
        log_weight = ((x - shift) ** 2 - (x - mu) ** 2) / (2 * sigma * sigma)
        shifted.append(math.exp(log_weight) if x > threshold else 0.0)
    cmean = statistics.fmean(crude)
    clo, chi = wilson_interval(int(sum(crude)), samples)
    imean, ilo, ihi = mean_ci(shifted)
    crude_var = statistics.variance(crude)
    is_var = statistics.variance(shifted)
    return {"samples": samples, "mu": mu, "sigma": sigma, "threshold": threshold,
            "proposal_mean": shift, "threshold_sigma": (threshold - mu) / sigma,
            "crude_estimate": cmean, "crude_ci_low": clo, "crude_ci_high": chi,
            "is_estimate": imean, "is_ci_low": ilo, "is_ci_high": ihi,
            "crude_sample_variance": crude_var, "is_sample_variance": is_var,
            "variance_reduction": crude_var / is_var if is_var else float("inf"),
            "crude_hits": int(sum(crude))}


def variance_reduction(samples=100_000, seed=0):
    """Estimate integral_0^1 exp(u) du using plain, antithetic, and control MC."""
    rng = random.Random(seed)
    us = [rng.random() for _ in range(samples)]
    vals = [math.exp(u) for u in us]
    plain_var = statistics.variance(vals)
    paired = [(math.exp(u) + math.exp(1 - u)) / 2 for u in us]
    anti_var = statistics.variance(paired)
    control = [u - 0.5 for u in us]
    # The known integral gives Cov(exp(U), U - 1/2) = (3-e)/2 and
    # Var(U - 1/2) = 1/12, so beta is fixed rather than fitted on the same data.
    beta = 6 * (3 - math.e)
    controlled = [v - beta * c for v, c in zip(vals, control)]
    cv_var = statistics.variance(controlled)
    exact = math.e - 1
    return {"samples": samples, "exact": exact,
            "plain_estimate": statistics.fmean(vals), "plain_variance": plain_var,
            "antithetic_estimate": statistics.fmean(paired), "antithetic_variance": anti_var,
            "control_estimate": statistics.fmean(controlled), "control_variance": cv_var,
            "antithetic_reduction": plain_var / anti_var,
            "control_reduction": plain_var / cv_var, "control_beta": beta}


def five_d_integral(samples=100_000, seed=0):
    """MC and tensor midpoint quadrature for integral exp(sum(x_i)) on [0,1]^5."""
    rng = random.Random(seed)
    values = [math.exp(sum(rng.random() for _ in range(5))) for _ in range(samples)]
    estimate, lo, hi = mean_ci(values)
    exact = (math.e - 1) ** 5
    return {"samples": samples, "mc_estimate": estimate, "mc_ci_low": lo, "mc_ci_high": hi,
            "exact": exact, "mc_abs_error": abs(estimate - exact)}


def midpoint_5d(points_per_axis):
    """Explicit tensor midpoint rule; cost is m**5 function evaluations."""
    m = points_per_axis
    if m < 1:
        raise ValueError("points_per_axis must be positive")
    coordinates = [(i + 0.5) / m for i in range(m)]
    total = 0.0
    for point in product(coordinates, repeat=5):
        total += math.exp(sum(point))
    return total / (m ** 5)
