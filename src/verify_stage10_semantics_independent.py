"""Independent semantic verifier for terminal Stage 10 configs and system logs.

This verifier supplements, but does not modify, the frozen main analyzer and numeric
independent verifier. It checks implementation semantics that row-count checks alone
cannot establish: fixed resource assignments, logical lag, per-round cardinality,
selection ranks, norm ratios, complete hyperparameters, and formal-path isolation.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "stage10_cifar10_early_replication.json"
PROCESSED = ROOT / "results" / "processed" / "stage10_cifar10_early_replication"
FORMAL_ROOT = (ROOT / "results" / "raw" / "stage10_cifar10_early_replication").resolve()
MANIFEST_SHA256 = "bcfa8cc9204d537756dbddb25fb8feaf48154d707f06f8f256b1f92d11724f8a"
EPOCH_RE = re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)", re.MULTILINE)
GROUP_LAG = {"strong": 0, "medium": 0, "weak": 1, "straggler": 2}
GROUP_COUNTS = {"strong": 10, "medium": 15, "weak": 15, "straggler": 10}
REQUIRED_COLUMNS = {
    "round", "client_id", "resource_group", "requested_staleness", "effective_staleness",
    "current_norm", "effective_norm", "norm_ratio", "current_cosine_to_mean",
    "effective_cosine_to_mean", "stale_delta_norm", "aggregator_score", "selected",
    "selection_rank",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def validate_system_rows(
    rows: Iterable[dict[str, str]],
    groups: list[str],
    run_id: str,
    expected_rounds: int = 60,
    selected_per_round: int = 38,
) -> dict[str, int]:
    rows = list(rows)
    require(len(groups) == 50, f"{run_id}: meta groups must contain 50 clients")
    require(Counter(groups) == Counter(GROUP_COUNTS), f"{run_id}: group counts differ from four-tier profile")
    require(len(rows) == expected_rounds * 50, f"{run_id}: expected {expected_rounds*50} system rows")
    require(REQUIRED_COLUMNS.issubset(rows[0]), f"{run_id}: required system columns missing")
    by_round: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        round_id = int(row["round"])
        client_id = int(row["client_id"])
        require(0 <= round_id < expected_rounds, f"{run_id}: out-of-range round {round_id}")
        require(0 <= client_id < 50, f"{run_id}: out-of-range client {client_id}")
        group = row["resource_group"]
        require(group == groups[client_id], f"{run_id}: group assignment changed for client {client_id}")
        requested = int(row["requested_staleness"])
        effective = int(row["effective_staleness"])
        require(requested == GROUP_LAG[group], f"{run_id}: requested lag mismatch for {group}")
        require(effective == min(requested, round_id), f"{run_id}: effective lag mismatch r{round_id} c{client_id}")

        current_norm = float(row["current_norm"])
        effective_norm = float(row["effective_norm"])
        require(math.isfinite(current_norm) and current_norm >= 0, f"{run_id}: invalid current norm")
        require(math.isfinite(effective_norm) and effective_norm >= 0, f"{run_id}: invalid effective norm")
        if current_norm > 0:
            ratio = float(row["norm_ratio"])
            require(math.isfinite(ratio) and ratio >= 0, f"{run_id}: invalid norm ratio")
            require(math.isclose(ratio, effective_norm / current_norm, rel_tol=1e-7, abs_tol=1e-10), f"{run_id}: norm ratio mismatch")
        else:
            require(row["norm_ratio"] == "", f"{run_id}: zero current norm must have blank ratio")
        for column in ("current_cosine_to_mean", "effective_cosine_to_mean"):
            value = float(row[column])
            require(math.isfinite(value) and -1.000001 <= value <= 1.000001, f"{run_id}: invalid {column}")
        require(math.isfinite(float(row["stale_delta_norm"])) and float(row["stale_delta_norm"]) >= 0, f"{run_id}: invalid stale delta")
        require(math.isfinite(float(row["aggregator_score"])), f"{run_id}: missing or invalid aggregator score")
        selected = int(row["selected"])
        require(selected in (0, 1), f"{run_id}: selected must be binary")
        if selected:
            rank = int(row["selection_rank"])
            require(0 <= rank < selected_per_round, f"{run_id}: selected rank out of range")
        else:
            require(row["selection_rank"] == "", f"{run_id}: unselected client has a rank")
        by_round[round_id].append(row)

    require(set(by_round) == set(range(expected_rounds)), f"{run_id}: round coverage mismatch")
    for round_id, round_rows in by_round.items():
        clients = [int(row["client_id"]) for row in round_rows]
        require(len(round_rows) == 50 and set(clients) == set(range(50)), f"{run_id}: client coverage failed at round {round_id}")
        selected = [row for row in round_rows if int(row["selected"]) == 1]
        require(len(selected) == selected_per_round, f"{run_id}: selection cardinality failed at round {round_id}")
        require({int(row["selection_rank"]) for row in selected} == set(range(selected_per_round)), f"{run_id}: selection ranks failed at round {round_id}")
    return {"rows": len(rows), "rounds": len(by_round), "selected_rows": expected_rounds * selected_per_round}


def expected_resolved(row: dict[str, str]) -> dict[str, Any]:
    return {
        "epochs": 60,
        "seed": int(row["train_seed"]),
        "seed_partition": int(row["partition_seed"]),
        "seed_train": int(row["train_seed"]),
        "system_seed": int(row["system_seed"]),
        "algorithm": "FedSGD",
        "optimizer": "SGD",
        "momentum": 0.9,
        "weight_decay": 0.0001,
        "num_clients": 50,
        "batch_size": 128,
        "learning_rate": 0.01,
        "local_epochs": 1,
        "model": "simplecnn",
        "dataset": "CIFAR10",
        "distribution": "non-iid",
        "dirichlet_alpha": 0.5,
        "cache_partition": False,
        "num_workers": 0,
        "num_adv": 0,
        "attack": "NoAttack",
        "defense": row["vendor_aggregator"],
        "system_profile": "four_tier",
    }


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest_path = (ROOT / config["paths"]["manifest"]).resolve()
    require(digest(manifest_path) == MANIFEST_SHA256, "formal manifest hash changed")
    manifest = read_csv(manifest_path)
    require(len(manifest) == 27, "formal manifest does not contain 27 cells")
    main_analysis = json.loads((PROCESSED / "analysis.json").read_text(encoding="utf-8"))
    independent = json.loads((PROCESSED / "independent_verification.json").read_text(encoding="utf-8"))
    require(main_analysis.get("verified_cells") == 27 and main_analysis.get("all_integrity_checks_passed") is True, "main analysis is not terminal and complete")
    require(independent.get("status") == "passed" and independent.get("verified_cells") == 27, "numeric independent verification did not pass")
    main_hashes = {
        (row["run_id"], row["artifact"]): row["sha256"]
        for row in read_csv(PROCESSED / "raw_sha256.csv")
    }
    require(len(main_hashes) == 81, "main artifact hash ledger must contain 27 x 3 rows")
    checked = []
    for row in manifest:
        run_id = row["run_id"]
        output = Path(row["output"]).resolve()
        system_log = Path(row["system_log"]).resolve()
        resolved_path = Path(row["resolved_config"]).resolve()
        require(all(under(path, FORMAL_ROOT) for path in (output, system_log, resolved_path)), f"{run_id}: artifact escaped formal root")
        require("smoke" not in str(output).lower() and "smoke" not in str(system_log).lower(), f"{run_id}: smoke path entered formal manifest")
        for artifact, path in (("output", output), ("system_log", system_log), ("resolved_config", resolved_path)):
            require(path.is_file() and path.stat().st_size > 0, f"{run_id}: missing {artifact}")
            require(main_hashes.get((run_id, artifact)) == digest(path), f"{run_id}: {artifact} hash differs from main ledger")

        text = output.read_text(encoding="utf-8", errors="replace")
        epochs = [int(value) for value, _ in EPOCH_RE.findall(text)]
        require("Training finished on" in text and epochs == list(range(60)), f"{run_id}: training completion failed")
        resolved = json.loads(resolved_path.read_text(encoding="utf-8"))
        for key, value in expected_resolved(row).items():
            require(resolved.get(key) == value, f"{run_id}: resolved {key} mismatch")
        require(ast.literal_eval(resolved["defense_params"]) == config["defense_params"], f"{run_id}: defense params mismatch")

        meta_path = system_log.with_name(system_log.stem + ".meta.json")
        require(meta_path.is_file() and meta_path.stat().st_size > 0, f"{run_id}: system meta missing")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        require(meta.get("profile") == "four_tier", f"{run_id}: meta profile mismatch")
        require(meta.get("system_seed") == int(row["system_seed"]), f"{run_id}: meta system seed mismatch")
        require(meta.get("staleness_by_group") == GROUP_LAG, f"{run_id}: meta lag map mismatch")
        coverage = validate_system_rows(read_csv(system_log), list(meta["groups"]), run_id)
        checked.append({"run_id": run_id, **coverage, "meta_sha256": digest(meta_path)})

    result = {
        "status": "passed",
        "verified_cells": len(checked),
        "verified_rows": sum(row["rows"] for row in checked),
        "verified_rounds": sum(row["rounds"] for row in checked),
        "verified_selected_rows": sum(row["selected_rows"] for row in checked),
        "selection_cardinality_per_round": 38,
        "resource_group_counts": GROUP_COUNTS,
        "logical_lag_map": GROUP_LAG,
        "formal_root": str(FORMAL_ROOT),
        "smoke_excluded": True,
        "cells": checked,
    }
    path = PROCESSED / "semantic_verification.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
