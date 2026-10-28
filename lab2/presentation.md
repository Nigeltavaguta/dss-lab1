% Lab 2: Sorting Under Real-World Constraints
% Nigel Tavaguta (R236699C)
% Design and Analysis of Algorithms

# The workload

- 100 million transaction records per day
- Sort by timestamp, amount, then merchant
- Memory limit: 512 MB
- Input is often partly sorted
- Need stable behavior and protection from adversarial inputs

**Question:** Which sorting design gives good performance without a quadratic worst case or exceeding memory?

---

# Algorithms compared

| Algorithm | Worst time | Extra space | Stable | Adaptive |
|---|---|---|---|---|
| Merge sort | O(n log n) | O(n) | Yes | No |
| Lomuto / Hoare quicksort | O(n²) | O(log n) typical | No | No |
| Heapsort | O(n log n) | O(1) | No | No |
| Built-in Timsort | O(n log n) | O(n) | Yes | Yes |
| Timsort-style / hybrid | O(n log n) | O(n) merge path | Merge path | Yes |

The benchmark also includes an in-place median-of-medians quicksort as a deterministic pivot defense.

---

# Hybrid design

1. Scan for ascending and descending natural runs.
2. Reverse strictly descending runs.
3. Return after a single run, or merge neighboring runs in linear passes.
4. If runs are highly fragmented, use introsort.
5. In introsort, use insertion sort for short ranges and heapsort after the depth limit.

This exploits existing order while bounding worst-case work by O(n log n).

---

# Adversarial quicksort

- Lomuto chooses the last record as pivot.
- On sorted or reverse-sorted input, it can split into sizes 0 and n−1.
- Recurrence: Q(n) = Q(n−1) + Θ(n) = Θ(n²).
- At n = 5,000: 12,497,500 key comparisons.
- Median-of-medians guarantees a constant-fraction split; introsort uses a heap fallback.

![Adversarial distribution benchmark](output/sorting_adversarial.png)

---

# Experimental method

- Five seeded inputs: random, sorted, reverse-sorted, nearly sorted, adversarial
- Eight algorithms through n = 5,000
- Six faster algorithms through n = 20,000
- Three timing repetitions, reported as the median
- Key comparisons counted in a separate run
- Every output checked against Python's stable sort

---

# Results at n = 5,000

| Algorithm | Random time (ms) | Sorted time (ms) | Random comparisons | Sorted comparisons |
|---|---:|---:|---:|---:|
| Lomuto quicksort | 17.29 | 3,551.95 | 68,052 | 12,497,500 |
| Hoare quicksort | 20.94 | 15.62 | 91,249 | 66,807 |
| Median-of-medians | 160.94 | 148.51 | 468,619 | 457,665 |
| Built-in Timsort | 2.55 | 1.95 | 54,928 | 4,999 |
| Educational Timsort-style | 25.10 | 1.96 | 56,642 | 5,000 |
| Hybrid | 23.64 | 1.82 | 83,311 | 5,000 |

The Lomuto count matches n(n−1)/2 exactly on sorted input. Built-in Timsort is fast because its sort is implemented in optimized C.

---

# Partial presortedness

Timsort and the hybrid detect natural runs and reduce work when the input is ordered. The educational version uses simple minrun and merge rules, so nearly sorted data costs more comparisons than the built-in implementation.

![Nearly sorted distribution benchmark](output/sorting_nearly_sorted.png)

At n = 20,000, built-in Timsort used 46,984 comparisons on nearly sorted data. The educational version used 185,276 and the hybrid used 183,812.

---

# External sorting for 100 million records

- 64 serialized bytes per record gives about 6.4 GB on disk.
- Sort chunks under a 128 MiB estimated Python-object budget.
- About 268,000 records per chunk at an estimated 500 bytes per row.
- Roughly 374 sorted runs, merged with fan-in 32.
- Run generation plus two merge levels gives about 6N/B block transfers.
- Estimated sequential read/write traffic: about 38.4 GB.

The byte budget estimates memory. Peak process memory still needs measurement on representative records to validate the 512 MB ceiling.

---

# Recommendation

- Use external merge sort when the full batch exceeds RAM.
- Use Timsort for stable in-memory Python sorting.
- Use the hybrid when custom control and adaptivity are needed.
- Avoid endpoint-pivot quicksort on untrusted or partly sorted feeds.
- Measure peak RSS and timing on representative production records.

**Takeaway:** asymptotic bounds identify the risks; measured constants, stability, input structure, and memory determine the production choice.

**References:** Cormen et al. (2022); Musser (1997); Blum et al. (1973); Aggarwal and Vitter (1988).
