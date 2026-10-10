"""Independently recompute all Stage 9 trajectory bins from raw CSV files."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"configs"/"stage9_system_seed_converged.json"
DERIVED=ROOT/"results"/"processed"/"stage9_time_resolved"/"trajectory_bins.csv"
OUTPUT=ROOT/"results"/"processed"/"stage9_time_resolved"/"independent_verification.json"


def read(path):
    with Path(path).open(encoding="utf-8",newline="") as handle: return list(csv.DictReader(handle))


def bin_name(r):
    if r<2:return None
    if r<10:return ("2-9",2,9,5.5)
    s=(r//10)*10;return (f"{s}-{s+9}",s,s+9,s+4.5)


def main():
    cfg=json.loads(CONFIG.read_text(encoding="utf-8")); old=[x for x in read(ROOT/cfg["paths"]["stage8_manifest"]) if int(x["train_seed"]) in (2026,2027,2028)]; new=read(ROOT/cfg["paths"]["manifest"]); manifest=old+new
    if len(manifest)!=27: raise SystemExit("expected 27 raw cells")
    recomputed={}
    for row in manifest:
        acc=defaultdict(lambda:defaultdict(lambda:[0.0,0.0,0.0,0]))
        with Path(row["system_log"]).open(encoding="utf-8-sig",newline="") as handle:
            count=0
            for item in csv.DictReader(handle):
                count+=1; r=int(item["round"]); spec=bin_name(r)
                if spec is None or item["resource_group"] not in ("strong","straggler"): continue
                bucket=acc[spec][item["resource_group"]]; bucket[0]+=float(item["selected"]);bucket[1]+=float(item["norm_ratio"]);bucket[2]+=float(item["aggregator_score"]);bucket[3]+=1
        if count!=15000 or len(acc)!=30: raise SystemExit(f"raw coverage failed: {row['run_id']}")
        for spec,groups in acc.items():
            if set(groups)!={"strong","straggler"}: raise SystemExit(f"group coverage failed: {row['run_id']}")
            s=groups["strong"];t=groups["straggler"]
            key=(int(row["train_seed"]),int(row["system_seed"]),row["distance"],spec[0])
            recomputed[key]=(100*(t[0]/t[3]-s[0]/s[3]),t[1]/t[3]-s[1]/s[3],t[2]/t[3]-s[2]/s[3])
    derived=read(DERIVED)
    if len(derived)!=810 or len(recomputed)!=810: raise SystemExit("trajectory row-count mismatch")
    max_error=0.0
    for row in derived:
        key=(int(row["train_seed"]),int(row["system_seed"]),row["distance"],row["bin"])
        expected=recomputed.get(key)
        if expected is None: raise SystemExit(f"missing derived key: {key}")
        actual=(float(row["selection_disparity_pp"]),float(row["norm_ratio_gap"]),float(row["score_gap"]))
        max_error=max(max_error,max(abs(a-b) for a,b in zip(actual,expected)))
    if max_error>1e-10: raise SystemExit(f"trajectory numerical mismatch: {max_error}")
    result={"status":"passed","raw_cells":27,"verified_cell_bin_rows":810,"max_absolute_error":max_error}
    OUTPUT.write_text(json.dumps(result,indent=2),encoding="utf-8");print(json.dumps(result,indent=2))


if __name__=="__main__":main()
