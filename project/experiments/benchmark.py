"""Run every experiment and write CSV files to ../output.

    python experiments/benchmark.py            # full run (about 15-20 min)
    python experiments/benchmark.py --quick    # small smoke run
    python experiments/benchmark.py --resume   # skip experiments already in output/

Experiments
  E1 pruning      nodes for naive BT vs FC vs FC+MRV vs FC+MRV+degree vs MAC
  E2 scaling      greedy, BT, B&B and hybrid on n = 10..500 (time, slots, gap)
  E3 greedy       approximation ratio of greedy orders, crown worst case
  E4 bnb_ablation effect of the lower bound and the initial upper bound
  E5 trace        anytime behaviour of the hybrid on large instances
  E6 reduction    3-SAT -> 3-colouring -> timetabling agreement check
  E7 timetable    full UZ-inspired timetable with venues (n = 500)
  stats           confidence intervals and Wilcoxon tests for the report
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "output")

from ete.backtracking import backtracking, min_slots_backtracking, naive_backtracking
from ete.bounds import clique_bound, lower_bound, venue_bound
from ete.branch_bound import branch_and_bound
from ete.generators import crown_instance, random_instance, uz_instance
from ete.greedy import greedy
from ete.hybrid import hybrid
from ete.local_search import local_search
from ete.model import assign_venues, slots_used, violations
from ete.reductions import (brute_force_sat, colouring_from_assignment,
                            colouring_to_timetabling, is_satisfied, random_3sat,
                            sat_to_colouring)
from ete.stats import bootstrap_ci, geometric_mean, mean_ci, wilcoxon


def write_csv(name, rows):
    path = os.path.join(OUT, name)
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {name} ({len(rows)} rows)")


def make(dataset, n, seed):
    if dataset == "uz":
        return uz_instance(n, seed)
    p = 0.3 if n <= 40 else 0.1
    return random_instance(n, p, seed)


# ---------------------------------------------------------------- E1 ------
VARIANTS = [
    ("naive", lambda i, k, L: naive_backtracking(i, k, node_limit=L)),
    ("fc", lambda i, k, L: backtracking(i, k, mrv=False, degree=False, node_limit=L)),
    ("fc+mrv", lambda i, k, L: backtracking(i, k, degree=False, node_limit=L)),
    ("fc+mrv+deg", lambda i, k, L: backtracking(i, k, node_limit=L)),
    ("fc+mrv+deg+mac", lambda i, k, L: backtracking(i, k, mac=True, node_limit=L)),
]


def e1_pruning(sizes, seeds, node_limit):
    print("E1 pruning")
    rows = []
    for dataset in ("random", "uz"):
        for n in sizes:
            for seed in seeds:
                inst = make(dataset, n, seed)
                opt = branch_and_bound(inst, time_limit=30)
                if not opt.optimal:
                    continue
                for case, k in (("feasible k=opt", opt.slots), ("refute k=opt-1", opt.slots - 1)):
                    if k < 1:
                        continue
                    for name, solve in VARIANTS:
                        r = solve(inst, k, node_limit)
                        rows.append({"dataset": dataset, "n": n, "seed": seed,
                                     "case": case, "k": k, "variant": name,
                                     "nodes": r.nodes, "seconds": round(r.seconds, 5),
                                     "status": r.status})
    write_csv("e1_pruning.csv", rows)
    return rows


# ---------------------------------------------------------------- E2 ------
def e2_scaling(sizes, seeds, budget):
    print("E2 scaling")
    rows = []
    for dataset in ("uz", "random"):
        for n in sizes:
            for seed in seeds:
                inst = make(dataset, n, seed)
                lb = lower_bound(inst)
                runs = [greedy(inst, "largest_first"), greedy(inst, "dsatur"),
                        min_slots_backtracking(inst, time_limit=budget),
                        branch_and_bound(inst, time_limit=budget, lb=lb),
                        hybrid(inst, time_limit=budget, seed=seed)]
                names = ["greedy-LF", "greedy-DSATUR", "BT-FC-MRV-deg",
                         "B&B", "hybrid"]
                for name, r in zip(names, runs):
                    found = r.assignment is not None and r.slots is not None
                    rows.append({
                        "dataset": dataset, "n": n, "seed": seed,
                        "edges": inst.num_edges, "algorithm": name,
                        "slots": r.slots if found else "",
                        "lower_bound": lb,
                        "gap": (r.slots - lb) if found else "",
                        "optimal": int(bool(r.optimal) or (found and r.slots == lb)),
                        "conflicts": violations(inst, r.assignment) if found else "",
                        "seconds": round(r.seconds, 5), "nodes": r.nodes,
                        "status": r.status,
                    })
            print(f"  {dataset} n={n} done")
    write_csv("e2_scaling.csv", rows)
    return rows


# ---------------------------------------------------------------- E3 ------
def e3_greedy(seeds):
    print("E3 greedy")
    crown = []
    for k in range(2, 31):
        inst = crown_instance(k)
        crown.append({"k": k, "vertices": 2 * k, "chi": 2,
                      "natural": greedy(inst, "natural").slots,
                      "largest_first": greedy(inst, "largest_first").slots,
                      "dsatur": greedy(inst, "dsatur").slots,
                      "delta_plus_1": inst.max_degree() + 1})
    write_csv("e3_crown.csv", crown)
    rows = []
    for p in (0.1, 0.3, 0.5):
        for seed in seeds:
            inst = random_instance(30, p, seed)
            opt = branch_and_bound(inst, time_limit=30)
            if not opt.optimal:
                continue
            row = {"p": p, "seed": seed, "chi": opt.slots,
                   "clique": clique_bound(inst), "delta_plus_1": inst.max_degree() + 1}
            for order in ("natural", "random", "largest_first", "dsatur"):
                row[order] = greedy(inst, order, seed).slots
            rows.append(row)
    write_csv("e3_greedy_ratio.csv", rows)
    return crown, rows


# ---------------------------------------------------------------- E4 ------
def e4_bnb(seeds, time_limit):
    print("E4 B&B ablation")
    configs = [("LB + greedy UB", True, True), ("greedy UB only", False, True),
               ("LB only", True, False), ("neither", False, False)]
    rows = []
    cases = [("random", 30, 0.5), ("random", 40, 0.5), ("random", 50, 0.3),
             ("random", 60, 0.3), ("uz", 30, None), ("uz", 50, None), ("uz", 80, None)]
    for dataset, n, p in cases:
        for seed in seeds:
            inst = random_instance(n, p, seed) if dataset == "random" else uz_instance(n, seed)
            for name, use_lb, use_ub in configs:
                r = branch_and_bound(inst, use_lower_bound=use_lb, use_greedy_ub=use_ub,
                                     time_limit=time_limit)
                rows.append({"dataset": dataset, "n": n, "p": p or "", "seed": seed,
                             "config": name, "slots": r.slots or "",
                             "optimal": int(r.optimal), "nodes": r.nodes,
                             "seconds": round(r.seconds, 5)})
    write_csv("e4_bnb_ablation.csv", rows)
    return rows


# ---------------------------------------------------------------- E5 ------
def e5_trace(budget):
    print("E5 anytime trace")
    rows = []
    for label, inst in (("random n=500 p=0.1", random_instance(500, 0.1, 1)),
                        ("random n=300 p=0.1", random_instance(300, 0.1, 1)),
                        ("uz n=500", uz_instance(500, 1))):
        lb = lower_bound(inst)
        h = hybrid(inst, time_limit=budget, seed=1)
        for t, k in h.extra["trace"]:
            rows.append({"instance": label, "solver": "hybrid", "time": round(t, 4),
                         "slots": k, "lower_bound": lb})
        b = branch_and_bound(inst, time_limit=budget, lb=lb)
        for t, k in b.extra["trace"]:
            rows.append({"instance": label, "solver": "B&B", "time": round(t, 4),
                         "slots": k, "lower_bound": lb})
        g = greedy(inst, "dsatur")
        ls = local_search(inst, g.assignment, lb, budget, seed=1)
        for t, k in ls.extra["trace"]:
            rows.append({"instance": label, "solver": "DSATUR + tabu",
                         "time": round(g.seconds + t, 4), "slots": k, "lower_bound": lb})
        print(f"  {label}: hybrid {h.slots}, B&B {b.slots}, tabu {ls.slots}, LB {lb}")
    write_csv("e5_trace.csv", rows)
    return rows


# ---------------------------------------------------------------- E6 ------
def e6_reduction(seeds):
    """Check both directions of 3-SAT <=p 3-colouring <=p timetabling.

    Part A (3-variable formulas): exact search decides whether the reduced
    instance has a 3-slot timetable, and this is compared with brute-force
    SAT. Part B (larger formulas): satisfiable formulas are planted, and the
    colouring built constructively from the satisfying assignment is checked
    to be a conflict-free 3-slot timetable. This also records how the
    instance grows with the formula.
    """
    print("E6 reduction check")
    rows = []
    nv = 3
    for m in (8, 12, 16, 20):
        for seed in seeds:
            clauses = random_3sat(nv, m, seed)
            sat = brute_force_sat(clauses, nv) is not None
            adj = sat_to_colouring(clauses, nv)
            inst = colouring_to_timetabling(adj, 3)
            r = branch_and_bound(inst, use_greedy_ub=False, time_limit=15)
            decided = r.status != "limit"
            colourable = r.status == "solved" and r.slots is not None and r.slots <= 3
            rows.append({"part": "A exact", "vars": nv, "clauses": m, "seed": seed,
                         "exams": inst.n, "conflict_edges": inst.num_edges,
                         "satisfiable": int(sat),
                         "timetable_3_slots": int(colourable) if decided else "",
                         "agree": int(sat == colourable) if decided else "",
                         "nodes": r.nodes, "seconds": round(r.seconds, 4)})
    for nv in (10, 20, 50, 100, 200):
        m = round(4.26 * nv)
        for seed in seeds:
            rng = random.Random(seed)
            planted = [rng.random() < 0.5 for _ in range(nv)]
            clauses = []
            while len(clauses) < m:
                c = random_3sat(nv, 1, rng.random())[0]
                if is_satisfied([c], planted):
                    clauses.append(c)
            start = time.perf_counter()
            adj = sat_to_colouring(clauses, nv)
            inst = colouring_to_timetabling(adj, 3)
            colouring = colouring_from_assignment(clauses, nv, planted)
            ok = colouring is not None and violations(inst, colouring) == 0
            rows.append({"part": "B constructive", "vars": nv, "clauses": m,
                         "seed": seed, "exams": inst.n,
                         "conflict_edges": inst.num_edges, "satisfiable": 1,
                         "timetable_3_slots": int(ok), "agree": int(ok),
                         "nodes": 0, "seconds": round(time.perf_counter() - start, 4)})
    write_csv("e6_reduction.csv", rows)
    return rows


# ---------------------------------------------------------------- E7 ------
def e7_timetable(budget):
    print("E7 UZ timetable")
    inst = uz_instance(500, 1)
    res = hybrid(inst, time_limit=budget, seed=1)
    rooms = assign_venues(inst, res.assignment)
    venue = {v.id: v for v in inst.venues}
    lect = {l.id: l for l in inst.lecturers}
    rows = []
    for e in sorted(range(inst.n), key=lambda e: (res.assignment[e], -inst.sizes[e])):
        t = res.assignment[e]
        v = venue[rooms[e]]
        rows.append({"slot": t + 1, "day": t // 2 + 1,
                     "session": "09:00" if t % 2 == 0 else "14:00",
                     "exam": inst.exams[e].code, "students": inst.sizes[e],
                     "venue": v.name, "capacity": v.capacity,
                     "lecturer": lect[inst.exams[e].lecturer].name})
    write_csv("e7_timetable.csv", rows)
    # Summary for the report.
    seats = sum(v.capacity for v in inst.venues)
    per_slot = {}
    for e, t in enumerate(res.assignment):
        per_slot.setdefault(t, []).append(e)
    util = [sum(inst.sizes[e] for e in es) / seats for es in per_slot.values()]
    same_day = 0
    for g in inst.groups:
        days = [res.assignment[e] // 2 for e in g.exams]
        same_day += (len(days) - len(set(days))) * g.size
    summary = [{
        "exams": inst.n, "edges": inst.num_edges, "groups": len(inst.groups),
        "students_seated": sum(inst.sizes), "venues": len(inst.venues),
        "lecturers": len(inst.lecturers),
        "restricted_exams": inst.summary()["restricted_exams"],
        "clique_bound": clique_bound(inst), "venue_bound": venue_bound(inst),
        "slots": res.slots, "days": (res.slots + 1) // 2,
        "optimal": int(res.optimal), "conflicts": violations(inst, res.assignment),
        "seconds": round(res.seconds, 3),
        "mean_seat_utilisation": round(statistics.fmean(util), 3),
        "student_same_day_pairs": same_day,
    }]
    write_csv("e7_summary.csv", summary)
    return summary


# ------------------------------------------------------------- stats ------
def statistics_tables(e1, e2, e4):
    print("Statistics")
    rows = []

    def nodes_by(dataset, case, variant):
        sel = [r for r in e1 if r["dataset"] == dataset and r["case"] == case
               and r["variant"] == variant]
        sel.sort(key=lambda r: (r["n"], r["seed"]))
        return [r["nodes"] for r in sel]

    for dataset in ("random", "uz"):
        for case in ("feasible k=opt", "refute k=opt-1"):
            base = nodes_by(dataset, case, "naive")
            for variant, _ in VARIANTS[1:]:
                other = nodes_by(dataset, case, variant)
                reductions = [100 * (1 - o / b) for o, b in zip(other, base) if b > 0]
                med, lo, hi = bootstrap_ci(reductions)
                w, n, p = wilcoxon(base, other)
                rows.append({"test": "E1 pruning vs naive", "dataset": dataset,
                             "case": case, "comparison": f"naive vs {variant}",
                             "n_pairs": len(other),
                             "median_reduction_pct": round(med, 2),
                             "ci_low": round(lo, 2), "ci_high": round(hi, 2),
                             "wilcoxon_W": w, "nonzero": n, "p_value": f"{p:.3g}"})
            for a, b in (("fc+mrv", "fc+mrv+deg"), ("fc+mrv+deg", "fc+mrv+deg+mac")):
                xa, xb = nodes_by(dataset, case, a), nodes_by(dataset, case, b)
                ratio = [y / x for x, y in zip(xa, xb) if x > 0]
                gm = geometric_mean(ratio) if ratio else float("nan")
                w, n, p = wilcoxon(xa, xb)
                rows.append({"test": "E1 heuristic step", "dataset": dataset,
                             "case": case, "comparison": f"{a} vs {b}",
                             "n_pairs": len(xa),
                             "median_reduction_pct": round(100 * (1 - gm), 2),
                             "ci_low": "", "ci_high": "",
                             "wilcoxon_W": w, "nonzero": n, "p_value": f"{p:.3g}"})

    for dataset in ("uz", "random"):
        def slots_of(alg):
            sel = [r for r in e2 if r["dataset"] == dataset and r["algorithm"] == alg]
            sel.sort(key=lambda r: (r["n"], r["seed"]))
            return sel
        hyb = slots_of("hybrid")
        for other in ("greedy-LF", "greedy-DSATUR", "B&B"):
            oth = slots_of(other)
            pairs = [(o["slots"], h["slots"]) for o, h in zip(oth, hyb)
                     if o["slots"] != "" and h["slots"] != ""]
            diffs = [a - b for a, b in pairs]
            m, lo, hi = mean_ci(diffs)
            w, n, p = wilcoxon([a for a, _ in pairs], [b for _, b in pairs])
            rows.append({"test": "E2 slots saved by hybrid", "dataset": dataset,
                         "case": "all n", "comparison": f"{other} - hybrid",
                         "n_pairs": len(pairs),
                         "median_reduction_pct": round(m, 3),
                         "ci_low": round(lo, 3), "ci_high": round(hi, 3),
                         "wilcoxon_W": w, "nonzero": n, "p_value": f"{p:.3g}"})

    full = [r for r in e4 if r["config"] == "LB + greedy UB"]
    for other in ("greedy UB only", "LB only", "neither"):
        oth = [r for r in e4 if r["config"] == other]
        a = [r["nodes"] for r in oth]
        b = [r["nodes"] for r in full]
        ratio = [y / x for x, y in zip(a, b) if x > 0]
        w, n, p = wilcoxon(a, b)
        rows.append({"test": "E4 B&B ablation", "dataset": "all", "case": "nodes",
                     "comparison": f"{other} vs LB + greedy UB",
                     "n_pairs": len(a),
                     "median_reduction_pct": round(100 * (1 - geometric_mean(ratio)), 2),
                     "ci_low": "", "ci_high": "", "wilcoxon_W": w, "nonzero": n,
                     "p_value": f"{p:.3g}"})
    write_csv("stats_tests.csv", rows)

    summary = []
    for dataset in ("uz", "random"):
        for alg in ("greedy-LF", "greedy-DSATUR", "BT-FC-MRV-deg", "B&B", "hybrid"):
            for n in sorted({r["n"] for r in e2}):
                sel = [r for r in e2 if r["dataset"] == dataset and r["algorithm"] == alg
                       and r["n"] == n]
                if not sel:
                    continue
                times = [r["seconds"] for r in sel]
                found = [r for r in sel if r["slots"] != ""]
                gaps = [r["gap"] for r in found]
                tm, tlo, thi = mean_ci(times)
                gm = mean_ci(gaps) if gaps else ("", "", "")
                summary.append({
                    "dataset": dataset, "algorithm": alg, "n": n, "runs": len(sel),
                    "solved": len(found),
                    "proven_optimal": sum(r["optimal"] for r in sel),
                    "mean_slots": round(statistics.fmean(r["slots"] for r in found), 3) if found else "",
                    "mean_lb": round(statistics.fmean(r["lower_bound"] for r in sel), 3),
                    "mean_gap": round(gm[0], 3) if gaps else "",
                    "gap_ci_low": round(gm[1], 3) if gaps else "",
                    "gap_ci_high": round(gm[2], 3) if gaps else "",
                    "mean_seconds": round(tm, 5), "sec_ci_low": round(max(0, tlo), 5),
                    "sec_ci_high": round(thi, 5),
                    "max_conflicts": max((r["conflicts"] for r in found), default=""),
                })
    write_csv("e2_summary.csv", summary)


def _load(name, ints=(), floats=()):
    """Read a CSV written earlier, converting numeric columns."""
    with open(os.path.join(OUT, name), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ints:
            r[k] = int(r[k]) if r[k] != "" else ""
        for k in floats:
            r[k] = float(r[k]) if r[k] != "" else ""
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--resume", action="store_true",
                        help="reuse experiment CSVs that already exist in output/")
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    start = time.perf_counter()

    def have(name):
        return args.resume and os.path.exists(os.path.join(OUT, name))

    if args.quick:
        e1 = e1_pruning([10, 15], range(1, 4), 20000)
        e2 = e2_scaling([10, 50, 100], range(1, 3), 0.5)
        e3_greedy(range(1, 4))
        e4 = e4_bnb(range(1, 3), 2)
        e5_trace(2)
        e6_reduction(range(1, 3))
        e7_timetable(2)
    else:
        e1 = _load("e1_pruning.csv", ints=("n", "seed", "k", "nodes")) if have("e1_pruning.csv")             else e1_pruning([10, 15, 20, 25, 30], range(1, 16), 200000)
        e2 = _load("e2_scaling.csv", ints=("n", "seed", "slots", "lower_bound", "gap",
                                           "optimal", "conflicts", "nodes"),
                   floats=("seconds",)) if have("e2_scaling.csv")             else e2_scaling([10, 25, 50, 100, 200, 300, 400, 500], range(1, 7), 2.0)
        if not have("e3_greedy_ratio.csv"):
            e3_greedy(range(1, 21))
        e4 = _load("e4_bnb_ablation.csv", ints=("n", "seed", "optimal", "nodes"))             if have("e4_bnb_ablation.csv") else e4_bnb(range(1, 11), 10)
        if not have("e5_trace.csv"):
            e5_trace(20)
        if not have("e6_reduction.csv"):
            e6_reduction(range(1, 11))
        if not have("e7_summary.csv"):
            e7_timetable(10)
    statistics_tables(e1, e2, e4)
    print(f"Done in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
