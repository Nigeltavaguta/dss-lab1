# Lab 1 - Empirical Validation of the Master Theorem and Recurrence Solving

## Requirements

- Python 3 (tested with Python 3.12.0)
- matplotlib (tested with 3.11.2): `pip install matplotlib`

## Run

Everything runs with one command:

```
python run_all.py
```

Takes about 40 seconds. All CSVs and plots are written to `output/` (created automatically).
Operation counts are reproducible (`task4.py` seeds the random generator with 42).
Wall-clock times will differ from run to run and between machines.

## Files

| File | What it does | Output |
|---|---|---|
| `task2_task3.py` | Simulates the four recurrences directly (a recursive function that makes `a` calls on `n/b` and adds `f(n)`), for n = 2^1 to 2^20. Memoized by `n`, since only about 20 distinct sizes occur. Matches the Task 1 closed forms exactly, so it checks the proofs rather than measuring anything real. | `recurrence_counts.csv`, `recurrence_{1..4}.png`, `g_ratio_{1..4}.png` |
| `task4.py` | Real algorithms with no memoization: merge sort (R1), a brute-force O(n^2) combine step (R2), pre-Karatsuba recursive multiplication (R3), recursive binary search (R4). Shows where real results deviate from theory. R2 is capped at n = 2^12 and R3 at 1024-bit operands, because they do genuine quadratic-scale work. | `real_implementations.csv`, `real_r{1..4}.png` |
| `run_all.py` | Calls both scripts' `run()` functions in order. | |

## Report

The report is `../R236699C LAB 1.md` (PDF: `../R236699C LAB 1.pdf`), one level up from this
folder. It covers the analytical solutions and induction proofs (Task 1), the methodology
and plots (Tasks 2 and 3), the critical analysis (Task 4), and the modified recurrence
(Task 5).
