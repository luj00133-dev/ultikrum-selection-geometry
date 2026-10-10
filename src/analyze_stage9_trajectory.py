"""Time-resolved secondary analysis of the verified Stage 8/9 crossed design."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from analyze_stage9_system_seed import combined_manifest


TRAIN_SEEDS=[2026,2027,2028]
SYSTEM_SEEDS=[91001,91002,91003]
DISTANCES=["euclidean","normalized_euclidean","cosine"]
COLORS={91001:"#2F5597",91002:"#2A9D8F",91003:"#E76F51"}


def bin_spec(round_id: int):
    if round_id < 2: return None
    if round_id < 10: return ("2-9",2,9,5.5)
    start=(round_id//10)*10
    return (f"{start}-{start+9}",start,start+9,start+4.5)


def stabilization_bin(frame: pd.DataFrame, threshold: float=5.0):
    values=frame[frame["bin_start"]>=10].sort_values("bin_start")
    for row in values.itertuples():
        remaining=values[values["bin_start"]>=row.bin_start]["value"].abs()
        if len(remaining) and bool((remaining<=threshold).all()): return int(row.bin_start)
    return None


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def weighted_window(frame: pd.DataFrame, start: int, end: int) -> float:
    subset=frame[(frame.bin_start>=start)&(frame.bin_end<=end)]
    return float(np.average(subset["value"],weights=subset["round_count"]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root",default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--config",default="configs/stage9_system_seed_converged.json")
    parser.add_argument("--output-dir",default="results/processed/stage9_time_resolved")
    parser.add_argument("--figure-dir",default="artifacts/figures/stage9_time_resolved")
    args=parser.parse_args(); root=Path(args.project_root).resolve()
    config=json.loads((root/args.config).read_text(encoding="utf-8")); manifest=combined_manifest(root,config)
    records=[]; integrity=[]
    for row in manifest:
        path=Path(row["system_log"]).resolve(); frame=pd.read_csv(path)
        if len(frame)!=15000 or set(frame["round"].unique())!=set(range(300)): raise ValueError(f"invalid raw trajectory: {row['run_id']}")
        counts=frame.groupby("round")["client_id"].agg(["size","nunique"])
        if not ((counts["size"]==50)&(counts["nunique"]==50)).all(): raise ValueError(f"client coverage failed: {row['run_id']}")
        frame=frame[frame["round"]>=2].copy(); specs=frame["round"].map(bin_spec)
        frame[["bin","bin_start","bin_end","bin_center"]]=pd.DataFrame(specs.tolist(),index=frame.index)
        grouped=frame.groupby(["bin","bin_start","bin_end","bin_center","resource_group"],as_index=False).agg(
            round_count=("round","nunique"),selection_rate=("selected","mean"),norm_ratio=("norm_ratio","mean"),score=("aggregator_score","mean"))
        pivot=grouped[grouped.resource_group.isin(["strong","straggler"])].pivot(index=["bin","bin_start","bin_end","bin_center","round_count"],columns="resource_group",values=["selection_rate","norm_ratio","score"]).reset_index()
        pivot.columns=["_".join(x).rstrip("_") if isinstance(x,tuple) else x for x in pivot.columns]
        for item in pivot.itertuples():
            records.append({"run_id":row["run_id"],"train_seed":int(row["train_seed"]),"system_seed":int(row["system_seed"]),"distance":row["distance"],
                "bin":item.bin,"bin_start":int(item.bin_start),"bin_end":int(item.bin_end),"bin_center":float(item.bin_center),"round_count":int(item.round_count),
                "selection_disparity_pp":100*(item.selection_rate_straggler-item.selection_rate_strong),
                "norm_ratio_gap":item.norm_ratio_straggler-item.norm_ratio_strong,"score_gap":item.score_straggler-item.score_strong})
        integrity.append({"run_id":row["run_id"],"path":str(path),"bytes":path.stat().st_size,"sha256":sha256(path)})
    bins=pd.DataFrame(records).sort_values(["train_seed","system_seed","distance","bin_start"])
    if len(bins)!=27*30: raise ValueError(f"expected 810 cell-bin rows, got {len(bins)}")
    margins=bins.groupby(["system_seed","distance","bin","bin_start","bin_end","bin_center","round_count"],as_index=False)[["selection_disparity_pp","norm_ratio_gap","score_gap"]].mean()
    overall=bins.groupby(["distance","bin","bin_start","bin_end","bin_center","round_count"],as_index=False)[["selection_disparity_pp","norm_ratio_gap","score_gap"]].mean()
    contrast=[]
    for (train_seed,system_seed,bin_name),part in bins.groupby(["train_seed","system_seed","bin"]):
        value=part.set_index("distance")["selection_disparity_pp"].to_dict(); meta=part.iloc[0]
        for control in DISTANCES[1:]: contrast.append({"train_seed":train_seed,"system_seed":system_seed,"bin":bin_name,"bin_start":int(meta.bin_start),"bin_end":int(meta.bin_end),"bin_center":float(meta.bin_center),"round_count":int(meta.round_count),"control":control,"control_minus_euclidean_pp":value[control]-value["euclidean"]})
    contrasts=pd.DataFrame(contrast)
    contrast_margins=contrasts.groupby(["system_seed","control","bin","bin_start","bin_end","bin_center","round_count"],as_index=False)["control_minus_euclidean_pp"].mean()
    summaries=[]
    for (system_seed,distance),part in margins.groupby(["system_seed","distance"]):
        work=part.rename(columns={"selection_disparity_pp":"value"})
        early=work[(work.bin_start>=10)&(work.bin_end<=99)]; late=work[(work.bin_start>=100)&(work.bin_end<=299)]
        summaries.append({"system_seed":system_seed,"distance":distance,"early_weighted_2_29_pp":weighted_window(work,2,29),"late_weighted_200_299_pp":weighted_window(work,200,299),
            "slope_10_99_pp_per_100_rounds":float(np.polyfit(early.bin_center,early.value,1)[0]*100),"slope_100_299_pp_per_100_rounds":float(np.polyfit(late.bin_center,late.value,1)[0]*100),
            "stabilization_start_round_abs_le_5":stabilization_bin(work)})
    summary=pd.DataFrame(summaries)
    associations=[]
    eu=bins[bins.distance=="euclidean"]
    for (train_seed,system_seed),part in eu.groupby(["train_seed","system_seed"]):
        rho_norm,p_norm=stats.spearmanr(part.selection_disparity_pp,-part.norm_ratio_gap)
        rho_score,p_score=stats.spearmanr(part.selection_disparity_pp,-part.score_gap)
        associations.append({"train_seed":train_seed,"system_seed":system_seed,"bins":len(part),"rho_selection_vs_negative_norm_ratio_gap":rho_norm,"p_descriptive_norm":p_norm,"rho_selection_vs_negative_score_gap":rho_score,"p_descriptive_score":p_score})
    associations=pd.DataFrame(associations)
    output=root/args.output_dir; figures=root/args.figure_dir; output.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    bins.to_csv(output/"trajectory_bins.csv",index=False); margins.to_csv(output/"system_seed_margins.csv",index=False); overall.to_csv(output/"overall_margins.csv",index=False)
    contrasts.to_csv(output/"paired_contrast_bins.csv",index=False); contrast_margins.to_csv(output/"control_system_seed_margins.csv",index=False); summary.to_csv(output/"decay_summaries.csv",index=False)
    associations.to_csv(output/"euclidean_geometry_associations.csv",index=False); pd.DataFrame(integrity).to_csv(output/"raw_sha256.csv",index=False)
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"figure.facecolor":"white","axes.facecolor":"white"})
    fig,axes=plt.subplots(1,3,figsize=(10.2,3.2),sharex=True,sharey=True)
    titles={"euclidean":"Euclidean","normalized_euclidean":"Normalized Euclidean","cosine":"Cosine"}
    for ax,distance in zip(axes,DISTANCES):
        for seed in SYSTEM_SEEDS:
            p=margins[(margins.distance==distance)&(margins.system_seed==seed)].sort_values("bin_center")
            ax.plot(p.bin_center,p.selection_disparity_pp,color=COLORS[seed],lw=1.25,label=f"system seed {seed}")
        p=overall[overall.distance==distance].sort_values("bin_center"); ax.plot(p.bin_center,p.selection_disparity_pp,color="#202020",lw=2.2,label="crossed mean")
        ax.axhline(0,color="#777777",lw=.8); ax.axhspan(-5,5,color="#B0B0B0",alpha=.13); ax.set_title(titles[distance]); ax.set_xlabel("Training round"); ax.grid(alpha=.15)
    axes[0].set_ylabel("Straggler - strong selection rate (pp)"); axes[-1].legend(frameon=False,fontsize=7,loc="best")
    fig.tight_layout();
    for ext in ("png","pdf","svg"): fig.savefig(figures/f"selection_disparity_trajectory.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.2),sharex=True,sharey=True)
    for ax,control in zip(axes,DISTANCES[1:]):
        for seed in SYSTEM_SEEDS:
            p=contrast_margins[(contrast_margins.control==control)&(contrast_margins.system_seed==seed)].sort_values("bin_center")
            ax.plot(p.bin_center,p.control_minus_euclidean_pp,color=COLORS[seed],lw=1.35,label=str(seed))
        ax.axhline(0,color="#777777",lw=.8); ax.set_title(titles[control]+" - Euclidean"); ax.set_xlabel("Training round"); ax.grid(alpha=.15)
    axes[0].set_ylabel("Paired disparity contrast (pp)"); axes[-1].legend(title="System seed",frameon=False,fontsize=7,title_fontsize=7)
    fig.tight_layout();
    for ext in ("png","pdf","svg"): fig.savefig(figures/f"control_contrast_trajectory.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.2),sharey=True)
    geometry_specs=[
        ("norm_ratio_gap","Negative straggler-strong norm-ratio gap"),
        ("score_gap","Negative straggler-strong score gap"),
    ]
    median_rhos=[
        float(associations.rho_selection_vs_negative_norm_ratio_gap.median()),
        float(associations.rho_selection_vs_negative_score_gap.median()),
    ]
    for ax,(column,xlabel),median_rho in zip(axes,geometry_specs,median_rhos):
        for seed in SYSTEM_SEEDS:
            p=eu[eu.system_seed==seed]
            ax.scatter(-p[column],p.selection_disparity_pp,s=16,alpha=.55,
                       color=COLORS[seed],edgecolors="none",label=str(seed))
        ax.axhline(0,color="#777777",lw=.8)
        ax.axhspan(-5,5,color="#B0B0B0",alpha=.13)
        ax.set_xlabel(xlabel)
        ax.grid(alpha=.15)
        ax.text(.03,.96,rf"median $\rho$ = {median_rho:.2f}",transform=ax.transAxes,
                ha="left",va="top",fontsize=8,
                bbox={"facecolor":"white","edgecolor":"none","alpha":.78,"pad":1.5})
    axes[0].set_ylabel("Straggler - strong selection rate (pp)")
    axes[-1].legend(title="System seed",frameon=False,fontsize=7,title_fontsize=7)
    fig.tight_layout()
    for ext in ("png","pdf","svg"): fig.savefig(figures/f"geometry_diagnostics.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)
    result={"status":"complete","cell_bin_rows":len(bins),"raw_files":len(integrity),"bins_per_cell":30,"warmup_excluded":[0,1],"practical_threshold_pp":5.0,
            "median_geometry_rho":{"negative_norm_ratio_gap":float(associations.rho_selection_vs_negative_norm_ratio_gap.median()),"negative_score_gap":float(associations.rho_selection_vs_negative_score_gap.median())}}
    (output/"analysis.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))


if __name__=="__main__": main()
