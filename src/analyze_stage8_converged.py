"""Verify and analyze all Stage 8 raw results at the seed level."""
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
from scipy import stats


EPOCH_RE = re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)", re.MULTILINE)
WINDOWS = [(2, 29), (30, 99), (100, 199), (200, 299)]
REQUIRED_COLUMNS = {
    "round", "client_id", "resource_group", "effective_staleness",
    "effective_norm", "current_norm", "norm_ratio", "aggregator_score", "selected",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_accuracy(path: Path) -> tuple[np.ndarray, np.ndarray]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "Training finished on" not in text:
        raise ValueError(f"completion marker missing: {path}")
    pairs = [(int(epoch), float(acc)) for epoch, acc in EPOCH_RE.findall(text)]
    epochs = np.asarray([item[0] for item in pairs], dtype=int)
    accuracy = np.asarray([item[1] for item in pairs], dtype=float)
    if not np.array_equal(epochs, np.arange(300)):
        raise ValueError(f"epochs are not exactly 0..299: {path}")
    return epochs, accuracy


def mean_ci(values: list[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    sd = float(array.std(ddof=1)) if len(array) > 1 else float("nan")
    half = float(stats.t.ppf(0.975, len(array) - 1) * sd / np.sqrt(len(array))) if len(array) > 1 else float("nan")
    return {"n": len(array), "mean": mean, "sd": sd, "ci_low": mean - half, "ci_high": mean + half}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", default="results/manifests/stage8_a05_converged_5seed.csv")
    parser.add_argument("--config", default="configs/stage8_a05_converged.json")
    parser.add_argument("--output-dir", default="results/processed/stage8_a05_converged_5seed")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    manifest_path = root / args.manifest
    config = json.loads((root / args.config).read_text(encoding="utf-8"))
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 15 or len({row["run_id"] for row in rows}) != 15:
        raise ValueError("manifest must contain 15 unique Stage 8 rows")

    integrity = []
    group_records = []
    run_records = []
    for row in rows:
        paths = {key: Path(row[key]).resolve() for key in ("output", "system_log", "resolved_config")}
        for key, path in paths.items():
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"missing or empty {key}: {path}")
        resolved = json.loads(paths["resolved_config"].read_text(encoding="utf-8"))
        expected = {
            "epochs": 300, "seed_partition": int(row["partition_seed"]),
            "seed_train": int(row["train_seed"]), "dataset": row["dataset"],
            "model": row["model"], "distribution": row["distribution"],
            "dirichlet_alpha": float(row["dirichlet_alpha"]), "attack": "NoAttack",
            "defense": row["vendor_aggregator"], "system_profile": "four_tier",
            "system_seed": int(row["system_seed"]), "num_clients": 50,
        }
        for key, value in expected.items():
            if resolved.get(key) != value:
                raise ValueError(f"resolved mismatch {row['run_id']} {key}: {resolved.get(key)!r} != {value!r}")
        defense = ast.literal_eval(resolved["defense_params"])
        if defense != json.loads(row["defense_params"]):
            raise ValueError(f"defense parameters mismatch: {row['run_id']}")

        epochs, accuracy = parse_accuracy(paths["output"])
        terminal_slope = float(np.polyfit(epochs[-50:], accuracy[-50:], 1)[0])
        final_accuracy = float(accuracy[-1])
        convergence_pass = final_accuracy >= config["gates"]["final_accuracy_min"] and terminal_slope >= config["gates"]["terminal_slope_min"]

        frame = pd.read_csv(paths["system_log"])
        if len(frame) != 15000 or not REQUIRED_COLUMNS.issubset(frame.columns):
            raise ValueError(f"invalid system table shape/columns: {row['run_id']}")
        if set(frame["round"].unique()) != set(range(300)):
            raise ValueError(f"round coverage failure: {row['run_id']}")
        counts = frame.groupby("round")["client_id"].agg(["size", "nunique"])
        if not ((counts["size"] == 50) & (counts["nunique"] == 50)).all():
            raise ValueError(f"client-round uniqueness failure: {row['run_id']}")

        seed = int(row["train_seed"])
        for start, end in WINDOWS:
            window = frame[(frame["round"] >= start) & (frame["round"] <= end)]
            for group, values in window.groupby("resource_group", sort=True):
                group_records.append({
                    "run_id": row["run_id"], "seed": seed, "aggregator": row["aggregator"],
                    "distance": row["distance"], "window": f"{start}-{end}",
                    "resource_group": group, "observations": len(values),
                    "selection_rate": float(values["selected"].mean()),
                    "effective_norm_mean": float(values["effective_norm"].mean()),
                    "norm_ratio_mean": float(values["norm_ratio"].mean()),
                    "score_mean": float(values["aggregator_score"].mean()),
                })
        run_records.append({
            "run_id": row["run_id"], "seed": seed, "aggregator": row["aggregator"],
            "distance": row["distance"], "final_accuracy": final_accuracy,
            "terminal_slope": terminal_slope, "convergence_pass": convergence_pass,
        })
        for key, path in paths.items():
            integrity.append({"run_id": row["run_id"], "artifact": key, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})

    run_frame = pd.DataFrame(run_records)
    if not run_frame["convergence_pass"].all():
        failed = run_frame.loc[~run_frame["convergence_pass"], "run_id"].tolist()
        raise ValueError(f"convergence gate failed; analysis stopped: {failed}")
    group_frame = pd.DataFrame(group_records)
    pivot = group_frame.pivot_table(index=["seed", "aggregator", "distance", "window"], columns="resource_group", values="selection_rate").reset_index()
    pivot["straggler_minus_strong_pp"] = 100 * (pivot["straggler"] - pivot["strong"])

    contrasts = []
    for window in [f"{a}-{b}" for a, b in WINDOWS]:
        subset = pivot[pivot["window"] == window]
        values = {(int(row.seed), row.distance): float(row.straggler_minus_strong_pp) for row in subset.itertuples()}
        for seed in sorted(subset["seed"].unique()):
            euclidean = values[(int(seed), "euclidean")]
            for control in ("normalized_euclidean", "cosine"):
                contrasts.append({"seed": int(seed), "window": window, "control": control,
                                  "euclidean_disparity_pp": euclidean,
                                  "control_disparity_pp": values[(int(seed), control)],
                                  "control_minus_euclidean_pp": values[(int(seed), control)] - euclidean})
    contrast_frame = pd.DataFrame(contrasts)
    summary = {}
    for (window, control), values in contrast_frame.groupby(["window", "control"]):
        summary[f"{window}_{control}_minus_euclidean"] = mean_ci(values["control_minus_euclidean_pp"].tolist())
    for (window, distance), values in pivot.groupby(["window", "distance"]):
        summary[f"{window}_{distance}_disparity"] = mean_ci(values["straggler_minus_strong_pp"].tolist())

    output = root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    run_frame.to_csv(output / "run_convergence.csv", index=False)
    group_frame.to_csv(output / "group_window_metrics.csv", index=False)
    pivot.to_csv(output / "seed_disparities.csv", index=False)
    contrast_frame.to_csv(output / "paired_distance_contrasts.csv", index=False)
    pd.DataFrame(integrity).to_csv(output / "raw_sha256.csv", index=False)
    result = {
        "status": "verified_analysis_complete", "manifest_sha256": sha256(manifest_path),
        "runs": len(run_frame), "complete_seeds_per_distance": run_frame.groupby("distance")["seed"].nunique().to_dict(),
        "all_convergence_gates_passed": True, "windows": [f"{a}-{b}" for a, b in WINDOWS],
        "summary": summary,
    }
    (output / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
