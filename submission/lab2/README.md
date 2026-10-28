# Lab 2: Sorting Under Real-World Constraints

Python 3 is required; Matplotlib is needed only to regenerate the plots. Run from this folder:

```powershell
python benchmark.py --sizes 500 2000 5000 --repeats 3
python benchmark.py --sizes 10000 20000 --algorithms merge quick_hoare heap timsort timsort_edu hybrid --repeats 3 --out output/fast_20k.csv
python plot_results.py
python external_sort.py transactions.csv sorted.csv --chunk-mib 128 --fan-in 32
```

The benchmark writes `output/benchmarks.csv` with median, minimum, and maximum timings, key-comparison counts, and correctness checks. Each run sorts fresh transaction-like records by timestamp, amount, then merchant; `id` is only a deterministic tie breaker in checking. Dataset generation is seeded. The adversarial distribution targets Lomuto's endpoint-pivot weakness. `quick_mom` is an in-place median-of-medians defense; `hybrid` detects monotone runs, insertion-sorts small pieces in its introsort path, and uses heapsort when partition depth is exhausted. `timsort_edu` is an educational implementation of natural runs, minrun insertion, and run-stack merging. Python's built-in `list.sort` remains the production Timsort baseline. `plot_results.py` generates the report figures from the CSV.

External sort expects CSV columns `timestamp,amount,merchant,id`, with a header. It budgets chunks using estimated Python object sizes and limits merge fan-in, but this estimate is not a hard RSS cap. Measure peak memory with representative records before relying on it under a strict 512 MB limit. At 100M rows, runs and output reside on disk and multi-pass merging keeps file handles bounded.

See [report.md](report.md) for algorithms, complexity, memory and I/O analysis, experiment protocol, and recommendations.

The rendered 15-page paper is `../R236699C LAB 2.pdf`. The 10-slide presentation is `../R236699C LAB 2 Presentation.pptx`, with a speaking outline in [speaker_notes.md](speaker_notes.md).
