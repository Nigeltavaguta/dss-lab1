Lab 5 submission package

Contents
- R236699C LAB 5.pdf: technical report
- lab5/: Python source code, report source, benchmark result CSVs, and plots

The Python source uses the standard library plus matplotlib (for plot_results.py).
Run everything from the lab5 folder with:
  python run_all.py

This regenerates every CSV and plot in lab5/output/ used by the report. Takes a few
seconds (the exact Vertex Cover branch-and-bound at n=19-20 is the slowest single step).
