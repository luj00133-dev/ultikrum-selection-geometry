"""Read-only progress and integrity audit for the frozen Stage 10 queue."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EPOCH=re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)",re.MULTILINE)
REQUIRED={"round","client_id","selected"}

def rows(path:Path):
    with path.open(encoding="utf-8-sig",newline="") as handle:return list(csv.DictReader(handle))

def digest(path:Path)->str:
    value=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):value.update(chunk)
    return value.hexdigest()

def audit(row:dict[str,str])->dict:
    output=Path(row["output"]); system=Path(row["system_log"]); resolved=Path(row["resolved_config"])
    result={"run_id":row["run_id"],"train_seed":int(row["train_seed"]),"system_seed":int(row["system_seed"]),"distance":row["distance"],"state":"missing","last_epoch":None,"issues":[]}
    existing=[path.is_file() and path.stat().st_size>0 for path in (output,system,resolved)]
    if not any(existing):return result
    result["state"]="partial"
    text=output.read_text(encoding="utf-8",errors="replace") if output.is_file() else ""; epochs=[(int(a),float(b)) for a,b in EPOCH.findall(text)]
    if epochs:
        result["last_epoch"]=epochs[-1][0]
        if [x[0] for x in epochs]!=list(range(len(epochs))):result["issues"].append("noncontiguous_epochs")
    complete_marker="Training finished on" in text
    if complete_marker and len(epochs)!=60:result["issues"].append("completion_marker_without_60_epochs")
    if resolved.is_file():
        try:
            cfg=json.loads(resolved.read_text(encoding="utf-8")); expected={"epochs":60,"seed_partition":int(row["partition_seed"]),"seed_train":int(row["train_seed"]),"system_seed":int(row["system_seed"]),"dataset":"CIFAR10","model":"simplecnn","distribution":"non-iid","dirichlet_alpha":0.5,"attack":"NoAttack","defense":row["vendor_aggregator"],"system_profile":"four_tier","num_clients":50}
            mismatch=[key for key,value in expected.items() if cfg.get(key)!=value]
            if mismatch:result["issues"].append("resolved_mismatch:"+",".join(mismatch))
        except Exception as exc:result["issues"].append("invalid_resolved_json:"+type(exc).__name__)
    elif complete_marker:result["issues"].append("missing_resolved_config")
    system_rows=[]
    if system.is_file():
        try:system_rows=rows(system)
        except Exception as exc:result["issues"].append("invalid_system_csv:"+type(exc).__name__)
    elif complete_marker:result["issues"].append("missing_system_log")
    result["system_rows"]=len(system_rows)
    if system_rows:
        if not REQUIRED.issubset(system_rows[0]):result["issues"].append("missing_system_columns")
        else:
            coverage=defaultdict(lambda:[0,set(),0])
            for item in system_rows:
                rnd=int(item["round"]);coverage[rnd][0]+=1;coverage[rnd][1].add(int(item["client_id"]));coverage[rnd][2]+=int(item["selected"])
            result["system_rounds"]=len(coverage)
            if complete_marker:
                if set(coverage)!=set(range(60)):result["issues"].append("system_round_coverage")
                if any(value[0]!=50 or len(value[1])!=50 for value in coverage.values()):result["issues"].append("client_coverage")
                if any(value[2]!=38 for value in coverage.values()):result["issues"].append("selection_cardinality")
    if complete_marker and len(epochs)==60 and len(system_rows)==3000 and all(existing) and not result["issues"]:
        first=sum(x[1] for x in epochs[:10])/10;last=sum(x[1] for x in epochs[-10:])/10;gain=last-first
        result.update({"state":"complete","first10_accuracy":first,"last10_accuracy":last,"accuracy_gain":gain,"learning_pass":last>=0.15 and gain>=0.03,"sha256":{"output":digest(output),"system_log":digest(system),"resolved_config":digest(resolved)}})
    elif complete_marker or result["issues"]:result["state"]="invalid"
    return result

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--project-root",default=str(ROOT));parser.add_argument("--config",default="configs/stage10_cifar10_early_replication.json");parser.add_argument("--out");args=parser.parse_args()
    root=Path(args.project_root).resolve();config=json.loads((root/args.config).read_text(encoding="utf-8"));manifest_path=root/config["paths"]["manifest"];manifest=rows(manifest_path)
    if len(manifest)!=27:raise SystemExit(f"expected 27 manifest rows, got {len(manifest)}")
    cells=[audit(row) for row in manifest];counts=Counter(item["state"] for item in cells);invalid=[item["run_id"] for item in cells if item["state"]=="invalid"];failed_learning=[item["run_id"] for item in cells if item["state"]=="complete" and not item["learning_pass"]]
    result={"status":"invalid" if invalid else "running" if counts["complete"]<27 else "complete","audited_at_utc":datetime.now(timezone.utc).isoformat(),"manifest":str(manifest_path),"manifest_sha256":digest(manifest_path),"counts":{"complete":counts["complete"],"partial":counts["partial"],"missing":counts["missing"],"invalid":counts["invalid"]},"invalid_cells":invalid,"failed_learning_cells":failed_learning,"cells":cells}
    text=json.dumps(result,indent=2)
    if args.out:
        path=Path(args.out);path=path if path.is_absolute() else root/path;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding="utf-8")
    print(text)

if __name__=="__main__":main()
