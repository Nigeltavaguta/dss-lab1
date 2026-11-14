
from fractions import Fraction


def exact_subset_sum(weights, target):
    # Pseudo-polynomial: O(n * target), not polynomial in target's bit length.
    reachable = {0}
    for w in weights:
        reachable |= {s + w for s in reachable if s + w <= target}
    return max(reachable)


def fptas_subset_sum(weights, target, epsilon):

    n = len(weights)
    if n == 0 or target <= 0:
        return 0
    if any(w < 0 for w in weights):
        raise ValueError("weights must be nonnegative")
    epsilon = Fraction(str(epsilon))
    if not 0 < epsilon < 1:
        raise ValueError("epsilon must be between 0 and 1")
    feasible = [w for w in weights if 0 < w <= target]
    if not feasible:
        return 0
    max_item = max(feasible)
    best_for_scaled = {0: 0}  # scaled sum -> smallest true sum achieving it
    for w in feasible:
        scaled_w = (w * n * epsilon.denominator) // (epsilon.numerator * max_item)
        updates = {}
        for s, true_sum in best_for_scaled.items():
            ns, nt = s + scaled_w, true_sum + w
            if nt <= target and (ns not in best_for_scaled or best_for_scaled[ns] > nt) \
                    and (ns not in updates or updates[ns] > nt):
                updates[ns] = nt
        for s, nt in updates.items():
            if s not in best_for_scaled or best_for_scaled[s] > nt:
                best_for_scaled[s] = nt
    return max(best_for_scaled.values())
