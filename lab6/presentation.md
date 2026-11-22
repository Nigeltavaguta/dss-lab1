# Lab 6 presentation outline

Target length: about 10 minutes, followed by questions.

## Slide 1: Why randomization helps

- Risk analysis asks for estimates, not always exact answers.
- Randomized algorithms trade certainty on one run for useful expected behavior or bounded error.
- Experiments use fixed seeds so the tables can be reproduced.

Speaking time: 1 minute.

## Slide 2: Three randomized algorithms

- Randomized Quicksort chooses a pivot uniformly.
- Miller–Rabin rejects composites with a one-sided error bound.
- Karger contracts random edges and repeats to find a minimum cut.

Speaking time: 1 minute.

## Slide 3: Quicksort and primality results

- Across sizes 100 to 2,000, average comparisons track (2(n+1)H_n-4n).
- The selected prime and composite cases were classified correctly.
- Miller–Rabin’s false-prime bound after 20 rounds is (4^{-20}).

Speaking time: 1.5 minutes.

## Slide 4: Karger’s Min-Cut

- The test graph has a known minimum cut of three.
- Out of 5,000 runs, 760 found that cut.
- Observed success was 15.2%, above the general lower bound of 2.22%.
- The theory says 205 repetitions suffice for a 99% success guarantee on a 10-vertex graph.

Speaking time: 1 minute.

## Slide 5: Estimating π and simulating a queue

- The π estimate becomes more precise with more samples, but does not improve every time.
- Wilson intervals show uncertainty for the hit proportion.
- The M/M/1 simulation approaches the analytical mean time of five time units.

Speaking time: 1.5 minutes.

## Slide 6: A rare loss and importance sampling

- The example estimates a net loss above $1 million under a simple normal model, with mean $400,000 and standard deviation $150,000.
- Crude Monte Carlo saw 14 exceedances in 500,000 samples.
- Importance sampling gave about 5,700 times lower sample variance at the same sample count.
- This example is methodological and is not a production risk estimate.

Speaking time: 1.5 minutes.

## Slide 7: Variance reduction and 5D integration

- Antithetic variates and a known-mean control each reduced variance by about 61 times.
- In five dimensions, 100,000-sample Monte Carlo had error about 0.012.
- The tensor midpoint rule needed 248,832 grid evaluations to reduce error to about 0.022.
- Tensor grids become expensive as dimension increases.

Speaking time: 1.5 minutes.

## Slide 8: Takeaways and limitations

- Theory predicts averages and guarantees, not the result of every run.
- Confidence intervals and repeated seeds help describe simulation uncertainty.
- Importance sampling and control variates help when their assumptions fit the problem.
- Ask questions about the normal loss assumption, batch means, and Karger’s repetition bound.

Speaking time: 1 minute, then Q&A.
