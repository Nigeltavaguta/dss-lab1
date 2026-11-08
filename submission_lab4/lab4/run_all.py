import benchmark
import plot_results

if __name__ == "__main__":
    benchmark.bench_pruning()
    benchmark.bench_exact_vs_greedy()
    benchmark.bench_timetabling()
    benchmark.bench_worst_case()
    benchmark.bench_greedy_order()
    plot_results.plot_pruning()
    plot_results.plot_exact_vs_greedy()
    plot_results.plot_quality_vs_time()
    plot_results.plot_worst_case()
    plot_results.plot_greedy_order()
