import benchmark
import plot_results

if __name__ == "__main__":
    benchmark.bench_vertex_cover()
    benchmark.bench_fptas()
    benchmark.bench_tsp()
    plot_results.plot_vertex_cover()
    plot_results.plot_fptas()
    plot_results.plot_tsp()
