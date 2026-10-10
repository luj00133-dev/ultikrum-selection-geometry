"""Audit and analyze the frozen 27-cell Stage 10 CIFAR-10 replication."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

EPOCH_RE=re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)",re.MULTILINE)
TRAIN=[2026,2027,2028]; SYSTEM=[91001,91002,91003]
DIST=["euclidean","normalized_euclidean","cosine"]
WINDOWS={"primary_2-29":(2,29),"secondary_30-59":(30,59)}
REQUIRED={"round","client_id","resource_group","selected","aggregator_score","effective_norm","norm_ratio"}

def sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()

def read_manifest(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8",newline="") as handle: return list(csv.DictReader(handle))

def parse_accuracy(path:Path)->tuple[np.ndarray,np.ndarray]:
    text=path.read_text(encoding="utf-8",errors="replace")
    values=[(int(a),float(b)) for a,b in EPOCH_RE.findall(text)]
    if "Training finished on" not in text or [x[0] for x in values]!=list(range(60)): raise ValueError(f"invalid epoch coverage: {path}")
    return np.asarray([x[0] for x in values]),np.asarray([x[1] for x in values])

def ss_decomposition(values:pd.DataFrame,column:str)->dict[str,float]:
    matrix=values.pivot(index="train_seed",columns="system_seed",values=column).loc[TRAIN,SYSTEM].to_numpy(dtype=float)
    overall=matrix.mean(); total=float(((matrix-overall)**2).sum())
    train=float(len(SYSTEM)*((matrix.mean(axis=1)-overall)**2).sum())
    system=float(len(TRAIN)*((matrix.mean(axis=0)-overall)**2).sum())
    interaction=max(0.0,total-train-system)
    share=lambda value:value/total if total>0 else 0.0
    return {"ss_total":total,"train_share":share(train),"system_share":share(system),"interaction_share":share(interaction)}

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-root",default=str(Path(__file__).resolve().parents[1])); parser.add_argument("--config",default="configs/stage10_cifar10_early_replication.json"); parser.add_argument("--output-dir",default="results/processed/stage10_cifar10_early_replication"); parser.add_argument("--figure-dir",default="artifacts/figures/stage10_cifar10_early_replication"); args=parser.parse_args()
    root=Path(args.project_root).resolve(); config=json.loads((root/args.config).read_text(encoding="utf-8")); manifest=read_manifest(root/config["paths"]["manifest"])
    expected={(t,s,d) for t in TRAIN for s in SYSTEM for d in DIST}; keys={(int(x["train_seed"]),int(x["system_seed"]),x["distance"]) for x in manifest}
    if len(manifest)!=27 or keys!=expected: raise ValueError("Stage 10 manifest is not the frozen 3x3x3 grid")
    cells=[]; groups=[]; accuracies=[]; integrity=[]
    for row in manifest:
        paths={name:Path(row[name]).resolve() for name in ("output","system_log","resolved_config")}
        if any(not p.is_file() or p.stat().st_size==0 for p in paths.values()): raise ValueError(f"missing artifact: {row['run_id']}")
        epochs,accuracy=parse_accuracy(paths["output"]); resolved=json.loads(paths["resolved_config"].read_text(encoding="utf-8"))
        expected_config={"epochs":60,"seed_partition":int(row["partition_seed"]),"seed_train":int(row["train_seed"]),"system_seed":int(row["system_seed"]),"dataset":"CIFAR10","model":"simplecnn","distribution":"non-iid","dirichlet_alpha":0.5,"attack":"NoAttack","defense":row["vendor_aggregator"],"system_profile":"four_tier","num_clients":50}
        for key,value in expected_config.items():
            if resolved.get(key)!=value: raise ValueError(f"resolved mismatch {row['run_id']} {key}")
        if ast.literal_eval(resolved["defense_params"])!=config["defense_params"]: raise ValueError(f"defense params mismatch: {row['run_id']}")
        first10=float(accuracy[:10].mean()); last10=float(accuracy[-10:].mean()); gain=last10-first10
        learning_pass=last10>=config["gates"]["minimum_last10_accuracy"] and gain>=config["gates"]["minimum_last10_minus_first10_accuracy"]
        frame=pd.read_csv(paths["system_log"])
        if len(frame)!=3000 or not REQUIRED.issubset(frame.columns): raise ValueError(f"invalid system table: {row['run_id']}")
        counts=frame.groupby("round")["client_id"].agg(["size","nunique"])
        if set(counts.index)!=set(range(60)) or not ((counts["size"]==50)&(counts["nunique"]==50)).all(): raise ValueError(f"client-round coverage failed: {row['run_id']}")
        meta={"run_id":row["run_id"],"train_seed":int(row["train_seed"]),"system_seed":int(row["system_seed"]),"distance":row["distance"]}
        for epoch,value in zip(epochs,accuracy): accuracies.append({**meta,"round":int(epoch),"test_accuracy":float(value)})
        for window,(start,end) in WINDOWS.items():
            subset=frame[(frame["round"]>=start)&(frame["round"]<=end)]
            grouped=subset[subset.resource_group.isin(["strong","straggler"])].groupby("resource_group").agg(observations=("selected","size"),selection_rate=("selected","mean"),norm_ratio=("norm_ratio","mean"),score=("aggregator_score","mean"))
            if set(grouped.index)!={"strong","straggler"}: raise ValueError(f"resource groups missing: {row['run_id']}")
            for resource,item in grouped.iterrows(): groups.append({**meta,"window":window,"resource_group":resource,**item.to_dict()})
            cells.append({**meta,"window":window,"selection_disparity_pp":100*(grouped.loc["straggler","selection_rate"]-grouped.loc["strong","selection_rate"]),"norm_ratio_gap":grouped.loc["straggler","norm_ratio"]-grouped.loc["strong","norm_ratio"],"score_gap":grouped.loc["straggler","score"]-grouped.loc["strong","score"],"first10_accuracy":first10,"last10_accuracy":last10,"last10_minus_first10_accuracy":gain,"learning_pass":learning_pass})
        for kind,path in paths.items(): integrity.append({"run_id":row["run_id"],"artifact":kind,"path":str(path),"bytes":path.stat().st_size,"sha256":sha256(path)})
    cell=pd.DataFrame(cells); group=pd.DataFrame(groups); accuracy=pd.DataFrame(accuracies)
    learning=cell[cell.window=="primary_2-29"][["run_id","train_seed","system_seed","distance","first10_accuracy","last10_accuracy","last10_minus_first10_accuracy","learning_pass"]]
    all_learning=bool(learning.learning_pass.all())
    contrasts=[]
    for (train_seed,system_seed,window),part in cell.groupby(["train_seed","system_seed","window"]):
        values=part.set_index("distance")["selection_disparity_pp"].to_dict(); eu=values["euclidean"]
        for control in DIST[1:]: contrasts.append({"train_seed":train_seed,"system_seed":system_seed,"window":window,"control":control,"euclidean_disparity_pp":eu,"control_disparity_pp":values[control],"control_minus_euclidean_pp":values[control]-eu})
    contrast=pd.DataFrame(contrasts)
    margins=cell.groupby(["system_seed","distance","window"],as_index=False)["selection_disparity_pp"].mean()
    contrast_margins=contrast.groupby(["system_seed","control","window"],as_index=False)["control_minus_euclidean_pp"].mean()
    primary=cell[cell.window=="primary_2-29"]
    crossed_eu=float(primary[primary.distance=="euclidean"].selection_disparity_pp.mean())
    eu_system=margins[(margins.window=="primary_2-29")&(margins.distance=="euclidean")].set_index("system_seed").selection_disparity_pp.to_dict()
    control_system={d:contrast_margins[(contrast_margins.window=="primary_2-29")&(contrast_margins.control==d)].set_index("system_seed").control_minus_euclidean_pp.to_dict() for d in DIST[1:]}
    gate_parts={"all_learning_gates_passed":all_learning,"crossed_euclidean_at_least_5pp":crossed_eu>=config["gates"]["minimum_crossed_euclidean_disparity_pp"],"euclidean_positive_each_system_seed":all(eu_system[s]>0 for s in SYSTEM),"both_controls_negative_each_system_seed":all(control_system[d][s]<0 for d in DIST[1:] for s in SYSTEM)}
    transfer_pass=all(gate_parts.values())
    variance=[]
    for (distance,window),part in cell.groupby(["distance","window"]): variance.append({"metric":"disparity","level":distance,"window":window,**ss_decomposition(part,"selection_disparity_pp")})
    for (control_name,window),part in contrast.groupby(["control","window"]): variance.append({"metric":"paired_contrast","level":control_name,"window":window,**ss_decomposition(part,"control_minus_euclidean_pp")})
    loo=[]
    for omitted in SYSTEM:
        kept=[s for s in SYSTEM if s!=omitted]
        eu=float(primary[(primary.system_seed.isin(kept))&(primary.distance=="euclidean")].selection_disparity_pp.mean())
        for control_name in DIST[1:]:
            delta=float(contrast[(contrast.window=="primary_2-29")&(contrast.system_seed.isin(kept))&(contrast.control==control_name)].control_minus_euclidean_pp.mean())
            loo.append({"omitted_system_seed":omitted,"control":control_name,"euclidean_mean_pp":eu,"control_minus_euclidean_mean_pp":delta})
    output=root/args.output_dir; figures=root/args.figure_dir; output.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    cell.to_csv(output/"crossed_metrics.csv",index=False); group.to_csv(output/"group_window_metrics.csv",index=False); accuracy.to_csv(output/"accuracy_trajectories.csv",index=False); learning.to_csv(output/"learning_gates.csv",index=False); contrast.to_csv(output/"paired_contrasts.csv",index=False); margins.to_csv(output/"system_seed_margins.csv",index=False); contrast_margins.to_csv(output/"control_system_seed_margins.csv",index=False); pd.DataFrame(variance).to_csv(output/"variance_decomposition.csv",index=False); pd.DataFrame(loo).to_csv(output/"leave_one_system_seed_out.csv",index=False); pd.DataFrame(integrity).to_csv(output/"raw_sha256.csv",index=False)
    plt.rcParams.update({"font.size":8,"axes.spines.top":False,"axes.spines.right":False,"figure.facecolor":"white","axes.facecolor":"white"})
    titles={"euclidean":"Euclidean","normalized_euclidean":"Normalized Euclidean","cosine":"Cosine"}
    fig,axes=plt.subplots(1,3,figsize=(8.4,2.9),sharex=True,sharey=True)
    limit=max(10,float(np.ceil(primary.selection_disparity_pp.abs().max()/5)*5))
    for ax,distance in zip(axes,DIST):
        matrix=primary[primary.distance==distance].pivot(index="train_seed",columns="system_seed",values="selection_disparity_pp").loc[TRAIN,SYSTEM]
        image=ax.imshow(matrix.to_numpy(),cmap="RdBu_r",vmin=-limit,vmax=limit)
        for i in range(3):
            for j in range(3): ax.text(j,i,f"{matrix.iloc[i,j]:+.1f}",ha="center",va="center",fontsize=7)
        ax.set_title(titles[distance]); ax.set_xticks(range(3),SYSTEM); ax.set_yticks(range(3),TRAIN); ax.set_xlabel("System seed")
    axes[0].set_ylabel("Train / partition seed"); fig.colorbar(image,ax=axes,label="Straggler - strong selection rate (pp)",fraction=.025,pad=.03); fig.subplots_adjust(left=.08,right=.88,bottom=.20,top=.88,wspace=.18)
    for ext in ("png","pdf","svg"): fig.savefig(figures/f"primary_disparity_matrix.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(5.0,3.0))
    for distance,color in zip(DIST,["#2F5597","#2A9D8F","#E76F51"]):
        subset=accuracy[accuracy.distance==distance].groupby("round").test_accuracy.agg(["mean","min","max"]).reset_index(); ax.plot(subset["round"],subset["mean"],label=titles[distance],color=color); ax.fill_between(subset["round"],subset["min"],subset["max"],color=color,alpha=.10)
    ax.set(xlabel="Training round",ylabel="Test accuracy",title="CIFAR-10 learning trajectories"); ax.grid(alpha=.15); ax.legend(frameon=False,fontsize=7); fig.tight_layout()
    for ext in ("png","pdf","svg"): fig.savefig(figures/f"accuracy_trajectory.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)
    result={"status":"complete" if all_learning else "learning_gate_failed","verified_cells":27,"all_integrity_checks_passed":True,"all_learning_gates_passed":all_learning,"crossed_euclidean_disparity_pp":crossed_eu,"euclidean_system_margins_pp":eu_system,"control_system_margins_pp":control_system,"gate_parts":gate_parts,"transfer_gate_pass":transfer_pass if all_learning else False,"next_action":"manuscript_assembly" if transfer_pass else "report_boundary_and_stop_expansion"}
    (output/"analysis.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))

if __name__=="__main__": main()
