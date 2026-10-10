"""Read-only directional-mechanism boundary diagnostic for verified Stage 8/9."""
from __future__ import annotations

import argparse
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

TRAIN=[2026,2027,2028]; SYSTEM=[91001,91002,91003]
DIST=["euclidean","normalized_euclidean","cosine"]
WINDOWS={"early_2-29":(2,29),"late_200-299":(200,299)}
REQUIRED={"round","client_id","resource_group","selected","current_cosine_to_mean","effective_cosine_to_mean"}
COLORS={91001:"#2F5597",91002:"#2A9D8F",91003:"#E76F51"}

def digest(path:Path)->str:
    value=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""): value.update(chunk)
    return value.hexdigest()

def bin_start(round_id:int)->int|None:
    if round_id<2:return None
    if round_id<10:return 2
    return (round_id//10)*10

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-root",default=str(Path(__file__).resolve().parents[1])); parser.add_argument("--config",default="configs/stage9_system_seed_converged.json"); parser.add_argument("--output-dir",default="results/processed/stage9_directional_diagnostic"); parser.add_argument("--figure-dir",default="artifacts/figures/stage9_directional_diagnostic"); args=parser.parse_args()
    root=Path(args.project_root).resolve(); config=json.loads((root/args.config).read_text(encoding="utf-8")); manifest=combined_manifest(root,config)
    rows=[]; bin_rows=[]; integrity=[]
    for meta in manifest:
        path=Path(meta["system_log"]).resolve(); frame=pd.read_csv(path)
        if len(frame)!=15000 or not REQUIRED.issubset(frame.columns): raise ValueError(f"invalid system log: {meta['run_id']}")
        counts=frame.groupby("round").client_id.agg(["size","nunique"])
        if set(counts.index)!=set(range(300)) or not ((counts["size"]==50)&(counts["nunique"]==50)).all(): raise ValueError(f"coverage failed: {meta['run_id']}")
        frame=frame.copy(); frame["direction_shift"]=frame.effective_cosine_to_mean-frame.current_cosine_to_mean
        base={"run_id":meta["run_id"],"train_seed":int(meta["train_seed"]),"system_seed":int(meta["system_seed"]),"distance":meta["distance"]}
        for name,(start,end) in WINDOWS.items():
            part=frame[(frame["round"]>=start)&(frame["round"]<=end)&frame.resource_group.isin(["strong","straggler"])]
            grouped=part.groupby("resource_group").agg(selection_rate=("selected","mean"),current_cosine=("current_cosine_to_mean","mean"),effective_cosine=("effective_cosine_to_mean","mean"),direction_shift=("direction_shift","mean"))
            if set(grouped.index)!={"strong","straggler"}: raise ValueError(f"missing groups: {meta['run_id']}")
            rows.append({**base,"window":name,"straggler_direction_shift":grouped.loc["straggler","direction_shift"],"strong_direction_shift":grouped.loc["strong","direction_shift"],"effective_cosine_gap":grouped.loc["straggler","effective_cosine"]-grouped.loc["strong","effective_cosine"],"current_cosine_gap":grouped.loc["straggler","current_cosine"]-grouped.loc["strong","current_cosine"],"selection_disparity_pp":100*(grouped.loc["straggler","selection_rate"]-grouped.loc["strong","selection_rate"])})
        sub=frame[(frame["round"]>=2)&frame.resource_group.isin(["strong","straggler"])].copy(); sub["bin_start"]=sub["round"].map(bin_start)
        grouped=sub.groupby(["bin_start","resource_group"]).agg(selection_rate=("selected","mean"),effective_cosine=("effective_cosine_to_mean","mean")).reset_index()
        for start,part in grouped.groupby("bin_start"):
            p=part.set_index("resource_group")
            bin_rows.append({**base,"bin_start":int(start),"selection_disparity_pp":100*(p.loc["straggler","selection_rate"]-p.loc["strong","selection_rate"]),"effective_cosine_gap":p.loc["straggler","effective_cosine"]-p.loc["strong","effective_cosine"]})
        integrity.append({"run_id":meta["run_id"],"path":str(path),"bytes":path.stat().st_size,"sha256":digest(path)})
    cell=pd.DataFrame(rows).sort_values(["train_seed","system_seed","distance","window"]); bins=pd.DataFrame(bin_rows).sort_values(["train_seed","system_seed","distance","bin_start"])
    if len(cell)!=54 or len(bins)!=810: raise ValueError(f"unexpected derived coverage: {len(cell)}, {len(bins)}")
    margins=cell.groupby(["system_seed","distance","window"],as_index=False)[["straggler_direction_shift","strong_direction_shift","effective_cosine_gap","current_cosine_gap","selection_disparity_pp"]].mean()
    associations=[]
    for (train_seed,system_seed),part in bins[bins.distance=="euclidean"].groupby(["train_seed","system_seed"]):
        rho,_=stats.spearmanr(part.selection_disparity_pp,part.effective_cosine_gap)
        associations.append({"train_seed":train_seed,"system_seed":system_seed,"bins":len(part),"rho_selection_vs_effective_cosine_gap":rho})
    associations=pd.DataFrame(associations)
    early=margins[margins.window=="early_2-29"]
    eu=early[early.distance=="euclidean"].set_index("system_seed"); cosine=early[early.distance=="cosine"].set_index("system_seed")
    parts={"euclidean_straggler_shift_negative_each_system_seed":all(eu.loc[s,"straggler_direction_shift"]<0 for s in SYSTEM),"euclidean_effective_cosine_gap_negative_each_system_seed":all(eu.loc[s,"effective_cosine_gap"]<0 for s in SYSTEM),"cosine_selection_disparity_negative_each_system_seed":all(cosine.loc[s,"selection_disparity_pp"]<0 for s in SYSTEM)}
    supported=all(parts.values()); output=root/args.output_dir; figures=root/args.figure_dir; output.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    cell.to_csv(output/"cell_window_metrics.csv",index=False); bins.to_csv(output/"binned_metrics.csv",index=False); margins.to_csv(output/"system_seed_margins.csv",index=False); associations.to_csv(output/"euclidean_direction_associations.csv",index=False); pd.DataFrame(integrity).to_csv(output/"raw_sha256.csv",index=False)
    plt.rcParams.update({"font.size":8,"axes.spines.top":False,"axes.spines.right":False,"figure.facecolor":"white","axes.facecolor":"white"})
    fig,axes=plt.subplots(1,3,figsize=(8.7,3.0),sharex=True)
    specs=[("straggler_direction_shift","Straggler directional shift"),("effective_cosine_gap","Straggler - strong effective cosine"),("selection_disparity_pp","Straggler - strong selection rate (pp)")]
    for ax,(column,title) in zip(axes,specs):
        for seed in SYSTEM:
            p=early[early.system_seed==seed].set_index("distance").loc[DIST]
            ax.plot(range(3),p[column],marker="o",lw=1.2,color=COLORS[seed],label=str(seed))
        ax.axhline(0,color="#777777",lw=.8); ax.set_xticks(range(3),["Euclid.","Norm.","Cosine"]); ax.set_title(title); ax.grid(alpha=.15)
    axes[-1].legend(title="System seed",frameon=False,fontsize=7,title_fontsize=7); fig.tight_layout()
    for ext in ("png","pdf","svg"): fig.savefig(figures/f"early_directional_diagnostic.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)
    result={"status":"complete","verified_cells":27,"cell_window_rows":54,"binned_rows":810,"support_parts":parts,"stable_direction_exclusion_supported":supported,"median_euclidean_rho":float(associations.rho_selection_vs_effective_cosine_gap.median()),"claim_action":"retain_opposing_direction_mechanism" if supported else "downgrade_to_mixed_directional_evidence"}
    (output/"analysis.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))

if __name__=="__main__":main()
