"""Single command for the whole project: tests, experiments, then plots.

    python run_all.py           # full run (about 20 minutes)
    python run_all.py --quick   # smoke run with small sizes
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(*args):
    print("\n$ python " + " ".join(args))
    subprocess.run([sys.executable, *args], cwd=HERE, check=True)


if __name__ == "__main__":
    extra = ["--quick"] if "--quick" in sys.argv else []
    run("-m", "unittest", "discover", "-s", "tests")
    run(os.path.join("experiments", "benchmark.py"), *extra)
    run(os.path.join("experiments", "plot_results.py"))
