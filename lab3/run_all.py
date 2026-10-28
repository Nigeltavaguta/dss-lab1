import benchmark
import plot_results

if __name__ == "__main__":
    benchmark.bench_knapsack()
    benchmark.bench_coin_change()
    benchmark.bench_tsp()
    plot_results.plot_knapsack()
    plot_results.plot_coin_change()
    plot_results.plot_tsp()
