# Lab 6: Monte Carlo Simulation and Randomized Algorithms

## Run

Requires Python 3.12 or later and Matplotlib 3.8 or later.

```powershell
python -m pip install matplotlib
python run_all.py
```

The command regenerates all CSV tables and PNG figures in `output/`. Fixed random seeds make the experiments reproducible. Change the seeds or sample sizes in `benchmark.py` for additional runs. Random seeds are for repeatable experiments and are not cryptographic randomness.

## Files

| File | Purpose |
|---|---|
| `randomized.py` | Randomized Quicksort, Miller–Rabin, Karger contraction, and Karger repetition bounds. |
| `simulation.py` | Monte Carlo integration, M/M/1 simulation, Gaussian rare-event importance sampling, and variance reduction. |
| `benchmark.py` | Runs the experiments and writes CSV result tables. |
| `plot_results.py` | Builds the convergence, comparison, and variance reduction plots. |
| `run_all.py` | Runs the full pipeline with one command. |
| `build_pdf.py` | Typesets report equations and builds the PDF with Pandoc and WeasyPrint. |
| `report.md` | Full technical report and interpretation of the generated results. |
| `presentation.md` | Eight-slide outline for the 10-minute oral presentation and Q&A. |

## Scope of the experiments

The portfolio-loss model is a deliberately simple normal model for demonstrating importance sampling. It estimates a net loss above $1 million for a model with mean $400,000 and standard deviation $150,000. It is not a calibrated financial risk model. The M/M/1 queue assumes independent exponential interarrival and service times and a stable system with arrival rate below service rate. The Karger experiment uses a small graph with a known cut so that success can be measured directly.

## Build the PDF

Run `python build_pdf.py` from this folder. It requires Matplotlib, Pandoc, and WeasyPrint. Pandoc's WeasyPrint PDF backend does not typeset TeX equations directly, so the script renders the report's math expressions as embedded images before building the PDF. It recreates the equation images in `output/pdf_math/`.
