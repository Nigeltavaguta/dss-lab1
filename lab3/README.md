# Lab 3 - Dynamic Programming vs. Greedy

Full commit history: https://github.com/Nigeltavaguta/dss-lab1

## Requirements

- Python 3 (tested with Python 3.12.0)
- matplotlib: `pip install matplotlib`

## Run

```
python run_all.py
```

Runs the knapsack, coin-change, and TSP benchmarks, then regenerates the plots. Takes a
few seconds (TSP's exact solver is exponential, but the sizes here are kept small on
purpose - see the report). Output goes to `output/`. `plot_results.py` forces matplotlib's
`Agg` backend, so this runs headless with no display needed and no `MPLBACKEND` env var
to set manually, even on machines whose default backend needs Tk/a display.

## Files

| File | What it does |
|---|---|
| `knapsack.py` | 0-1 knapsack: 2D DP, 1D DP (space-optimized), branch and bound. Plus the fractional greedy, which solves a different (easier) problem and is used both as a counterexample and as the B&B bounding function. |
| `coin_change.py` | Minimum coins for a target amount: DP, greedy (largest coin first), BFS. |
| `tsp.py` | Held-Karp exact DP, nearest-neighbor greedy, 2-opt local search. |
| `synthesis.py` | The Task 5 synthesis problem (orienteering: pick cities and a route to maximize value collected under a travel budget). Run directly for a small demo. |
| `datasets.py` | Instance generators used by the benchmarks. |
| `benchmark.py` | Runs everything across a range of sizes, writes CSVs to `output/`. |
| `plot_results.py` | Turns the CSVs into the plots used in the report. |
| `run_all.py` | Runs the above two in order. |

## Report

The report is `report.md` (PDF: `../R236699C LAB 3.pdf`). It covers the greedy-vs-DP
proofs and counterexamples (Task 1), the implementations and complexity analysis
(Tasks 2-3), the TSP approximation-ratio proof (Task 4), the benchmark results (Task 5),
and the orienteering synthesis (Task 5 of the brief's numbering - the novel problem).
