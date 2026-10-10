"""Independent standard-library verification of the Stage 8/9 crossed artifacts."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"configs"/"stage9_system_seed_converged.json"
OUTPUT=ROOT/"results"/"processed"/"stage9_system_seed_converged"/"independent_verification.json"
EPOCH=re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)",re.MULTILINE)
TRAIN=[2026,2027,2028]; SYSTEM=[91001,91002,91003]; DIST=["euclidean","normalized_euclidean","cosine"]


def rows(path: Path):
    with path.open(encoding="utf-8",newline="") as handle: return list(csv.DictReader(handle))


def main():
    config=json.loads(CONFIG.read_text(encoding="utf-8"))
    old=[x for x in rows(ROOT/config["paths"]["stage8_manifest"]) if int(x["train_seed"]) in TRAIN]
    new=rows(ROOT/config["paths"]["manifest"]); combined=old+new
    expected={(a,b,c) for a in TRAIN for b in SYSTEM for c in DIST}
    keys={(int(x["train_seed"]),int(x["system_seed"]),x["distance"]) for x in combined}
    if len(combined)!=27 or keys!=expected: raise SystemExit("independent combined-grid check failed")
    findings=[]; rates={}
    for row in combined:
        text=Path(row["output"]).read_text(encoding="utf-8",errors="replace"); epochs=[(int(a),float(b)) for a,b in EPOCH.findall(text)]
        if "Training finished on" not in text or [x[0] for x in epochs]!=list(range(300)): raise SystemExit(f"log failed: {row['run_id']}")
        resolved=json.loads(Path(row["resolved_config"]).read_text(encoding="utf-8")); expected_config=(int(row["train_seed"]),int(row["partition_seed"]),int(row["system_seed"]),row["vendor_aggregator"],300)
        if (resolved.get("seed_train"),resolved.get("seed_partition"),resolved.get("system_seed"),resolved.get("defense"),resolved.get("epochs"))!=expected_config: raise SystemExit(f"resolved failed: {row['run_id']}")
        counts=defaultdict(lambda:[0,set()]); selected=defaultdict(lambda:[0,0])
        with Path(row["system_log"]).open(encoding="utf-8-sig",newline="") as handle:
            for item in csv.DictReader(handle):
                rnd=int(item["round"]); cid=int(item["client_id"]); counts[rnd][0]+=1; counts[rnd][1].add(cid)
                window="2-29" if 2<=rnd<=29 else "200-299" if 200<=rnd<=299 else None
                if window and item["resource_group"] in ("strong","straggler"):
                    bucket=selected[(window,item["resource_group"])]; bucket[0]+=int(item["selected"]); bucket[1]+=1
        if set(counts)!=set(range(300)) or any(v[0]!=50 or len(v[1])!=50 for v in counts.values()): raise SystemExit(f"system rows failed: {row['run_id']}")
        key=(int(row["train_seed"]),int(row["system_seed"]),row["distance"])
        for window in ("2-29","200-299"):
            strong=selected[(window,"strong")]; slow=selected[(window,"straggler")]
            rates[key+(window,)]=100*(slow[0]/slow[1]-strong[0]/strong[1])
        findings.append({"run_id":row["run_id"],"final_accuracy":epochs[-1][1],"rows":sum(v[0] for v in counts.values())})
    decisions={}
    for window in ("2-29","200-299"):
        eu={sys:sum(rates[(train,sys,"euclidean",window)] for train in TRAIN)/3 for sys in SYSTEM}
        controls={control:{sys:sum(rates[(train,sys,control,window)]-rates[(train,sys,"euclidean",window)] for train in TRAIN)/3 for sys in SYSTEM} for control in DIST[1:]}
        qualifying=[c for c,v in controls.items() if all(v[s]<0 for s in SYSTEM)]
        decisions[window]={"euclidean_all_positive":all(eu[s]>0 for s in SYSTEM),"controls_all_negative":qualifying}
    passed=all(v["euclidean_all_positive"] and v["controls_all_negative"] for v in decisions.values())
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps({"status":"passed","verified_runs":27,"lag_dose_gate_pass":passed,"decision":decisions,"findings":findings},indent=2),encoding="utf-8")
    print(f"independent Stage 9 verification passed: 27/27; lag_dose_gate_pass={passed}")


if __name__=="__main__": main()
