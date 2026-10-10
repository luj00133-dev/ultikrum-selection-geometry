"""Build the deterministic Stage 8 converged alpha=0.5 manifest."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


SEEDS = [2026, 2027, 2028, 2029, 2030]
AGGREGATORS = ["MultiKrum", "MultiKrumNormalized", "MultiKrumCosine"]
EXPECTED_ROWS = 300 * 50
RESULT_ROOT_NAME = "stage8_a05_converged_5seed"
FIELDS = [
    "run_id", "stage", "dataset", "model", "algorithm", "data_condition",
    "partition", "distribution", "dirichlet_alpha", "system_condition",
    "system_profile", "partition_seed", "train_seed", "system_seed",
    "resource_assignment_seed", "aggregator", "vendor_aggregator", "distance",
    "defense_params", "attack", "rounds", "expected_system_rows", "base_config",
    "output", "system_log", "resolved_config", "completion_marker", "status",
]


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Stage 8 config must be a JSON object")
    return value


def resolve_root(config: dict[str, Any], project_root: str | Path | None = None) -> Path:
    return Path(project_root or config.get("project_root") or Path(__file__).parents[1]).resolve()


def inside(root: Path, value: str | Path) -> Path:
    path = Path(value)
    path = (path if path.is_absolute() else root / path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {path}") from exc
    return path


def registered_aggregators(root: Path) -> set[str]:
    pattern = re.compile(r"@aggregator_registry\s*\nclass\s+(\w+)", re.MULTILINE)
    names: set[str] = set()
    requested = root / "vendor" / "FLPoison" / "aggregators"
    fallback = Path(__file__).resolve().parents[1] / "vendor" / "FLPoison" / "aggregators"
    source_root = requested if requested.is_dir() else fallback
    for source in sorted(source_root.glob("*.py")):
        names.update(pattern.findall(source.read_text(encoding="utf-8")))
    return names


def validate(config: dict[str, Any], root: Path) -> None:
    if config.get("experiment") != "stage8_a05_converged_5seed":
        raise ValueError("unexpected Stage 8 experiment name")
    fixed = {
        "dataset": "FashionMNIST", "model": "lenet", "algorithm": "FedSGD",
        "rounds": 300, "num_clients": 50, "attack": "NoAttack",
        "system_condition": "heterogeneous", "system_profile": "four_tier",
        "system_seed": 91001,
    }
    for key, expected in fixed.items():
        if config.get(key) != expected:
            raise ValueError(f"Stage 8 requires {key}={expected!r}")
    if config.get("seeds") != SEEDS:
        raise ValueError(f"Stage 8 seeds must be {SEEDS}")
    condition = config.get("data_condition", {})
    if condition != {
        "name": "a05", "partition": "dirichlet", "distribution": "non-iid",
        "dirichlet_alpha": 0.5,
    }:
        raise ValueError("Stage 8 is fixed to Dirichlet alpha=0.5")
    controls = config.get("distance_controls", [])
    if [item.get("aggregator") for item in controls] != AGGREGATORS:
        raise ValueError("Stage 8 distance controls or order changed")
    if [item.get("distance") for item in controls] != [
        "euclidean", "normalized_euclidean", "cosine"
    ]:
        raise ValueError("Stage 8 distance labels changed")
    params = config.get("defense_params")
    if params != {"avg_percentage": 0.76, "enable_check": False, "num_score_neighbors": 39}:
        raise ValueError("Stage 8 frozen defense parameters changed")
    missing = set(AGGREGATORS) - registered_aggregators(root)
    if missing:
        raise ValueError(f"unregistered aggregators: {sorted(missing)}")
    if inside(root, config["paths"]["result_root"]).name != RESULT_ROOT_NAME:
        raise ValueError("Stage 8 must use its dedicated result root")
    inside(root, config["base_config"])
    gates = config.get("gates", {})
    if gates != {
        "final_accuracy_min": 0.60,
        "terminal_window_rounds": 50,
        "terminal_slope_min": -0.0015,
        "minimum_complete_seeds": 5,
    }:
        raise ValueError("Stage 8 frozen gates changed")


def build_rows(config: dict[str, Any], project_root: str | Path | None = None) -> list[dict[str, Any]]:
    root = resolve_root(config, project_root)
    validate(config, root)
    result_root = inside(root, config["paths"]["result_root"])
    base_config = inside(root, config["base_config"])
    condition = config["data_condition"]
    params = json.dumps(config["defense_params"], sort_keys=True, separators=(",", ":"))
    rows = []
    for seed in SEEDS:
        for control in config["distance_controls"]:
            run_id = f"stage8_a05_r300_{control['name']}_s{seed}"
            output = result_root / f"{run_id}.log"
            rows.append({
                "run_id": run_id, "stage": config["experiment"],
                "dataset": config["dataset"], "model": config["model"],
                "algorithm": config["algorithm"], "data_condition": condition["name"],
                "partition": condition["partition"], "distribution": condition["distribution"],
                "dirichlet_alpha": condition["dirichlet_alpha"],
                "system_condition": config["system_condition"],
                "system_profile": config["system_profile"], "partition_seed": seed,
                "train_seed": seed, "system_seed": config["system_seed"],
                "resource_assignment_seed": config["system_seed"],
                "aggregator": control["aggregator"],
                "vendor_aggregator": control["aggregator"], "distance": control["distance"],
                "defense_params": params, "attack": config["attack"],
                "rounds": config["rounds"], "expected_system_rows": EXPECTED_ROWS,
                "base_config": str(base_config), "output": str(output),
                "system_log": str(output.with_suffix(".system.csv")),
                "resolved_config": str(output.with_suffix(".resolved.json")),
                "completion_marker": "Training finished on", "status": "planned",
            })
    return rows


def write_rows(rows: list[dict[str, Any]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--project-root")
    parser.add_argument("--out")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve() if args.project_root else Path(__file__).parents[1]
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    config = load_config(config_path)
    rows = build_rows(config, root)
    if args.dry_run:
        print(json.dumps(rows, indent=2) if args.json else "\n".join(row["run_id"] for row in rows))
        return
    output = inside(root, args.out or config["paths"]["manifest"])
    write_rows(rows, output)
    print(f"wrote {len(rows)} Stage 8 cells to {output}")


if __name__ == "__main__":
    main()
