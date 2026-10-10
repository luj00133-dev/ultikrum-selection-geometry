"""Generate a hash-audited Stage 10 manuscript candidate from terminal artifacts.

The pre-transfer sources are never overwritten.  This program accepts only the
already rendered and independently verified Stage 10 terminal state, replaces
the exact frozen placeholders, and writes separate candidate sources for review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from render_stage10_manuscript_insert import (
    extract_margins,
    learning_bounds,
    terminal_state,
)


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed" / "stage10_cifar10_early_replication"
MAIN_PLACEHOLDERS = (
    "[[STAGE10_SENTENCE_PENDING]]",
    "[[STAGE10_CONTRIBUTION_PENDING]]",
    "[[STAGE10_METHODS_PENDING_FINAL_STATUS]]",
    "[[STAGE10_RESULTS_PENDING: INSERT ONLY AFTER 27/27 CELLS PASS INTEGRITY AND LEARNING GUARDS AND MAIN/INDEPENDENT ANALYSES AGREE.]]",
    "[[STAGE10_EXTERNAL_VALIDITY_PENDING]]",
    "[[STAGE10_CONCLUSION_PENDING]]",
)
SUPPLEMENT_PLACEHOLDERS = (
    "[[STAGE10_STATUS_PENDING]]",
    "[[STAGE10_SUPPLEMENTARY_RESULTS_PENDING]]",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def signed(value: float) -> str:
    return f"{value:+.2f}"


def exact_replace(text: str, placeholder: str, replacement: str) -> str:
    require(text.count(placeholder) == 1, f"expected exactly one placeholder: {placeholder}")
    return text.replace(placeholder, replacement)


def extract_abstract_sentence(insert: str, state: str) -> str:
    match = re.search(r"^\*\*Abstract sentence:\*\* (.+)$", insert, flags=re.MULTILINE)
    require(match is not None, "generated insert has no abstract sentence")
    sentence = match.group(1)
    if state == "invalid":
        require(sentence == "[OMIT STAGE 10 FROM THE ABSTRACT]", "invalid state has a result sentence")
        return ""
    require(sentence != "[OMIT STAGE 10 FROM THE ABSTRACT]", "valid terminal state omits result sentence")
    return sentence


def table(euclidean: dict[int, float], controls: dict[str, dict[int, float]]) -> str:
    lines = [
        "| System seed | Euclidean disparity (pp) | Normalized minus Euclidean (pp) | Cosine minus Euclidean (pp) |",
        "|---:|---:|---:|---:|",
    ]
    for seed in (91001, 91002, 91003):
        lines.append(
            f"| {seed} | {signed(euclidean[seed])} | "
            f"{signed(controls['normalized_euclidean'][seed])} | {signed(controls['cosine'][seed])} |"
        )
    return "\n".join(lines)


def render_blocks(
    state: str,
    analysis: dict[str, Any],
    independent: dict[str, Any],
    semantic: dict[str, Any],
    sentence: str,
    euclidean: dict[int, float],
    controls: dict[str, dict[int, float]],
    minimum_last10: float,
    minimum_gain: float,
    failed_learning: list[str],
) -> tuple[dict[str, str], dict[str, str]]:
    common_methods = (
        "All 27 frozen CIFAR-10/simpleCNN cells completed 60 rounds with exactly 50 client rows per round. "
        "The numeric verifier independently recomputed 54 cell windows, while the semantic verifier checked "
        f"{int(semantic['verified_rows']):,} client-round rows, logical lag, group assignments, and 38-of-50 selection cardinality."
    )
    crossed = signed(float(analysis["crossed_euclidean_disparity_pp"]))
    numeric_audit = (
        f"The minimum final-10-round accuracy was {minimum_last10:.4f}, the minimum final-minus-first-10-round "
        f"gain was {minimum_gain:+.4f}, and the independent maximum absolute disagreement was "
        f"{float(independent['max_absolute_error']):.3e}."
    )

    if state == "pass":
        contribution = (
            "6. A frozen CIFAR-10/simpleCNN transfer grid reproduces the early Euclidean disparity and both "
            "scale-removing control contrasts for every resource assignment, providing bounded cross-dataset/model evidence."
        )
        methods_prefix = common_methods + " Every cell passed both pre-specified learning-malfunction guards."
        decision = (
            "The frozen transfer gate **passes**. This supports cross-dataset/model transfer of the early "
            "scale-sensitive selection effect, but not converged persistence, attack robustness, physical-device behavior, "
            "or a deployable defense."
        )
        external = (
            "The frozen CIFAR-10/simpleCNN grid independently reproduces the early effect, extending the controlled "
            "evidence across one additional dataset/model pair."
        )
        conclusion = (
            "The CIFAR-10/simpleCNN transfer gate also passes, supporting a bounded cross-dataset/model early-stage "
            "effect while leaving converged persistence and real-system behavior unestablished."
        )
        status = "Pass; 27/27 complete, learning-valid, numerically and semantically verified"
    elif state == "fail":
        contribution = (
            "6. A complete, learning-valid CIFAR-10/simpleCNN grid fails the frozen transfer gate, establishing a "
            "negative-transfer boundary and preventing overgeneralization of the FashionMNIST mechanism diagnosis."
        )
        methods_prefix = common_methods + " Every cell passed both pre-specified learning-malfunction guards."
        decision = (
            "The frozen transfer gate **fails despite complete, learning-valid data**. This negative-transfer boundary "
            "prohibits a cross-dataset/model replication claim and stops outcome-repair expansion."
        )
        external = (
            "The complete CIFAR-10/simpleCNN grid does not satisfy the frozen transfer gate; therefore the positive "
            "mechanism evidence remains bounded to FashionMNIST/LeNet."
        )
        conclusion = (
            "The complete CIFAR-10/simpleCNN grid fails the frozen transfer gate, providing a negative-transfer boundary "
            "rather than cross-dataset/model replication."
        )
        status = "Complete Fail; 27/27 complete, learning-valid, numerically and semantically verified"
    else:
        require(failed_learning, "invalid terminal state has no failed learning cells")
        contribution = (
            "The frozen CIFAR-10/simpleCNN grid is retained as an integrity record but is not interpreted because at "
            "least one pre-specified learning-malfunction guard failed."
        )
        methods_prefix = common_methods + (
            f" {len(failed_learning)} cell(s) failed a pre-specified learning-malfunction guard; transfer-effect gates "
            "were therefore not evaluated."
        )
        decision = (
            "Stage 10 is **scientifically invalid for transfer interpretation** because a frozen learning-malfunction "
            "guard failed. No transfer-effect sign or boundary is reported, no cell is removed, and no threshold is changed."
        )
        external = "The CIFAR-10 grid is not used as external-validity evidence because its learning guard failed."
        conclusion = "Stage 10 is omitted from scientific transfer conclusions because its frozen learning guard failed."
        status = "Invalid for transfer interpretation; learning guard failed; effect gates not evaluated"

    if state in {"pass", "fail"}:
        result = (
            f"{methods_prefix} {numeric_audit}\n\n"
            f"The crossed early Euclidean straggler-minus-strong disparity was {crossed} pp. "
            "System-seed margins and paired controls were:\n\n"
            f"{table(euclidean, controls)}\n\n"
            f"{decision}\n\n"
            "![Stage 10 early disparity matrix](../artifacts/figures/stage10_cifar10_early_replication/primary_disparity_matrix.png)\n\n"
            "**Figure 6.** Frozen CIFAR-10 early-window disparity matrix. Rows are train/partition seeds, columns are "
            "resource-assignment seeds, and panels are the three pre-specified distance rules.\n\n"
            "![Stage 10 learning trajectories](../artifacts/figures/stage10_cifar10_early_replication/accuracy_trajectory.png)\n\n"
            "**Figure 7.** CIFAR-10 test-accuracy trajectories across the complete frozen grid. Lines show crossed means "
            "and bands show the observed seed range; these curves are learning-integrity evidence rather than independent replicates."
        )
        supplementary_result = (
            f"All 27 cells passed learning and integrity guards. {numeric_audit}\n\n"
            f"Crossed early Euclidean disparity: {crossed} pp.\n\n{table(euclidean, controls)}\n\n{decision}"
        )
    else:
        failed = ", ".join(f"`{item}`" for item in failed_learning)
        result = f"{methods_prefix} {numeric_audit}\n\n{decision} Failed learning cell(s): {failed}."
        supplementary_result = (
            f"All 27 cells completed the frozen artifact checks, but {len(failed_learning)} learning guard(s) failed: "
            f"{failed}. Transfer-effect gates were not evaluated and no effect values are reported. {numeric_audit}"
        )

    main = {
        MAIN_PLACEHOLDERS[0]: sentence,
        MAIN_PLACEHOLDERS[1]: contribution,
        MAIN_PLACEHOLDERS[2]: methods_prefix,
        MAIN_PLACEHOLDERS[3]: result,
        MAIN_PLACEHOLDERS[4]: external,
        MAIN_PLACEHOLDERS[5]: conclusion,
    }
    supplement = {
        SUPPLEMENT_PLACEHOLDERS[0]: status,
        SUPPLEMENT_PLACEHOLDERS[1]: supplementary_result,
    }
    return main, supplement


def validate_terminal(processed: Path, insert_path: Path) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], str]:
    paths = {
        "analysis": processed / "analysis.json",
        "independent_verification": processed / "independent_verification.json",
        "semantic_verification": processed / "semantic_verification.json",
        "insert_audit": processed / "manuscript_insert_audit.json",
    }
    for path in (*paths.values(), insert_path):
        require(path.is_file() and path.stat().st_size > 0, f"terminal input missing: {path}")
    analysis = read_json(paths["analysis"])
    independent = read_json(paths["independent_verification"])
    semantic = read_json(paths["semantic_verification"])
    audit = read_json(paths["insert_audit"])
    state = terminal_state(analysis, independent, semantic)
    require(audit.get("status") == "rendered" and audit.get("terminal_state") == state, "insert audit state mismatch")
    for key in ("analysis", "independent_verification", "semantic_verification"):
        require(digest(paths[key]) == audit["inputs"][key]["sha256"], f"insert input hash mismatch: {key}")
    require(digest(insert_path) == audit["output_sha256"], "insert output hash mismatch")
    insert = insert_path.read_text(encoding="utf-8")
    if state == "invalid":
        require("| Transfer-effect gates | Not evaluated |" in insert, "invalid insert leaks effect-gate interpretation")
    return state, analysis, independent, semantic, insert


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--main-source", default="manuscript/manuscript_v0.md")
    parser.add_argument("--supplement-source", default="manuscript/supplementary_v0.md")
    parser.add_argument("--main-output", default="manuscript/manuscript_stage10_candidate.md")
    parser.add_argument("--supplement-output", default="manuscript/supplementary_stage10_candidate.md")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    processed = root / "results" / "processed" / "stage10_cifar10_early_replication"
    insert_path = root / "manuscript" / "stage10_verified_insert.md"
    state, analysis, independent, semantic, insert = validate_terminal(processed, insert_path)
    euclidean, controls = extract_margins(processed, analysis)
    minimum_last10, minimum_gain = learning_bounds(processed)
    learning_rows = read_csv(processed / "learning_gates.csv")
    failed_learning = [row["run_id"] for row in learning_rows if row["learning_pass"].lower() != "true"]
    sentence = extract_abstract_sentence(insert, state)
    main_replacements, supplement_replacements = render_blocks(
        state, analysis, independent, semantic, sentence, euclidean, controls,
        minimum_last10, minimum_gain, failed_learning,
    )
    main_source = root / args.main_source
    supplement_source = root / args.supplement_source
    main_text = main_source.read_text(encoding="utf-8")
    supplement_text = supplement_source.read_text(encoding="utf-8")
    for placeholder, replacement in main_replacements.items():
        main_text = exact_replace(main_text, placeholder, replacement)
    for placeholder, replacement in supplement_replacements.items():
        supplement_text = exact_replace(supplement_text, placeholder, replacement)
    require("[[STAGE10_" not in main_text and "[[STAGE10_" not in supplement_text, "scientific placeholders remain")
    main_output = root / args.main_output
    supplement_output = root / args.supplement_output
    main_output.write_text(main_text, encoding="utf-8")
    supplement_output.write_text(supplement_text, encoding="utf-8")
    audit = {
        "status": "candidate_generated",
        "terminal_state": state,
        "inputs": {
            "main_source": {"path": str(main_source), "sha256": digest(main_source)},
            "supplement_source": {"path": str(supplement_source), "sha256": digest(supplement_source)},
            "insert": {"path": str(insert_path), "sha256": digest(insert_path)},
            "manuscript_insert_audit": {"path": str(processed / "manuscript_insert_audit.json"), "sha256": digest(processed / "manuscript_insert_audit.json")},
        },
        "outputs": {
            "main": {"path": str(main_output), "sha256": digest(main_output)},
            "supplement": {"path": str(supplement_output), "sha256": digest(supplement_output)},
        },
        "author_placeholders_preserved": True,
    }
    audit_path = processed / "manuscript_candidate_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

