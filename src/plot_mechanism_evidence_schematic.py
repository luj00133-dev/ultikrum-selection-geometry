"""Generate the manuscript mechanism-and-evidence schematic as vector graphics."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle
import numpy as np

BLUE="#2F5597"; TEAL="#2A9D8F"; ORANGE="#E76F51"; INK="#24313A"; GREY="#73808A"; LIGHT="#F4F7F9"; PALE="#EAF1F7"

def box(ax,xy,width,height,title,text,edge=BLUE,face=LIGHT):
    patch=FancyBboxPatch(xy,width,height,boxstyle="round,pad=0.018,rounding_size=0.025",linewidth=1.15,edgecolor=edge,facecolor=face)
    ax.add_patch(patch);x,y=xy
    ax.text(x+.028,y+height-.040,title,ha="left",va="top",fontsize=8.4,fontweight="bold",color=INK)
    ax.text(x+.028,y+height-.105,text,ha="left",va="top",fontsize=6.6,color=INK,linespacing=1.25)
    return patch

def arrow(ax,start,end,color=GREY,style="-|>",lw=1.15,connectionstyle="arc3"):
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle=style,mutation_scale=9,linewidth=lw,color=color,connectionstyle=connectionstyle))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--project-root",default=str(Path(__file__).resolve().parents[1]));parser.add_argument("--output-dir",default="artifacts/figures/manuscript");args=parser.parse_args()
    root=Path(args.project_root).resolve();out=root/args.output_dir;out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"figure.facecolor":"white"})
    fig=plt.figure(figsize=(11.4,4.85));grid=fig.add_gridspec(1,2,width_ratios=[1.02,1.28],wspace=.12);ax=fig.add_subplot(grid[0]);flow=fig.add_subplot(grid[1])

    # Panel a: geometric mechanism.
    ax.set_xlim(-.12,1.34);ax.set_ylim(-.30,.95);ax.set_aspect("equal");ax.axis("off")
    ax.text(-.10,.88,"a",fontsize=12,fontweight="bold",color=INK);ax.text(-.01,.88,"Scale-sensitive selection geometry",fontsize=10.5,fontweight="bold",color=INK)
    origin=np.array([.03,-.10]);rng=np.random.default_rng(7)
    cloud=np.column_stack([rng.normal(.95,.055,18),rng.normal(.35,.05,18)])
    ax.scatter(cloud[:,0],cloud[:,1],s=18,color=BLUE,alpha=.28,edgecolors="none",zorder=2)
    ax.add_patch(Circle((.95,.35),.14,facecolor=PALE,edgecolor=BLUE,alpha=.55,lw=1.0,zorder=1))
    ax.text(.94,.60,"current-update\nneighborhood",ha="center",va="bottom",fontsize=7.3,color=BLUE)
    strong=np.array([.98,.38]);current=np.array([1.03,.28]);effective=np.array([.69,.21]);unit=np.array([1.08,.33])
    arrow(ax,origin,strong,BLUE,lw=2.0);ax.text(.73,.54,"strong",fontsize=7.5,color=BLUE,fontweight="bold")
    arrow(ax,origin,current,GREY,lw=1.4);ax.text(1.12,.18,"straggler current",fontsize=6.8,color=GREY,ha="right")
    arrow(ax,origin,effective,ORANGE,lw=2.2);ax.text(.43,.02,"stale effective",fontsize=7.2,color=ORANGE,fontweight="bold")
    arrow(ax,current,effective,ORANGE,style="->",lw=1.2,connectionstyle="arc3,rad=.18")
    ax.text(.77,-.02,"scale contraction\n+ directional shift",ha="center",va="top",fontsize=7.0,color=ORANGE)
    ax.plot([effective[0],strong[0]],[effective[1],strong[1]],ls="--",lw=1.1,color=TEAL)
    ax.text(.80,.39,"smaller raw\nEuclidean distance",fontsize=6.8,color=TEAL,ha="center",va="bottom")
    ax.plot([current[0],unit[0]],[current[1],unit[1]],ls=":",color=GREY,lw=1)
    arrow(ax,origin,unit,TEAL,lw=1.8);ax.text(1.12,.52,"unit-norm control",fontsize=6.8,color=TEAL,ha="center")
    ax.text(-.06,-.255,"Raw Euclidean distance mixes radius and angle;\nnormalized and cosine controls remove the radial channel.",fontsize=6.9,color=INK,ha="left",va="bottom")

    # Panel b: frozen evidence chain.
    flow.set_xlim(0,1);flow.set_ylim(0,1);flow.axis("off");flow.text(.01,.96,"b",fontsize=12,fontweight="bold",color=INK);flow.text(.08,.96,"Crossed, auditable evidence chain",fontsize=10.5,fontweight="bold",color=INK)
    box(flow,(.02,.72),.28,.19,"Frozen design","3 train × 3 system seeds\n× 3 distance rules\nNoAttack; logical staleness",BLUE,PALE)
    box(flow,(.36,.72),.28,.19,"Raw integrity","Resolved config + completion\n300/60 sequential rounds\n50 clients; 38 selected",TEAL,"#ECF6F3")
    box(flow,(.70,.72),.28,.19,"Independent recomputation","Cell/window summaries\nfile-level SHA-256 hashes\nno pseudo-replication",ORANGE,"#FCF1ED")
    arrow(flow,(.30,.815),(.36,.815));arrow(flow,(.64,.815),(.70,.815))
    box(flow,(.02,.40),.28,.18,"Early window","Euclidean attraction\nscale-control attenuation",BLUE,PALE)
    box(flow,(.36,.40),.28,.18,"Converged boundary","system-seed-dependent decay\nlate invariance rejected",TEAL,"#ECF6F3")
    box(flow,(.70,.40),.28,.18,"Directional boundary","stale cosine shift exists\nstable exclusion rejected",ORANGE,"#FCF1ED")
    arrow(flow,(.16,.72),(.16,.58));arrow(flow,(.50,.72),(.50,.58));arrow(flow,(.84,.72),(.84,.58))
    box(flow,(.12,.09),.76,.19,"Supported claim boundary","Scale-sensitive early selection attraction is reproducible\nunder the frozen simulation. Persistence and directional\ninterpretation depend on stage and resource assignment.",INK,"#F7F7F5")
    arrow(flow,(.16,.40),(.32,.28));arrow(flow,(.50,.40),(.50,.28));arrow(flow,(.84,.40),(.68,.28))
    flow.text(.50,.025,"Not established: physical-device effects, attack robustness, fairness guarantees, or a new defense.",ha="center",va="bottom",fontsize=6.5,color=GREY)
    fig.subplots_adjust(left=.025,right=.985,bottom=.06,top=.96)
    for ext in ("png","pdf","svg"):fig.savefig(out/f"mechanism_evidence_schematic.{ext}",dpi=320,bbox_inches="tight")
    plt.close(fig)

if __name__=="__main__":main()
