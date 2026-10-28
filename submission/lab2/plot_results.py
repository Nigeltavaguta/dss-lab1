"""Create log-log timing and comparison plots from benchmark CSV."""
import argparse,csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_results(source="output/benchmarks.csv",out_dir="output"):
    data=defaultdict(list)
    with open(source,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            data[(r["algorithm"],r["distribution"])].append((int(r["n"]),float(r["seconds"]),int(r["comparisons"])))
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    distributions=("random","sorted","reverse","nearly_sorted","adversarial")
    for dist in distributions:
        fig,axes=plt.subplots(1,2,figsize=(11,4.5))
        for (alg,d),rows in data.items():
            if d!=dist:continue
            rows=sorted(rows)
            for ax,index,label in ((axes[0],1,"Seconds"),(axes[1],2,"Key comparisons")):
                ax.plot([x[0] for x in rows],[x[index] for x in rows],marker="o",label=alg)
        for ax,label in zip(axes,("Seconds","Key comparisons")):
            ax.set_title(label); ax.set_xscale("log",base=2); ax.set_yscale("log"); ax.set_xlabel("Records (n)"); ax.grid(True,which="both",alpha=.25)
        axes[0].set_ylabel("Elapsed seconds"); axes[1].set_ylabel("Comparisons"); axes[1].legend(fontsize=8,loc="best")
        fig.suptitle(dist.replace("_"," ").title()+" input")
        fig.tight_layout(); fig.savefig(out/f"sorting_{dist}.png",dpi=180); plt.close(fig)
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--csv",default="output/benchmarks.csv"); p.add_argument("--out",default="output"); a=p.parse_args(); plot_results(a.csv,a.out)
