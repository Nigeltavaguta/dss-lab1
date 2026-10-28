"""Bounded-memory external merge sort for newline-delimited CSV transactions.

Input columns: timestamp,amount,merchant,id. Uses temporary sorted runs and a
k-way merge; memory is bounded by chunk size plus one current row per run.
"""
import argparse,csv,heapq,sys,tempfile
from contextlib import ExitStack
from pathlib import Path

def row_key(row): return (int(row[0]),int(row[1]),row[2],int(row[3]))

def _estimated_row_bytes(row):
    # Include parsed row storage, sort keys and temporary sort references with slack.
    return sys.getsizeof(row)+sum(sys.getsizeof(field) for field in row)+160

def _write_run(rows,path):
    rows.sort(key=row_key)
    with path.open("w",newline="",encoding="utf-8") as out:
        csv.writer(out).writerows(rows)

def _merge_runs(paths,destination):
    with ExitStack() as stack:
        readers=[csv.reader(stack.enter_context(p.open(newline="",encoding="utf-8"))) for p in paths]
        heap=[]
        for ix,reader in enumerate(readers):
            row=next(reader,None)
            if row is not None:heapq.heappush(heap,(row_key(row),ix,row))
        with destination.open("w",newline="",encoding="utf-8") as out:
            writer=csv.writer(out)
            while heap:
                _,ix,row=heapq.heappop(heap);writer.writerow(row)
                nxt=next(readers[ix],None)
                if nxt is not None:heapq.heappush(heap,(row_key(nxt),ix,nxt))

def external_sort(source,destination,chunk_records=None,chunk_budget_bytes=128*1024*1024,fan_in=32,temp_dir=None):
    if fan_in<2:raise ValueError("fan_in must be at least 2")
    if chunk_budget_bytes<1024:raise ValueError("chunk_budget_bytes is too small")
    source,destination=Path(source),Path(destination); destination.parent.mkdir(parents=True,exist_ok=True); runs=[]
    with tempfile.TemporaryDirectory(dir=temp_dir) as td:
        with source.open(newline="",encoding="utf-8") as inp:
            reader=csv.reader(inp); header=next(reader,None)
            chunk=[]; estimated=0
            for row in reader:
                row_bytes=_estimated_row_bytes(row)
                if chunk and (estimated+row_bytes>chunk_budget_bytes or (chunk_records and len(chunk)>=chunk_records)):
                    run=Path(td)/f"run{len(runs)}.csv";_write_run(chunk,run);runs.append(run);chunk=[];estimated=0
                chunk.append(row);estimated+=row_bytes
            if chunk:
                run=Path(td)/f"run{len(runs)}.csv";_write_run(chunk,run);runs.append(run)
        # Bound open files and merge-head memory with multi-pass fan-in.
        pass_no=0
        while len(runs)>fan_in:
            next_runs=[]
            for start in range(0,len(runs),fan_in):
                group=runs[start:start+fan_in]
                if len(group)==1:next_runs.append(group[0]);continue
                merged=Path(td)/f"merge{pass_no}_{len(next_runs)}.csv";_merge_runs(group,merged);next_runs.append(merged)
            runs=next_runs;pass_no+=1
        with destination.open("w",newline="",encoding="utf-8") as out:
            writer=csv.writer(out)
            if header is not None: writer.writerow(header)
        if runs:
            # Write final merge after header, streaming through a temporary final file.
            final=Path(td)/"final.csv";_merge_runs(runs,final)
            with final.open(newline="",encoding="utf-8") as inp, destination.open("a",newline="",encoding="utf-8") as out:
                for block in iter(lambda:inp.read(1024*1024),""):out.write(block)
    return destination

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("source"); p.add_argument("destination"); p.add_argument("--chunk-mib",type=int,default=128); p.add_argument("--chunk-records",type=int); p.add_argument("--fan-in",type=int,default=32); a=p.parse_args(); external_sort(a.source,a.destination,a.chunk_records,a.chunk_mib*1024*1024,a.fan_in)
