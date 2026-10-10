"""Independently verify the Stage 10 terminal results report and its provenance."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed" / "stage10_cifar10_early_replication"
REPORT = ROOT / "docs" / "stage10_cifar10_early_replication_results.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def state_from_verified_inputs(analysis: dict[str, Any], independent: dict[str, Any], semantic: dict[str, Any]) -> str:
    require(independent.get("status") == "passed" and independent.get("verified_cells") == 27, "numeric verification is not terminal")
    require(independent.get("verified_cell_windows") == 54, "numeric window coverage mismatch")
    require(semantic.get("status") == "passed" and semantic.get("verified_rows") == 81000, "semantic verification is not terminal")
    require(semantic.get("verified_selected_rows") == 61560, "semantic selected-row coverage mismatch")
    require(analysis.get("gate_parts") == independent.get("gate_parts"), "main and independent gate parts differ")
    require(analysis.get("transfer_gate_pass") == independent.get("transfer_gate_pass"), "main and independent decisions differ")
    if not analysis.get("all_learning_gates_passed"):
        require(analysis.get("status") == "learning_gate_failed", "learning-invalid analysis status mismatch")
        return "invalid"
    require(analysis.get("status") == "complete", "learning-valid analysis status mismatch")
    return "pass" if analysis.get("transfer_gate_pass") else "fail"


def verify_text(
    text: str,
    state: str,
    analysis: dict[str, Any],
    failed_learning: list[str],
) -> None:
    require(f"Terminal state: **{state}**." in text, "terminal state missing from report")
    require("does not establish Byzantine/backdoor robustness" in text, "claim boundary missing")
    crossed = f"{float(analysis['crossed_euclidean_disparity_pp']):+.2f} pp"
    euclidean = {int(key): float(value) for key, value in analysis["euclidean_system_margins_pp"].items()}
    controls = {
        name: {int(key): float(value) for key, value in values.items()}
        for name, values in analysis["control_system_margins_pp"].items()
    }
    if state in {"pass", "fail"}:
        require(crossed in text, "crossed disparity missing from report")
        for seed in (91001, 91002, 91003):
            row = (
                f"| {seed} | {euclidean[seed]:+.2f} | "
                f"{controls['normalized_euclidean'][seed]:+.2f} | {controls['cosine'][seed]:+.2f} |"
            )
            require(row in text, f"system-seed report row mismatch: {seed}")
        labels = {
            "all_learning_gates_passed": "All 27 learning guards pass",
            "crossed_euclidean_at_least_5pp": "Crossed Euclidean disparity is at least +5 pp",
            "euclidean_positive_each_system_seed": "Euclidean margin is positive for every system seed",
            "both_controls_negative_each_system_seed": "Both controls are negative for every system seed",
        }
        for key, label in labels.items():
            expected = f"| {label} | {'Pass' if analysis['gate_parts'][key] else 'Fail'} |"
            require(expected in text, f"gate ledger mismatch: {key}")
        if state == "pass":
            require("bounded cross-dataset/model support" in text, "pass report lacks bounded transfer wording")
        else:
            require("negative-transfer boundary" in text, "fail report lacks negative-transfer wording")
    else:
        require(failed_learning, "invalid report has no failed learning cells")
        require("Transfer-effect gates were **not evaluated**" in text, "invalid report lacks non-evaluation boundary")
        require(crossed not in text, "invalid report leaks crossed disparity")
        require("Crossed Euclidean disparity is at least +5 pp" not in text, "invalid report leaks effect gate")
        require("| 91001 |" not in text and "| 91002 |" not in text and "| 91003 |" not in text, "invalid report leaks system margins")
        for run_id in failed_learning:
            require(f"`{run_id}`" in text, f"failed learning cell missing: {run_id}")


def main() -> None:
    audit_path = PROCESSED / "results_report_audit.json"
    require(audit_path.is_file() and REPORT.is_file(), "terminal results report or audit is missing")
    audit = read_json(audit_path)
    require(audit.get("status") == "rendered", "results report audit is not terminal")
    expected_inputs = {
        "analysis": PROCESSED / "analysis.json",
        "independent": PROCESSED / "independent_verification.json",
        "semantic": PROCESSED / "semantic_verification.json",
        "manifest": ROOT / "results" / "manifests" / "stage10_cifar10_early_replication.csv",
        "system_seed_margins": PROCESSED / "system_seed_margins.csv",
        "control_system_seed_margins": PROCESSED / "control_system_seed_margins.csv",
        "learning_gates": PROCESSED / "learning_gates.csv",
    }
    require(set(audit.get("inputs", {})) == set(expected_inputs), "results report audit input set mismatch")
    for name, item in audit["inputs"].items():
        path = Path(item["path"])
        require(path.resolve() == expected_inputs[name].resolve(), f"results report input path mismatch: {name}")
        require(path.is_file() and digest(path) == item["sha256"], f"results report input hash mismatch: {name}")
    require(Path(audit.get("output", "")).resolve() == REPORT.resolve(), "results report output path mismatch")
    require(digest(REPORT) == audit.get("output_sha256"), "results report output hash mismatch")
    analysis = read_json(PROCESSED / "analysis.json")
    independent = read_json(PROCESSED / "independent_verification.json")
    semantic = read_json(PROCESSED / "semantic_verification.json")
    state = state_from_verified_inputs(analysis, independent, semantic)
    require(audit.get("terminal_state") == state, "results report terminal-state mismatch")
    failed_learning = [row["run_id"] for row in read_csv(PROCESSED / "learning_gates.csv") if row["learning_pass"].lower() != "true"]
    verify_text(REPORT.read_text(encoding="utf-8"), state, analysis, failed_learning)
    result = {
        "status": "passed",
        "terminal_state": state,
        "verified_report_sha256": digest(REPORT),
        "verified_input_count": len(audit["inputs"]),
        "invalid_branch_effect_values_suppressed": True,
    }
    output = PROCESSED / "results_report_verification.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
