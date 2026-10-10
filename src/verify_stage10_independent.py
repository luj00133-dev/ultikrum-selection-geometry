"""Independent standard-library verifier for the frozen Stage 10 grid."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"configs"/"stage10_cifar10_early_replication.json"
PROCESSED=ROOT/"results"/"processed"/"stage10_cifar10_early_replication"
EPOCH=re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)",re.MULTILINE)
TRAIN=[2026,2027,2028]; SYSTEM=[91001,91002,91003]; DIST=["euclidean","normalized_euclidean","cosine"]
WINDOWS={"primary_2-29":(2,29),"secondary_30-59":(30,59)}

def read_rows(path:Path):
    with path.open(encoding="utf-8-sig",newline="") as handle: return list(csv.DictReader(handle))

def digest(path:Path)->str:
    value=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""): value.update(chunk)
    return value.hexdigest()

def close(a:float,b:float,tol:float=1e-10)->bool: return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol

def main()->None:
    config=json.loads(CONFIG.read_text(encoding="utf-8")); manifest=read_rows(ROOT/config["paths"]["manifest"])
    expected={(t,s,d) for t in TRAIN for s in SYSTEM for d in DIST}; keys={(int(x["train_seed"]),int(x["system_seed"]),x["distance"]) for x in manifest}
    if len(manifest)!=27 or keys!=expected: raise SystemExit("independent manifest grid failed")
    main_rows={(int(x["train_seed"]),int(x["system_seed"]),x["distance"],x["window"]):x for x in read_rows(PROCESSED/"crossed_metrics.csv")}
    if len(main_rows)!=54: raise SystemExit("main crossed table coverage failed")
    main_hash={(x["run_id"],x["artifact"]):x["sha256"] for x in read_rows(PROCESSED/"raw_sha256.csv")}
    recomputed={}; learning={}; maximum_error=0.0
    for row in manifest:
        output=Path(row["output"]); system_log=Path(row["system_log"]); resolved_path=Path(row["resolved_config"])
        text=output.read_text(encoding="utf-8",errors="replace"); epochs=[(int(a),float(b)) for a,b in EPOCH.findall(text)]
        if "Training finished on" not in text or [x[0] for x in epochs]!=list(range(60)): raise SystemExit(f"epoch coverage failed: {row['run_id']}")
        resolved=json.loads(resolved_path.read_text(encoding="utf-8")); expected_config=(60,int(row["partition_seed"]),int(row["train_seed"]),int(row["system_seed"]),"CIFAR10","simplecnn",row["vendor_aggregator"])
        actual=(resolved.get("epochs"),resolved.get("seed_partition"),resolved.get("seed_train"),resolved.get("system_seed"),resolved.get("dataset"),resolved.get("model"),resolved.get("defense"))
        if actual!=expected_config: raise SystemExit(f"resolved config failed: {row['run_id']}")
        for artifact,path in (("output",output),("system_log",system_log),("resolved_config",resolved_path)):
            if main_hash.get((row["run_id"],artifact))!=digest(path): raise SystemExit(f"hash mismatch: {row['run_id']} {artifact}")
        acc=[x[1] for x in epochs]; first=sum(acc[:10])/10; last=sum(acc[-10:])/10; gain=last-first
        learning[(int(row["train_seed"]),int(row["system_seed"]),row["distance"])]=last>=0.15 and gain>=0.03
        counts=defaultdict(lambda:[0,set()]); aggregates=defaultdict(lambda:[0,0,0.0,0.0])
        with system_log.open(encoding="utf-8-sig",newline="") as handle:
            for item in csv.DictReader(handle):
                rnd=int(item["round"]); cid=int(item["client_id"]); counts[rnd][0]+=1; counts[rnd][1].add(cid)
                if item["resource_group"] not in ("strong","straggler"): continue
                for name,(start,end) in WINDOWS.items():
                    if start<=rnd<=end:
                        bucket=aggregates[(name,item["resource_group"])]; bucket[0]+=int(item["selected"]); bucket[1]+=1; bucket[2]+=float(item["norm_ratio"]); bucket[3]+=float(item["aggregator_score"])
        if set(counts)!=set(range(60)) or any(v[0]!=50 or len(v[1])!=50 for v in counts.values()): raise SystemExit(f"client-round coverage failed: {row['run_id']}")
        key0=(int(row["train_seed"]),int(row["system_seed"]),row["distance"])
        for name in WINDOWS:
            strong=aggregates[(name,"strong")]; slow=aggregates[(name,"straggler")]
            values={"selection_disparity_pp":100*(slow[0]/slow[1]-strong[0]/strong[1]),"norm_ratio_gap":slow[2]/slow[1]-strong[2]/strong[1],"score_gap":slow[3]/slow[1]-strong[3]/strong[1]}
            recomputed[key0+(name,)]=values; main=main_rows[key0+(name,)]
            for column,value in values.items():
                error=abs(value-float(main[column])); maximum_error=max(maximum_error,error)
                if not close(value,float(main[column])): raise SystemExit(f"numeric mismatch: {key0} {name} {column}")
    all_learning=all(learning.values()); primary={(t,s,d):recomputed[(t,s,d,"primary_2-29")]["selection_disparity_pp"] for t in TRAIN for s in SYSTEM for d in DIST}
    crossed_eu=sum(primary[(t,s,"euclidean")] for t in TRAIN for s in SYSTEM)/9
    eu_system={s:sum(primary[(t,s,"euclidean")] for t in TRAIN)/3 for s in SYSTEM}
    controls={d:{s:sum(primary[(t,s,d)]-primary[(t,s,"euclidean")] for t in TRAIN)/3 for s in SYSTEM} for d in DIST[1:]}
    gate_parts={"all_learning_gates_passed":all_learning,"crossed_euclidean_at_least_5pp":crossed_eu>=5.0,"euclidean_positive_each_system_seed":all(eu_system[s]>0 for s in SYSTEM),"both_controls_negative_each_system_seed":all(controls[d][s]<0 for d in DIST[1:] for s in SYSTEM)}
    transfer=all(gate_parts.values())
    main_analysis=json.loads((PROCESSED/"analysis.json").read_text(encoding="utf-8"))
    if main_analysis["transfer_gate_pass"]!=transfer or not close(main_analysis["crossed_euclidean_disparity_pp"],crossed_eu): raise SystemExit("main decision mismatch")
    result={"status":"passed","verified_cells":27,"verified_cell_windows":54,"max_absolute_error":maximum_error,"all_learning_gates_passed":all_learning,"gate_parts":gate_parts,"transfer_gate_pass":transfer}
    (PROCESSED/"independent_verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))

if __name__=="__main__": main()
