# Exam Timetabling Engine (ETE)

Design and Analysis of Algorithms project: NP-hard scheduling engine for university exam timetabling.
HCS301, Group 11.

| Name | Registration number | Role |
|---|---|---|
| Nigel Tavaguta | R236699C | B&B Engineer |
| Malvine Marevere | R231556W | CSP Modeller |
| Claudy Gonyora | R231542E | Backtracking Engineer |
| Nashel Mashumba | R231524V | Evaluation Lead |
| Tanaka Gutsire | R204569J | Documentation Lead |

The engine schedules exams into time slots and venues so that:

- no student group sits two exams at once;
- no lecturer has two exams at once;
- every exam is in a slot when its lecturer is available;
- every exam gets its own venue that is large enough.

It then minimises the number of slots.
It models the problem as a constraint satisfaction problem built on a graph-colouring core and solves it with five algorithms.

## Requirements

- Python 3.10+ (tested with Python 3.12.0)
- matplotlib (tested with 3.11.2), for the plots only: `pip install matplotlib`

The solvers, tests and statistics use only the Python standard library.

## Run everything (single command)

```
python run_all.py
```

This runs the unit tests, every experiment and the plotting script. It writes the CSV files and figures to `output/`. The full run takes about 20 minutes, mostly because of the fixed time budgets given to the exact and hybrid solvers. `python run_all.py --quick` does a smaller smoke run.

Other entry points:

```
python -m unittest discover -s tests -v     # 22 unit and edge-case tests
python experiments/benchmark.py [--quick]   # experiments only
python experiments/plot_results.py          # figures from existing CSVs
python report/build_pdf.py                  # report PDF (pandoc + Chrome/Edge, internet for KaTeX)
cd report && pandoc slides.md -o slides.pptx   # presentation (.pptx with speaker notes)
```

## Layout

| Path | Contents |
|---|---|
| `ete/model.py` | Exams, venues, lecturers, student groups. Builds the conflict graph, checks venue feasibility (sorted matching), validates timetables, assigns rooms. |
| `ete/generators.py` | Random `G(n, p)` instances, UZ-inspired instances (faculties, Part 1-4 cohorts, service courses, electives, carry-overs, lecturer unavailability, mixed venues) and crown graphs. |
| `ete/bounds.py` | Clique lower bound (greedy clique) and venue lower bound. |
| `ete/backtracking.py` | Naive backtracking and backtracking with forward checking, MRV, the degree heuristic and MAC (each can be switched on or off). |
| `ete/branch_bound.py` | Branch-and-bound for the minimum number of slots: DSATUR-style branching, incumbent bound, LB stop, symmetry breaking. |
| `ete/greedy.py` | Greedy colouring: natural, random, Welsh-Powell (largest first) and DSATUR orders. |
| `ete/local_search.py` | TabuCol tabu search that removes slots one at a time; venue overflow is a soft penalty. |
| `ete/hybrid.py` | Hybrid: greedy, then tabu, then B&B seeded with the tabu timetable and polishing each new incumbent with tabu. |
| `ete/reductions.py` | 3-SAT to 3-colouring (OR gadgets) and colouring to timetabling, with decoding and a constructive encoder. |
| `ete/stats.py` | t confidence intervals, bootstrap CIs, Wilcoxon signed-rank test (exact for small n). |
| `experiments/benchmark.py` | Experiments E1-E7 and the statistics tables. |
| `experiments/plot_results.py` | Figures. |
| `tests/test_ete.py` | Unit tests: model, bounds, every solver against brute force, reductions, edge cases. |
| `report/` | Report source (`report.md`), PDF builder (`build_pdf.py`) and slides source (`slides.md`). |
| `output/` | Generated CSV files and PNG figures. |

## Experiments

| ID | Question | Output |
|---|---|---|
| E1 | How many nodes does each pruning technique save? | `e1_pruning.csv`, `e1_pruning.png` |
| E2 | How do time and quality scale from n = 10 to 500? | `e2_scaling.csv`, `e2_summary.csv`, `e2_time.png`, `e2_gap.png` |
| E3 | How far is greedy from optimal, and what is its worst case? | `e3_*.csv`, `e3_crown.png`, `e3_ratio.png` |
| E4 | What do the lower and upper bounds contribute to B&B? | `e4_bnb_ablation.csv`, `e4_bnb.png` |
| E5 | How does the best timetable improve over time? | `e5_trace.csv`, `e5_trace.png` |
| E6 | Does the 3-SAT reduction behave as the proof says? | `e6_reduction.csv` |
| E7 | A full 500-exam UZ-inspired timetable with rooms | `e7_timetable.csv`, `e7_summary.csv` |
| - | Confidence intervals and Wilcoxon tests | `stats_tests.csv` |

All randomness uses fixed seeds, so the slot counts and node counts are repeatable. Times depend on the machine.

## Using the engine on your own data

```python
from ete.model import Exam, Venue, Lecturer, StudentGroup, Instance, assign_venues
from ete.hybrid import hybrid

exams = [Exam(0, "HCS201", 120, lecturer=0), Exam(1, "HCS202", 80, lecturer=1),
         Exam(2, "HMA201", 300, lecturer=2)]
venues = [Venue(0, "Hall 1", 400), Venue(1, "LT 2", 150)]
lecturers = [Lecturer(0, "L0"), Lecturer(1, "L1", unavailable=frozenset({0})),
             Lecturer(2, "L2")]
groups = [StudentGroup(0, "HCS Part 2", 80, (0, 1, 2))]
inst = Instance(exams, num_slots=6, venues=venues, lecturers=lecturers, groups=groups)

result = hybrid(inst, time_limit=5)
print(result.slots, result.optimal, result.assignment, assign_venues(inst, result.assignment))
```

## Peer evaluation

Each member completes the Word form `GROUP 11 PEER EVALUATION FORM.docx` (submitted with the report, not kept in the repository) and hands it in separately, as the brief requires.

## Limitations

The UZ-inspired data is synthetic. Its structure follows a university exam session, but no real UZ enrolment data was used. An exam occupies exactly one venue, and a venue hosts one exam per session. The real UZ Block 4 timetable seats several papers in one venue (up to 16 in the Great Hall), so the engine's session counts are conservative for UZ practice (report Section 9.8). Soft constraints, such as spreading a student's exams across days, are measured but not optimised.
