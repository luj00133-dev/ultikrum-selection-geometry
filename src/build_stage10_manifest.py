"""Build the frozen Stage 10 CIFAR-10 early-replication manifest."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

TRAIN_SEEDS=[2026,2027,2028]
SYSTEM_SEEDS=[91001,91002,91003]
AGGREGATORS=["MultiKrum","MultiKrumNormalized","MultiKrumCosine"]
DISTANCES=["euclidean","normalized_euclidean","cosine"]
FIELDS=["run_id","stage","dataset","model","algorithm","data_condition","partition","distribution","dirichlet_alpha","system_condition","system_profile","partition_seed","train_seed","system_seed","resource_assignment_seed","aggregator","vendor_aggregator","distance","defense_params","attack","rounds","expected_system_rows","base_config","output","system_log","resolved_config","completion_marker","analysis_unit","status"]

def load_config(path: str|Path)->dict[str,Any]:
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("Stage 10 config must be an object")
    return value

def resolve_root(config:dict[str,Any],project_root:str|Path|None=None)->Path:
    return Path(project_root or config.get("project_root") or Path(__file__).parents[1]).resolve()

def inside(root:Path,value:str|Path)->Path:
    path=Path(value); path=(path if path.is_absolute() else root/path).resolve()
    try: path.relative_to(root)
    except ValueError as exc: raise ValueError(f"path escapes project root: {path}") from exc
    return path

def registered_aggregators(root:Path)->set[str]:
    pattern=re.compile(r"@aggregator_registry\s*\nclass\s+(\w+)",re.MULTILINE)
    names:set[str]=set()
    for source in sorted((root/"vendor"/"FLPoison"/"aggregators").glob("*.py")):
        names.update(pattern.findall(source.read_text(encoding="utf-8")))
    return names

def validate(config:dict[str,Any],root:Path)->None:
    fixed={"experiment":"stage10_cifar10_early_replication","dataset":"CIFAR10","model":"simplecnn","algorithm":"FedSGD","rounds":60,"num_clients":50,"attack":"NoAttack","system_condition":"heterogeneous","system_profile":"four_tier","train_seeds":TRAIN_SEEDS,"system_seeds":SYSTEM_SEEDS}
    for key,expected in fixed.items():
        if config.get(key)!=expected: raise ValueError(f"Stage 10 requires {key}={expected!r}")
    if config.get("data_condition")!={"name":"a05","partition":"dirichlet","distribution":"non-iid","dirichlet_alpha":0.5}: raise ValueError("Stage 10 data condition changed")
    controls=config.get("distance_controls",[])
    if [x.get("aggregator") for x in controls]!=AGGREGATORS or [x.get("distance") for x in controls]!=DISTANCES: raise ValueError("Stage 10 controls changed")
    if config.get("defense_params")!={"avg_percentage":0.76,"enable_check":False,"num_score_neighbors":39}: raise ValueError("Stage 10 defense parameters changed")
    if config.get("windows")!={"warmup_excluded":[0,1],"primary_early":[2,29],"secondary_later":[30,59]}: raise ValueError("Stage 10 windows changed")
    if config.get("gates")!={"minimum_last10_accuracy":0.15,"minimum_last10_minus_first10_accuracy":0.03,"minimum_crossed_euclidean_disparity_pp":5.0,"require_positive_euclidean_each_system_seed":True,"require_negative_both_control_contrasts_each_system_seed":True,"required_cells":27}: raise ValueError("Stage 10 gates changed")
    if set(AGGREGATORS)-registered_aggregators(root): raise ValueError("Stage 10 aggregator is not registered")
    if inside(root,config["paths"]["result_root"]).name!="stage10_cifar10_early_replication": raise ValueError("Stage 10 result root changed")
    inside(root,config["base_config"])

def build_rows(config:dict[str,Any],project_root:str|Path|None=None,smoke:bool=False)->list[dict[str,Any]]:
    root=resolve_root(config,project_root); validate(config,root)
    result_root=inside(root,"results/smoke/stage10_cifar10_early_replication" if smoke else config["paths"]["result_root"])
    base_config=inside(root,config["base_config"]); condition=config["data_condition"]
    params=json.dumps(config["defense_params"],sort_keys=True,separators=(",",":"))
    rounds=2 if smoke else config["rounds"]
    train_seeds=[TRAIN_SEEDS[0]] if smoke else TRAIN_SEEDS
    system_seeds=[SYSTEM_SEEDS[0]] if smoke else SYSTEM_SEEDS
    rows=[]
    for train_seed in train_seeds:
        for system_seed in system_seeds:
            for control in config["distance_controls"]:
                prefix="smoke" if smoke else "stage10"
                run_id=f"{prefix}_cifar10_a05_r{rounds}_{control['name']}_s{train_seed}_sys{system_seed}"
                output=result_root/f"{run_id}.log"
                rows.append({"run_id":run_id,"stage":config["experiment"],"dataset":config["dataset"],"model":config["model"],"algorithm":config["algorithm"],"data_condition":condition["name"],"partition":condition["partition"],"distribution":condition["distribution"],"dirichlet_alpha":condition["dirichlet_alpha"],"system_condition":config["system_condition"],"system_profile":config["system_profile"],"partition_seed":train_seed,"train_seed":train_seed,"system_seed":system_seed,"resource_assignment_seed":system_seed,"aggregator":control["aggregator"],"vendor_aggregator":control["aggregator"],"distance":control["distance"],"defense_params":params,"attack":config["attack"],"rounds":rounds,"expected_system_rows":rounds*50,"base_config":str(base_config),"output":str(output),"system_log":str(output.with_suffix(".system.csv")),"resolved_config":str(output.with_suffix(".resolved.json")),"completion_marker":"Training finished on","analysis_unit":"train_seed x system_seed","status":"smoke" if smoke else "planned"})
    expected=3 if smoke else 27
    if len(rows)!=expected or len({row["run_id"] for row in rows})!=expected: raise ValueError(f"Stage 10 expected {expected} unique cells")
    return rows

def write_rows(rows:list[dict[str,Any]],path:str|Path)->None:
    output=Path(path); output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS,lineterminator="\n"); writer.writeheader(); writer.writerows(rows)

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--config",required=True); parser.add_argument("--project-root"); parser.add_argument("--out"); parser.add_argument("--dry-run",action="store_true"); parser.add_argument("--json",action="store_true"); parser.add_argument("--smoke",action="store_true"); args=parser.parse_args()
    root=Path(args.project_root).resolve() if args.project_root else Path(__file__).parents[1]
    config_path=Path(args.config); config_path=config_path if config_path.is_absolute() else root/config_path
    config=load_config(config_path); rows=build_rows(config,root,smoke=args.smoke)
    if args.dry_run or args.smoke:
        print(json.dumps(rows,indent=2) if args.json else "\n".join(x["run_id"] for x in rows)); return
    output=inside(root,args.out or config["paths"]["manifest"]); write_rows(rows,output); print(f"wrote {len(rows)} Stage 10 cells to {output}")

if __name__=="__main__": main()
