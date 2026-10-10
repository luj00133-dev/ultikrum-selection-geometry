"""Render a bounded manuscript insert from terminal, independently verified Stage 10 outputs.

The renderer is frozen before Stage 10 completion.  It never reads partial raw cells
and refuses to run unless the main analyzer and independent verifier are terminal and
decision-consistent.  It writes a reviewable insert; it does not edit the manuscript.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_SEEDS = (91001, 91002, 91003)
CONTROLS = ("normalized_euclidean", "cosine")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict[str, Any]:
    require(path.is_file() and path.stat().st_size > 0, f"missing terminal artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file() and path.stat().st_size > 0, f"missing terminal artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def signed(value: float, digits: int = 2) -> str:
    return f"{value:+.{digits}f}"


def terminal_state(
    analysis: dict[str, Any], independent: dict[str, Any], semantic: dict[str, Any]
) -> str:
    require(analysis.get("verified_cells") == 27, "main analysis does not cover 27 cells")
    require(analysis.get("all_integrity_checks_passed") is True, "main integrity gate did not pass")
    require(analysis.get("status") in {"complete", "learning_gate_failed"}, "main analysis is not terminal")
    require(independent.get("status") == "passed", "independent verification did not pass")
    require(independent.get("verified_cells") == 27, "independent verifier does not cover 27 cells")
    require(independent.get("verified_cell_windows") == 54, "independent verifier does not cover 54 cell windows")
    require(semantic.get("status") == "passed", "independent semantic verification did not pass")
    require(semantic.get("verified_cells") == 27, "semantic verifier does not cover 27 cells")
    require(semantic.get("verified_rows") == 81000, "semantic verifier does not cover 81,000 rows")
    require(semantic.get("verified_rounds") == 1620, "semantic verifier does not cover 1,620 cell-rounds")
    require(semantic.get("verified_selected_rows") == 61560, "semantic verifier selection coverage mismatch")
    require(semantic.get("selection_cardinality_per_round") == 38, "semantic verifier cardinality mismatch")
    require(semantic.get("smoke_excluded") is True, "semantic verifier did not establish smoke exclusion")
    require(analysis.get("gate_parts") == independent.get("gate_parts"), "main and independent gate parts differ")
    require(
        analysis.get("all_learning_gates_passed") == independent.get("all_learning_gates_passed"),
        "main and independent learning decisions differ",
    )
    require(
        analysis.get("transfer_gate_pass") == independent.get("transfer_gate_pass"),
        "main and independent transfer decisions differ",
    )
    if not analysis["all_learning_gates_passed"]:
        require(analysis["status"] == "learning_gate_failed", "learning failure has an inconsistent main status")
        require(analysis["transfer_gate_pass"] is False, "invalid learning grid cannot pass transfer")
        return "invalid"
    require(analysis["status"] == "complete", "learning-valid grid must have complete status")
    return "pass" if analysis["transfer_gate_pass"] else "fail"


def extract_margins(
    processed: Path, analysis: dict[str, Any]
) -> tuple[dict[int, float], dict[str, dict[int, float]]]:
    margin_rows = read_csv(processed / "system_seed_margins.csv")
    control_rows = read_csv(processed / "control_system_seed_margins.csv")
    euclidean = {
        int(row["system_seed"]): float(row["selection_disparity_pp"])
        for row in margin_rows
        if row["window"] == "primary_2-29" and row["distance"] == "euclidean"
    }
    controls = {
        control: {
            int(row["system_seed"]): float(row["control_minus_euclidean_pp"])
            for row in control_rows
            if row["window"] == "primary_2-29" and row["control"] == control
        }
        for control in CONTROLS
    }
    require(set(euclidean) == set(SYSTEM_SEEDS), "Euclidean system margins are incomplete")
    require(all(set(values) == set(SYSTEM_SEEDS) for values in controls.values()), "control system margins are incomplete")
    for seed in SYSTEM_SEEDS:
        require(abs(euclidean[seed] - float(analysis["euclidean_system_margins_pp"][str(seed)])) <= 1e-10, f"Euclidean margin mismatch for {seed}")
        for control in CONTROLS:
            require(abs(controls[control][seed] - float(analysis["control_system_margins_pp"][control][str(seed)])) <= 1e-10, f"{control} margin mismatch for {seed}")
    return euclidean, controls


def learning_bounds(processed: Path) -> tuple[float, float]:
    rows = read_csv(processed / "learning_gates.csv")
    require(len(rows) == 27, "learning-gate table does not contain 27 cells")
    return (
        min(float(row["last10_accuracy"]) for row in rows),
        min(float(row["last10_minus_first10_accuracy"]) for row in rows),
    )


def render_insert(
    state: str,
    analysis: dict[str, Any],
    independent: dict[str, Any],
    euclidean: dict[int, float],
    controls: dict[str, dict[int, float]],
    minimum_last10: float,
    minimum_gain: float,
) -> str:
    if state == "pass":
        abstract_sentence = (
            "On CIFAR-10/simpleCNN, the frozen transfer grid independently reproduces "
            "the early effect and both metric-control contrasts across all three assignments."
        )
        decision = (
            "The frozen transfer gate **passes**. This supports cross-dataset/model transfer of "
            "the early scale-sensitive selection effect, but not converged persistence, attacks, "
            "physical-device behavior, or a deployable defense."
        )
    elif state == "fail":
        abstract_sentence = (
            "On CIFAR-10/simpleCNN, the complete frozen grid fails the transfer gate, "
            "delimiting rather than broadening the FashionMNIST finding."
        )
        decision = (
            "The frozen transfer gate **fails despite complete, learning-valid data**. This is a "
            "negative-transfer boundary. It does not invalidate the audited FashionMNIST result, "
            "but it prohibits a cross-dataset/model replication claim and stops further expansion."
        )
    else:
        abstract_sentence = ""
        decision = (
            "The Stage 10 grid is **scientifically invalid for transfer interpretation** because "
            "at least one frozen learning-malfunction guard failed. No transfer effect or boundary "
            "is reported, no cell is removed, and no threshold is changed. A separately frozen "
            "calibration would be required before any new grid."
        )

    lines = [
        "# Verified Stage 10 manuscript insert",
        "",
        f"**Terminal state:** `{state}`",
        "",
        f"**Abstract sentence:** {abstract_sentence or '[OMIT STAGE 10 FROM THE ABSTRACT]'}",
        "",
        "## Methods-status sentence",
        "",
        (
            "All 27 CIFAR-10/simpleCNN cells completed the frozen 60-round crossed grid, passed "
            "exact artifact and client-round coverage checks, and were recomputed by the independent verifier."
        ),
        "",
        "## Results",
        "",
    ]
    if state != "invalid":
        lines.extend([
            (
                "The crossed early Euclidean straggler-minus-strong disparity was "
                f"{signed(float(analysis['crossed_euclidean_disparity_pp']))} pp. System-seed margins and "
                "paired control contrasts are shown below."
            ),
            "",
            "| System seed | Euclidean disparity (pp) | Normalized minus Euclidean (pp) | Cosine minus Euclidean (pp) |",
            "|---:|---:|---:|---:|",
        ])
        for seed in SYSTEM_SEEDS:
            lines.append(
                f"| {seed} | {signed(euclidean[seed])} | "
                f"{signed(controls['normalized_euclidean'][seed])} | {signed(controls['cosine'][seed])} |"
            )
        lines.extend(["", decision, ""])
    else:
        lines.extend([decision, ""])

    lines.extend([
        "## Audit statement",
        "",
        f"The minimum final-10-round accuracy was {minimum_last10:.4f}, and the minimum final-minus-first-10-round gain was {minimum_gain:+.4f}. "
        f"The independent verifier covered {independent['verified_cells']} cells and {independent['verified_cell_windows']} cell windows; "
        f"its maximum absolute numerical disagreement was {float(independent['max_absolute_error']):.3e}.",
        "",
        "## Gate ledger",
        "",
        "| Frozen condition | Result |",
        "|---|---|",
    ])
    if state == "invalid":
        lines.extend([
            "| All 27 learning guards pass | Fail |",
            "| Transfer-effect gates | Not evaluated |",
        ])
    else:
        labels = {
            "all_learning_gates_passed": "All 27 learning guards pass",
            "crossed_euclidean_at_least_5pp": "Crossed Euclidean disparity is at least +5 pp",
            "euclidean_positive_each_system_seed": "Euclidean margin is positive for every system seed",
            "both_controls_negative_each_system_seed": "Both control contrasts are negative for every system seed",
        }
        for key, label in labels.items():
            lines.append(f"| {label} | {'Pass' if analysis['gate_parts'][key] else 'Fail'} |")
    lines.extend(["", "This generated insert must be reviewed before copying into the manuscript; it does not replace author confirmation of declarations.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--processed-dir", default="results/processed/stage10_cifar10_early_replication")
    parser.add_argument("--output", default="manuscript/stage10_verified_insert.md")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    processed = root / args.processed_dir
    analysis_path = processed / "analysis.json"
    independent_path = processed / "independent_verification.json"
    semantic_path = processed / "semantic_verification.json"
    analysis = read_json(analysis_path)
    independent = read_json(independent_path)
    semantic = read_json(semantic_path)
    state = terminal_state(analysis, independent, semantic)
    euclidean, controls = extract_margins(processed, analysis)
    minimum_last10, minimum_gain = learning_bounds(processed)
    rendered = render_insert(state, analysis, independent, euclidean, controls, minimum_last10, minimum_gain)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    audit = {
        "status": "rendered",
        "terminal_state": state,
        "output": str(output),
        "inputs": {
            "analysis": {"path": str(analysis_path), "sha256": digest(analysis_path)},
            "independent_verification": {"path": str(independent_path), "sha256": digest(independent_path)},
            "semantic_verification": {"path": str(semantic_path), "sha256": digest(semantic_path)},
            "system_seed_margins": {"path": str(processed / "system_seed_margins.csv"), "sha256": digest(processed / "system_seed_margins.csv")},
            "control_system_seed_margins": {"path": str(processed / "control_system_seed_margins.csv"), "sha256": digest(processed / "control_system_seed_margins.csv")},
            "learning_gates": {"path": str(processed / "learning_gates.csv"), "sha256": digest(processed / "learning_gates.csv")},
        },
        "output_sha256": digest(output),
    }
    (processed / "manuscript_insert_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
