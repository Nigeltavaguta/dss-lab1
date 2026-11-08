Lab 4 submission package

Contents
- R236699C LAB 4.pdf: technical report
- lab4/: Python source code, report source, benchmark result CSVs, and plots

The Python source uses the standard library plus matplotlib (for plot_results.py).
Run everything from the lab4 folder with:
  python run_all.py

This regenerates every CSV and plot in lab4/output/ used by the report. Takes about
20 seconds (the dense-graph worst-case sweep up to n=35 is the slow part, by design -
see Section 6.2 of the report).
