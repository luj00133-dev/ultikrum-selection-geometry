"""Independent standard-library verification of Stage 9 directional summaries."""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; CONFIG=ROOT/"configs"/"stage9_system_seed_converged.json"; OUT=ROOT/"results"/"processed"/"stage9_directional_diagnostic"
TRAIN=[2026,2027,2028]; SYSTEM=[91001,91002,91003]; DIST=["euclidean","normalized_euclidean","cosine"]
WINDOWS={"early_2-29":(2,29),"late_200-299":(200,299)}

def rows(path:Path):
    with path.open(encoding="utf-8-sig",newline="") as handle:return list(csv.DictReader(handle))

def main()->None:
    config=json.loads(CONFIG.read_text(encoding="utf-8")); old=[x for x in rows(ROOT/config["paths"]["stage8_manifest"]) if int(x["train_seed"]) in TRAIN and int(x["system_seed"])==91001 and x["distance"] in DIST]; new=rows(ROOT/config["paths"]["manifest"]); manifest=old+new
    expected={(t,s,d) for t in TRAIN for s in SYSTEM for d in DIST}; keys={(int(x["train_seed"]),int(x["system_seed"]),x["distance"]) for x in manifest}
    if len(manifest)!=27 or keys!=expected:raise SystemExit("grid failed")
    main={(int(x["train_seed"]),int(x["system_seed"]),x["distance"],x["window"]):x for x in rows(OUT/"cell_window_metrics.csv")}
    if len(main)!=54:raise SystemExit("main table coverage failed")
    maximum=0.0; recomputed={}
    for meta in manifest:
        counts=defaultdict(lambda:[0,set()]); values=defaultdict(lambda:[0,0.0,0.0,0])
        with Path(meta["system_log"]).open(encoding="utf-8-sig",newline="") as handle:
            for item in csv.DictReader(handle):
                rnd=int(item["round"]); counts[rnd][0]+=1; counts[rnd][1].add(int(item["client_id"])); group=item["resource_group"]
                if group not in ("strong","straggler"):continue
                for name,(start,end) in WINDOWS.items():
                    if start<=rnd<=end:
                        key=(name,group); values[key][0]+=int(item["selected"]); values[key][1]+=float(item["current_cosine_to_mean"]); values[key][2]+=float(item["effective_cosine_to_mean"]); values[key][3]+=1
        if set(counts)!=set(range(300)) or any(v[0]!=50 or len(v[1])!=50 for v in counts.values()):raise SystemExit(f"coverage failed {meta['run_id']}")
        base=(int(meta["train_seed"]),int(meta["system_seed"]),meta["distance"])
        for name in WINDOWS:
            strong=values[(name,"strong")]; slow=values[(name,"straggler")]
            current_gap=slow[1]/slow[3]-strong[1]/strong[3]; effective_gap=slow[2]/slow[3]-strong[2]/strong[3]
            result={"straggler_direction_shift":(slow[2]-slow[1])/slow[3],"strong_direction_shift":(strong[2]-strong[1])/strong[3],"effective_cosine_gap":effective_gap,"current_cosine_gap":current_gap,"selection_disparity_pp":100*(slow[0]/slow[3]-strong[0]/strong[3])}
            recomputed[base+(name,)]=result; reference=main[base+(name,)]
            for column,value in result.items():
                error=abs(value-float(reference[column]));maximum=max(maximum,error)
                if not math.isclose(value,float(reference[column]),rel_tol=0,abs_tol=1e-10):raise SystemExit(f"numeric mismatch {base} {name} {column}")
    early={}
    for system in SYSTEM:
        for distance in DIST:
            records=[recomputed[(train,system,distance,"early_2-29")] for train in TRAIN]
            early[(system,distance)]={key:sum(x[key] for x in records)/3 for key in records[0]}
    parts={"euclidean_straggler_shift_negative_each_system_seed":all(early[(s,"euclidean")]["straggler_direction_shift"]<0 for s in SYSTEM),"euclidean_effective_cosine_gap_negative_each_system_seed":all(early[(s,"euclidean")]["effective_cosine_gap"]<0 for s in SYSTEM),"cosine_selection_disparity_negative_each_system_seed":all(early[(s,"cosine")]["selection_disparity_pp"]<0 for s in SYSTEM)}
    analysis=json.loads((OUT/"analysis.json").read_text(encoding="utf-8")); supported=all(parts.values())
    if analysis["support_parts"]!=parts or analysis["stable_direction_exclusion_supported"]!=supported:raise SystemExit("decision mismatch")
    result={"status":"passed","verified_cells":27,"verified_cell_windows":54,"max_absolute_error":maximum,"support_parts":parts,"stable_direction_exclusion_supported":supported};(OUT/"independent_verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8");print(json.dumps(result,indent=2))

if __name__=="__main__":main()
