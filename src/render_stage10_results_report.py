"""Render a human-readable, hash-audited Stage 10 terminal results report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from render_stage10_manuscript_insert import extract_margins, learning_bounds, terminal_state


ROOT = Path(__file__).resolve().parents[1]
SYSTEM = (91001, 91002, 91003)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def signed(value: float) -> str:
    return f"{value:+.2f}"


def render(
    state: str,
    analysis: dict[str, Any],
    independent: dict[str, Any],
    semantic: dict[str, Any],
    euclidean: dict[int, float],
    controls: dict[str, dict[int, float]],
    minimum_last10: float,
    minimum_gain: float,
    failed_learning: list[str],
    manifest_sha256: str,
) -> str:
    lines = [
        "# Stage 10 CIFAR-10 early-effect replication: terminal results",
        "",
        "## Frozen scope and integrity",
        "",
        "- Grid: 3 train/partition seeds × 3 system-assignment seeds × 3 distance rules = 27 cells.",
        "- Training: CIFAR-10/simpleCNN, FedSGD, 50 clients, Dirichlet alpha = 0.5, NoAttack, 60 rounds.",
        "- Primary window: rounds 2--29; secondary window: rounds 30--59.",
        f"- Formal manifest SHA-256: `{manifest_sha256}`.",
        f"- Numeric verifier: `{independent['status']}`, 27 cells, 54 windows, maximum error {float(independent['max_absolute_error']):.3e}.",
        f"- Semantic verifier: `{semantic['status']}`, {int(semantic['verified_rows']):,} client-round rows and {int(semantic['verified_selected_rows']):,} selected rows.",
        f"- Minimum final-10-round accuracy: {minimum_last10:.4f}; minimum final-minus-first-10 gain: {minimum_gain:+.4f}.",
        "",
        "## Terminal decision",
        "",
        f"Terminal state: **{state}**.",
        "",
    ]
    if state in {"pass", "fail"}:
        lines.extend([
            f"Crossed early Euclidean straggler-minus-strong selection disparity: **{signed(float(analysis['crossed_euclidean_disparity_pp']))} pp**.",
            "",
            "| System seed | Euclidean disparity (pp) | Normalized minus Euclidean (pp) | Cosine minus Euclidean (pp) |",
            "|---:|---:|---:|---:|",
        ])
        for seed in SYSTEM:
            lines.append(
                f"| {seed} | {signed(euclidean[seed])} | {signed(controls['normalized_euclidean'][seed])} | {signed(controls['cosine'][seed])} |"
            )
        lines.extend(["", "### Frozen gate ledger", "", "| Gate | Result |", "|---|---|"])
        labels = {
            "all_learning_gates_passed": "All 27 learning guards pass",
            "crossed_euclidean_at_least_5pp": "Crossed Euclidean disparity is at least +5 pp",
            "euclidean_positive_each_system_seed": "Euclidean margin is positive for every system seed",
            "both_controls_negative_each_system_seed": "Both controls are negative for every system seed",
        }
        for key, label in labels.items():
            lines.append(f"| {label} | {'Pass' if analysis['gate_parts'][key] else 'Fail'} |")
        lines.extend(["", "## Consequence", ""])
        if state == "pass":
            lines.append(
                "The frozen transfer gate passes. The early scale-sensitive selection effect has bounded cross-dataset/model support. "
                "Stage 9 nevertheless ruled out assignment-stable converged persistence, so lag-dose and attack expansion remain No-Go."
            )
        else:
            lines.append(
                "The complete, learning-valid grid fails the frozen transfer gate. This is a negative-transfer boundary; it prohibits a "
                "cross-dataset/model replication claim and stops outcome-repair expansion."
            )
    else:
        lines.extend([
            "At least one pre-specified learning-malfunction guard failed. Transfer-effect gates were **not evaluated**; no selection-effect "
            "signs, margins, contrasts, or figures are reported.",
            "",
            "Failed learning cells:",
            "",
        ])
        lines.extend(f"- `{run_id}`" for run_id in failed_learning)
        lines.extend([
            "",
            "## Consequence",
            "",
            "Stage 10 is scientifically invalid for transfer interpretation. No cell is removed and no threshold is changed. Any calibration "
            "or rerun requires a separately frozen protocol.",
        ])
    lines.extend([
        "",
        "## Claim boundary",
        "",
        "This experiment does not establish Byzantine/backdoor robustness, physical-device behavior, asynchronous-network performance, a "
        "fairness guarantee, a new defense, or a system-seed-invariant converged dual mechanism.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--processed-dir", default="results/processed/stage10_cifar10_early_replication")
    parser.add_argument("--output", default="docs/stage10_cifar10_early_replication_results.md")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    processed = root / args.processed_dir
    paths = {
        "analysis": processed / "analysis.json",
        "independent": processed / "independent_verification.json",
        "semantic": processed / "semantic_verification.json",
        "manifest": root / "results/manifests/stage10_cifar10_early_replication.csv",
        "system_seed_margins": processed / "system_seed_margins.csv",
        "control_system_seed_margins": processed / "control_system_seed_margins.csv",
        "learning_gates": processed / "learning_gates.csv",
    }
    for path in paths.values():
        if not path.is_file():
            raise ValueError(f"terminal report input missing: {path}")
    analysis = read_json(paths["analysis"])
    independent = read_json(paths["independent"])
    semantic = read_json(paths["semantic"])
    state = terminal_state(analysis, independent, semantic)
    euclidean, controls = extract_margins(processed, analysis)
    minimum_last10, minimum_gain = learning_bounds(processed)
    failed_learning = [row["run_id"] for row in read_csv(processed / "learning_gates.csv") if row["learning_pass"].lower() != "true"]
    if state == "invalid" and not failed_learning:
        raise ValueError("invalid terminal state has no failed learning cells")
    report = render(
        state, analysis, independent, semantic, euclidean, controls,
        minimum_last10, minimum_gain, failed_learning, digest(paths["manifest"]),
    )
    output = root / args.output
    output.write_text(report, encoding="utf-8")
    audit = {
        "status": "rendered",
        "terminal_state": state,
        "inputs": {name: {"path": str(path), "sha256": digest(path)} for name, path in paths.items()},
        "output": str(output),
        "output_sha256": digest(output),
    }
    audit_path = processed / "results_report_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
