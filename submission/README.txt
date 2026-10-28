Lab 2 submission package

Contents
- R236699C LAB 2.pdf: technical report
- lab2/: Python source code, report source, benchmark result CSVs, and plots
- lab2/input.csv and lab2/sorted.csv: sample data and output supporting the external-sort memory measurement in the report

The Python source uses the standard library. Matplotlib is needed only to regenerate plots.
Run the benchmark from the lab2 folder with:
  python benchmark.py --sizes 500 2000 5000 --repeats 3

Run the external sorter from the lab2 folder with:
  python external_sort.py input.csv sorted.csv --chunk-mib 128 --fan-in 32
