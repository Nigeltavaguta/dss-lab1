# Lab 5 - P vs. NP: Empirical and Theoretical Exploration

## Requirements

- Python 3 (tested with Python 3.12.0)
- matplotlib (tested with 3.11.2): `pip install matplotlib`

## Run

```
python run_all.py
```

Takes a few seconds. The exact Vertex Cover branch-and-bound at n=19-20 is the slowest single
step (tens of milliseconds). All CSVs and plots are written to `output/`.

## Files

| File | What it does | Output |
|---|---|---|
| `vertex_cover.py` | `min_vertex_cover_bb` (exact branch-and-bound), `approx_vertex_cover` (2-approximation via maximal matching). | - |
| `metric_tsp.py` | `tsp_held_karp` (exact DP, small n), `prim_mst` + `two_approx_tsp` (double-MST 2-approximation). | - |
| `subset_sum.py` | `exact_subset_sum` (pseudo-polynomial DP), `fptas_subset_sum` (scaling FPTAS). | - |
| `datasets.py` | Random graphs, Euclidean point sets (metric TSP instances), random subset-sum instances. | - |
| `benchmark.py` | Vertex-cover ratio vs. n, FPTAS accuracy/runtime vs. epsilon, TSP approximation ratio vs. n. | `output/*.csv` |
| `plot_results.py` | Turns those CSVs into the plots used in the report. | `output/*.png` |
| `run_all.py` | Runs both of the above in order. | |

## Report

The report is `report.md` (PDF: `../R236699C LAB 5.pdf`). It covers the complexity
classification table (SAT through integer factorization), the three polynomial-time reductions
(3-SAT to Clique, Clique to Vertex Cover, Vertex Cover to Set Cover) with correctness proofs,
the three approximation algorithms with their ratio proofs, the benchmark results, and a
1500-word critical essay on the implications of P != NP for cryptography, optimization, and AI.
