# Lab 4 - Backtracking and Branch-and-Bound for NP-Hard Problems

## Requirements

- Python 3 (tested with Python 3.12.0)
- matplotlib (tested with 3.11.2): `pip install matplotlib`

## Run

```
python run_all.py
```

Takes around 20 seconds on the tested machine. The dense-graph sweep includes an n=35
instance that took about 10 seconds for the exact branch-and-bound solver in the latest run.
Runtime varies by machine. All CSVs and plots are written to `output/`.

## Files

| File | What it does | Output |
|---|---|---|
| `graph_coloring.py` | The four algorithms: `naive_backtracking`, `backtracking_fc_mrv` (forward checking + MRV), `branch_and_bound_chromatic` (exact chromatic number, clique-based lower bound), `greedy_coloring` (Welsh-Powell by default, or a custom vertex order). | - |
| `datasets.py` | `random_graph` (Erdos-Renyi), `timetabling_instance` (exam-conflict graph from simulated student enrollments), `crown_graph` (the adversarial bipartite instance used to show greedy can be forced to use far more colors than necessary). | - |
| `benchmark.py` | Five benchmarks: pruning comparison, exact-vs-greedy quality, timetabling instances, a dense-graph worst-case sweep, and the greedy adversarial-order demo. | `output/*.csv` |
| `plot_results.py` | Turns those CSVs into the plots used in the report. | `output/*.png` |
| `run_all.py` | Runs both of the above in order. | |

## Report

The report is `report.md` (PDF: `../R236699C LAB 4.pdf`). It covers the graph-coloring model
of exam timetabling, the NP-completeness proof (reduction from 3-SAT), the pruning analysis,
the greedy approximation-ratio analysis (with the crown-graph counterexample), the benchmark
results, and a deployment recommendation.
