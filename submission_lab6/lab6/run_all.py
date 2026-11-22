"""Reproduce all Lab 6 results and figures with one command."""

import benchmark
import plot_results


if __name__ == "__main__":
    benchmark.run_all()
    plot_results.make_plots()
