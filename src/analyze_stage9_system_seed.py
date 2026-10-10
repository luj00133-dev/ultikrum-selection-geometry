"""Audit and analyze the 27-cell Stage 8/9 crossed system-seed design."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


EPOCH_RE = re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)", re.MULTILINE)
WINDOWS = [(2, 29), (30, 99), (100, 199), (200, 299)]
TRAIN_SEEDS = [2026, 2027, 2028]
SYSTEM_SEEDS = [91001, 91002, 91003]
DISTANCES = ["euclidean", "normalized_euclidean", "cosine"]
REQUIRED_COLUMNS = {"round", "client_id", "resource_group", "selected", "aggregator_score", "effective_norm", "norm_ratio"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))


def combined_manifest(root: Path, config: dict) -> list[dict[str, str]]:
    stage8 = read_manifest(root / config["paths"]["stage8_manifest"])
    prior = [row for row in stage8 if int(row["train_seed"]) in TRAIN_SEEDS and int(row["system_seed"]) == 91001 and row["distance"] in DISTANCES]
    new = read_manifest(root / config["paths"]["manifest"])
    if len(prior) != 9 or len(new) != 18: raise ValueError(f"expected 9 Stage 8 + 18 Stage 9 rows, got {len(prior)} + {len(new)}")
    keys = [(int(x["train_seed"]), int(x["system_seed"]), x["distance"]) for x in prior + new]
    expected = {(a, b, c) for a in TRAIN_SEEDS for b in SYSTEM_SEEDS for c in DISTANCES}
    if len(keys) != len(set(keys)) or set(keys) != expected: raise ValueError("combined manifest is not the frozen 3x3x3 design")
    return prior + new


def parse_accuracy(path: Path) -> tuple[np.ndarray, np.ndarray]:
    text = path.read_text(encoding="utf-8", errors="replace")
    pairs = [(int(a), float(b)) for a, b in EPOCH_RE.findall(text)]
    if "Training finished on" not in text or [x[0] for x in pairs] != list(range(300)):
        raise ValueError(f"invalid epoch coverage: {path}")
    return np.asarray([x[0] for x in pairs]), np.asarray([x[1] for x in pairs])


def ss_decomposition(values: pd.DataFrame, value: str) -> dict[str, float]:
    matrix = values.pivot(index="train_seed", columns="system_seed", values=value).loc[TRAIN_SEEDS, SYSTEM_SEEDS]
    data = matrix.to_numpy(dtype=float); overall = data.mean()
    ss_total = float(((data - overall) ** 2).sum())
    ss_train = float(len(SYSTEM_SEEDS) * ((data.mean(axis=1) - overall) ** 2).sum())
    ss_system = float(len(TRAIN_SEEDS) * ((data.mean(axis=0) - overall) ** 2).sum())
    ss_interaction = max(0.0, ss_total - ss_train - ss_system)
    def share(x: float) -> float: return x / ss_total if ss_total > 0 else 0.0
    return {"ss_total": ss_total, "train_share": share(ss_train), "system_share": share(ss_system), "interaction_share": share(ss_interaction)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--config", default="configs/stage9_system_seed_converged.json")
    parser.add_argument("--output-dir", default="results/processed/stage9_system_seed_converged")
    args = parser.parse_args(); root = Path(args.project_root).resolve()
    config = json.loads((root / args.config).read_text(encoding="utf-8")); rows = combined_manifest(root, config)
    run_records=[]; group_records=[]; integrity=[]
    expected_params = config["defense_params"]
    for row in rows:
        paths={k:Path(row[k]).resolve() for k in ("output","system_log","resolved_config")}
        if any(not p.is_file() or p.stat().st_size == 0 for p in paths.values()): raise ValueError(f"missing artifact: {row['run_id']}")
        epochs, accuracy = parse_accuracy(paths["output"]); resolved=json.loads(paths["resolved_config"].read_text(encoding="utf-8"))
        expected={"epochs":300,"seed_partition":int(row["partition_seed"]),"seed_train":int(row["train_seed"]),"system_seed":int(row["system_seed"]),
                  "dataset":"FashionMNIST","model":"lenet","distribution":"non-iid","dirichlet_alpha":0.5,"attack":"NoAttack",
                  "defense":row["vendor_aggregator"],"system_profile":"four_tier","num_clients":50}
        for key,value in expected.items():
            if resolved.get(key) != value: raise ValueError(f"resolved mismatch {row['run_id']} {key}")
        if ast.literal_eval(resolved["defense_params"]) != expected_params: raise ValueError(f"defense params mismatch: {row['run_id']}")
        final=float(accuracy[-1]); slope=float(np.polyfit(epochs[-50:],accuracy[-50:],1)[0])
        passed=final >= config["gates"]["final_accuracy_min"] and slope >= config["gates"]["terminal_slope_min"]
        frame=pd.read_csv(paths["system_log"])
        if len(frame) != 15000 or not REQUIRED_COLUMNS.issubset(frame.columns): raise ValueError(f"invalid system table: {row['run_id']}")
        counts=frame.groupby("round")["client_id"].agg(["size","nunique"])
        if set(counts.index) != set(range(300)) or not ((counts["size"]==50)&(counts["nunique"]==50)).all(): raise ValueError(f"client-round coverage failed: {row['run_id']}")
        train_seed=int(row["train_seed"]); system_seed=int(row["system_seed"]); distance=row["distance"]
        for start,end in WINDOWS:
            window=frame[(frame["round"]>=start)&(frame["round"]<=end)]
            for group,values in window.groupby("resource_group"):
                group_records.append({"run_id":row["run_id"],"train_seed":train_seed,"system_seed":system_seed,"distance":distance,
                    "window":f"{start}-{end}","resource_group":group,"observations":len(values),"selection_rate":float(values["selected"].mean())})
        run_records.append({"run_id":row["run_id"],"source_stage":row["stage"],"train_seed":train_seed,"system_seed":system_seed,
                            "distance":distance,"final_accuracy":final,"terminal_slope":slope,"convergence_pass":passed})
        for kind,path in paths.items(): integrity.append({"run_id":row["run_id"],"artifact":kind,"path":str(path),"bytes":path.stat().st_size,"sha256":sha256(path)})
    runs=pd.DataFrame(run_records)
    if len(runs)!=27 or not runs["convergence_pass"].all():
        failed=runs.loc[~runs["convergence_pass"],"run_id"].tolist(); raise ValueError(f"combined convergence gate failed: {failed}")
    groups=pd.DataFrame(group_records)
    disparities=groups.pivot_table(index=["train_seed","system_seed","distance","window"],columns="resource_group",values="selection_rate").reset_index()
    disparities["straggler_minus_strong_pp"]=100*(disparities["straggler"]-disparities["strong"])
    contrast_records=[]
    for (train_seed,system_seed,window),part in disparities.groupby(["train_seed","system_seed","window"]):
        value=dict(zip(part["distance"],part["straggler_minus_strong_pp"])); eu=value["euclidean"]
        for control in DISTANCES[1:]: contrast_records.append({"train_seed":train_seed,"system_seed":system_seed,"window":window,"control":control,
            "euclidean_disparity_pp":eu,"control_disparity_pp":value[control],"control_minus_euclidean_pp":value[control]-eu})
    contrasts=pd.DataFrame(contrast_records)
    variance=[]
    for (distance,window),part in disparities.groupby(["distance","window"]):
        variance.append({"metric":"disparity","level":distance,"window":window,**ss_decomposition(part,"straggler_minus_strong_pp")})
    for (control,window),part in contrasts.groupby(["control","window"]):
        variance.append({"metric":"paired_contrast","level":control,"window":window,**ss_decomposition(part,"control_minus_euclidean_pp")})
    margins=disparities.groupby(["system_seed","distance","window"],as_index=False)["straggler_minus_strong_pp"].mean()
    contrast_margins=contrasts.groupby(["system_seed","control","window"],as_index=False)["control_minus_euclidean_pp"].mean()
    decisions={}
    for window in ("2-29","200-299"):
        e=margins[(margins.window==window)&(margins.distance=="euclidean")].set_index("system_seed")["straggler_minus_strong_pp"]
        controls={c:contrast_margins[(contrast_margins.window==window)&(contrast_margins.control==c)].set_index("system_seed")["control_minus_euclidean_pp"].to_dict() for c in DISTANCES[1:]}
        euclidean_all_positive=all(e[s]>0 for s in SYSTEM_SEEDS)
        qualifying=[c for c,v in controls.items() if all(v[s]<0 for s in SYSTEM_SEEDS)]
        decisions[window]={"euclidean_system_margins_pp":e.to_dict(),"control_system_margins_pp":controls,
                           "euclidean_all_positive":euclidean_all_positive,"controls_all_negative":qualifying,
                           "window_pass":euclidean_all_positive and bool(qualifying)}
    loo=[]
    for omitted in SYSTEM_SEEDS:
        kept=[x for x in SYSTEM_SEEDS if x!=omitted]
        for window in ("2-29","200-299"):
            eu=float(disparities[(disparities.system_seed.isin(kept))&(disparities.distance=="euclidean")&(disparities.window==window)]["straggler_minus_strong_pp"].mean())
            for control in DISTANCES[1:]:
                delta=float(contrasts[(contrasts.system_seed.isin(kept))&(contrasts.control==control)&(contrasts.window==window)]["control_minus_euclidean_pp"].mean())
                loo.append({"omitted_system_seed":omitted,"window":window,"control":control,"euclidean_mean_pp":eu,"control_minus_euclidean_mean_pp":delta})
    overall_pass=all(item["window_pass"] for item in decisions.values())
    output=root/args.output_dir; output.mkdir(parents=True,exist_ok=True)
    runs.to_csv(output/"run_convergence.csv",index=False); groups.to_csv(output/"group_window_metrics.csv",index=False)
    disparities.to_csv(output/"crossed_disparities.csv",index=False); contrasts.to_csv(output/"paired_contrasts.csv",index=False)
    pd.DataFrame(variance).to_csv(output/"variance_decomposition.csv",index=False); margins.to_csv(output/"system_seed_margins.csv",index=False)
    contrast_margins.to_csv(output/"control_system_seed_margins.csv",index=False); pd.DataFrame(loo).to_csv(output/"leave_one_system_seed_out.csv",index=False)
    pd.DataFrame(integrity).to_csv(output/"raw_sha256.csv",index=False)
    result={"status":"verified_analysis_complete","combined_runs":27,"all_convergence_gates_passed":True,"decision":decisions,
            "lag_dose_gate_pass":overall_pass,"next_action":"lag_dose" if overall_pass else "system_seed_dependent_reframe_or_more_seeds"}
    (output/"analysis.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))


if __name__ == "__main__": main()
