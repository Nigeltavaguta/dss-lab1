# Speaker notes for the 10-minute presentation

## Slide 1: Title, about 20 seconds

Introduce the lab as an algorithm engineering study. The central question is not just which method has the best asymptotic order, but which one is safe and practical for a fintech batch with presorted inputs and a strict memory cap.

## Slide 2: Workload, about 60 seconds

Explain the composite ordering. Timestamp is the first key, amount breaks timestamp ties, and merchant breaks the remaining ties. A production pipeline must also decide how to normalize merchant names and how to treat malformed fields. The 100 million record size makes RAM a first-order constraint, not a minor implementation detail.

## Slide 3: Algorithms, about 60 seconds

Compare guarantees and tradeoffs. Merge sort is stable but needs linear extra memory. Heapsort has a hard O(n log n) bound and constant extra space but is not stable. Quicksort is often fast, but simple pivot rules can be attacked. Timsort combines stability with adaptivity and is the production Python reference.

## Slide 4: Hybrid, about 70 seconds

Walk through the run scan, reversal of strictly descending runs, and early return for a single run. Explain that natural runs are merged linearly. When the input has many short runs, introsort protects against poor partitions. Insertion sort handles tiny ranges, and heapsort takes over after the depth limit.

## Slide 5: Adversary, about 70 seconds

For Lomuto with the last element as pivot, sorted data places the pivot at one extreme. The remaining range shrinks by one each time, so the comparison count is triangular and quadratic. Median-of-medians selects pivots with a guaranteed balance. Introsort instead caps the damage with a heap fallback, which is simpler for a practical hybrid.

## Slide 6: Method, about 50 seconds

Describe the five deterministic input generators. Timings are the median of three runs. Comparison counts are taken separately so instrumentation does not distort time. These are small algorithm comparison datasets, not a full-scale test of 100 million records.

## Slide 7: Results, about 80 seconds

Focus on the sorted Lomuto result. It performs over 12 million comparisons at n=5,000 and takes more than 3.5 seconds in this Python implementation. The other algorithms remain near their expected n log n growth. Built-in Timsort's time is especially low because it runs in optimized C, so compare operation counts as well as absolute time.

## Slide 8: Presortedness, about 60 seconds

Explain why the built-in Timsort and custom hybrid benefit from monotone runs. The educational implementation is correct but less refined on nearly sorted data because its minrun and merge policy are simpler. This illustrates the gap between implementing a design idea and matching a production runtime's tuning.

## Slide 9: External sort, about 80 seconds

The serialized input is already several gigabytes. The Python implementation writes sorted runs to disk and merges no more than 32 at once. With around 374 runs, two merge levels follow initial run generation. That is three read/write passes, or roughly 38.4 GB of I/O under the 64-byte record assumption. The 128 MiB setting is an estimate, so production requires peak RSS measurement with realistic maximum-length records.

## Slide 10: Recommendation, about 60 seconds

Close with a workload-based choice. Use external merge sort for batches that exceed available RAM, Timsort when stable in-memory sorting is enough, and the hybrid when the algorithm itself must be controlled. Do not expose endpoint-pivot quicksort to untrusted or presorted data. State that the most important production follow-up is a measured memory test and representative full-scale benchmark.
