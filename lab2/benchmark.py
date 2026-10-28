"""Benchmark each algorithm and save timings and checks to CSV."""
import argparse,csv,time
import statistics
from pathlib import Path
from datasets import generate,KINDS
import sorting
from sorting import ALGORITHMS,key

def run(out="output/benchmarks.csv", sizes=(500,2000,5000,8000), algorithms=None, repeats=3):
    path=Path(out); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(("algorithm","distribution","n","seconds","seconds_min","seconds_max","repeats","comparisons","correct"))
        for n in sizes:
            for kind in KINDS:
                original=generate(kind,n)
                expected=sorted(original,key=key)
                selected=ALGORITHMS if algorithms is None else {n:ALGORITHMS[n] for n in algorithms}
                for name,fn in selected.items():
                    elapsed_runs=[]; correct=True
                    for _ in range(repeats):
                        data=original.copy(); sorting.reset_comparisons(False)
                        start=time.perf_counter(); fn(data); elapsed_runs.append(time.perf_counter()-start)
                        correct=correct and data==expected
                    counted=original.copy(); sorting.reset_comparisons(True); fn(counted)
                    comparisons=sorting.COMPARISONS; sorting.reset_comparisons(False)
                    w.writerow((name,kind,n,f"{statistics.median(elapsed_runs):.8f}",f"{min(elapsed_runs):.8f}",f"{max(elapsed_runs):.8f}",repeats,comparisons,correct and counted==expected))
    return path

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--sizes",nargs="+",type=int,default=[500,2000,5000,8000]); p.add_argument("--algorithms",nargs="+",choices=ALGORITHMS); p.add_argument("--repeats",type=int,default=3); p.add_argument("--out",default="output/benchmarks.csv"); args=p.parse_args(); run(args.out,args.sizes,args.algorithms,args.repeats)
