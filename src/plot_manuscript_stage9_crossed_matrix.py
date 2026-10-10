"""Create the manuscript's crossed early-disparity figure from verified Stage 9 data."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "processed" / "stage9_system_seed_converged" / "crossed_disparities.csv"
OUTPUT = ROOT / "artifacts" / "figures" / "manuscript"
TRAIN = (2026, 2027, 2028)
SYSTEM = (91001, 91002, 91003)
DISTANCES = (
    ("euclidean", "Euclidean"),
    ("normalized_euclidean", "Normalized Euclidean"),
    ("cosine", "Cosine"),
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load_matrices() -> dict[str, np.ndarray]:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["window"] == "2-29"]
    expected = {(train, system, distance) for train in TRAIN for system in SYSTEM for distance, _ in DISTANCES}
    found = {(int(row["train_seed"]), int(row["system_seed"]), row["distance"]) for row in rows}
    if len(rows) != 27 or found != expected:
        raise ValueError("verified early crossed table is not the expected 3x3x3 grid")
    lookup = {
        (int(row["train_seed"]), int(row["system_seed"]), row["distance"]): float(row["straggler_minus_strong_pp"])
        for row in rows
    }
    return {
        distance: np.asarray([[lookup[(train, system, distance)] for system in SYSTEM] for train in TRAIN])
        for distance, _ in DISTANCES
    }


def main() -> None:
    matrices = load_matrices()
    maximum = max(float(np.abs(matrix).max()) for matrix in matrices.values())
    limit = float(np.ceil(maximum / 5.0) * 5.0)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(1, 3, figsize=(7.25, 2.55), sharex=True, sharey=True)
    image = None
    for panel, (axis, (distance, title)) in enumerate(zip(axes, DISTANCES)):
        matrix = matrices[distance]
        image = axis.imshow(matrix, cmap="RdBu_r", vmin=-limit, vmax=limit, interpolation="nearest", aspect="equal")
        for row in range(3):
            for column in range(3):
                value = matrix[row, column]
                color = "white" if abs(value) >= 0.58 * limit else "#1f2933"
                axis.text(column, row, f"{value:+.1f}", ha="center", va="center", color=color, fontsize=7.2, fontweight="medium")
        axis.set_title(title, pad=7, fontweight="semibold")
        axis.set_xticks(range(3), [str(value) for value in SYSTEM])
        axis.set_yticks(range(3), [str(value) for value in TRAIN])
        axis.set_xlabel("System seed", labelpad=4)
        axis.text(-0.16, 1.08, chr(ord("a") + panel), transform=axis.transAxes, fontsize=9, fontweight="bold", va="top")
        axis.tick_params(length=0)
        for spine in axis.spines.values():
            spine.set_visible(False)
    axes[0].set_ylabel("Train / partition seed", labelpad=6)
    assert image is not None
    colorbar = fig.colorbar(image, ax=axes, orientation="horizontal", fraction=0.08, pad=0.20, aspect=35)
    colorbar.set_label("Straggler − strong selection rate (percentage points)", labelpad=4)
    colorbar.outline.set_linewidth(0.5)
    colorbar.ax.tick_params(length=2, width=0.5)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.84, bottom=0.28, wspace=0.18)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stem = OUTPUT / "crossed_early_disparity_matrix"
    for extension in ("png", "pdf", "svg"):
        fig.savefig(stem.with_suffix(f".{extension}"), dpi=400, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    audit = {
        "status": "rendered",
        "source": str(SOURCE),
        "source_sha256": digest(SOURCE),
        "window": "2-29",
        "cells": 27,
        "color_limit_pp": limit,
        "outputs": {
            extension: {
                "path": str(stem.with_suffix(f".{extension}")),
                "sha256": digest(stem.with_suffix(f".{extension}")),
            }
            for extension in ("png", "pdf", "svg")
        },
    }
    (OUTPUT / "crossed_early_disparity_matrix.audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
