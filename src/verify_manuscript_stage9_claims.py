"""Verify that manuscript Stage 9 numbers and claim boundaries match audited outputs.

This check is intentionally independent of the scientific analyzers.  It reads their
terminal artifacts and the manuscript source, then fails on missing/incorrectly
rounded values, unsupported claim language, unresolved citation keys, or premature
removal of the Stage 10 placeholders.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "manuscript_v0.md"
SUPPLEMENTARY = ROOT / "manuscript" / "supplementary_v0.md"
BIBLIOGRAPHY = ROOT / "manuscript" / "references.bib"
STAGE9 = ROOT / "results" / "processed" / "stage9_system_seed_converged"
TRAJECTORY = ROOT / "results" / "processed" / "stage9_time_resolved"
DIRECTION = ROOT / "results" / "processed" / "stage9_directional_diagnostic"
STAGE10 = ROOT / "results" / "processed" / "stage10_cifar10_early_replication"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def signed(value: float, digits: int = 2) -> str:
    return f"{value:+.{digits}f}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def check_citations(text: str, bibliography: str) -> None:
    cited = set(re.findall(r"@([A-Za-z0-9:_-]+)", text))
    entries = set(re.findall(r"@\w+\{([^,]+),", bibliography))
    require(cited == entries, f"citation mismatch: cited-only={sorted(cited-entries)}, bib-only={sorted(entries-cited)}")


def check_abstract(text: str) -> int:
    match = re.search(r"(?s)## Abstract\s+(.*?)\s+\*\*Keywords", text)
    require(match is not None, "abstract block not found")
    pending = "[[STAGE10_SENTENCE_PENDING]]" in match.group(1)
    abstract = match.group(1).replace("[[STAGE10_SENTENCE_PENDING]]", "")
    words = re.findall(r"\b[\w'’-]+\b", abstract, flags=re.UNICODE)
    limit = 170 if pending else 200
    require(len(words) <= limit, f"abstract has {len(words)} words; limit for current state is {limit}")
    return len(words)


def check_stage9_tables(text: str) -> None:
    analysis = json.loads((STAGE9 / "analysis.json").read_text(encoding="utf-8"))
    require(analysis["status"] == "verified_analysis_complete", "Stage 9 analysis is not terminal")
    require(analysis["all_convergence_gates_passed"], "Stage 9 convergence gate failed")
    require(not analysis["lag_dose_gate_pass"], "manuscript boundary expects the frozen lag-dose No-Go")

    for window in ("2-29", "200-299"):
        result = analysis["decision"][window]
        for seed, value in result["euclidean_system_margins_pp"].items():
            require(signed(value) in text, f"missing Euclidean {window} seed {seed}: {signed(value)}")
        for control in ("normalized_euclidean", "cosine"):
            for seed, value in result["control_system_margins_pp"][control].items():
                require(signed(value) in text, f"missing {control} {window} seed {seed}: {signed(value)}")

    variance = read_csv(STAGE9 / "variance_decomposition.csv")
    wanted = {
        ("disparity", "euclidean"): "48.2%",
        ("paired_contrast", "normalized_euclidean"): "62.0%",
        ("paired_contrast", "cosine"): "42.1%",
    }
    for key, rendered in wanted.items():
        row = next(item for item in variance if (item["metric"], item["level"]) == key and item["window"] == "200-299")
        computed = f'{100 * float(row["system_share"]):.1f}%'
        require(computed == rendered and rendered in text, f"system-share mismatch for {key}: {computed}")


def check_trajectory(text: str) -> None:
    analysis = json.loads((TRAJECTORY / "analysis.json").read_text(encoding="utf-8"))
    require(analysis["status"] == "complete" and analysis["cell_bin_rows"] == 810, "trajectory analysis incomplete")
    for value in analysis["median_geometry_rho"].values():
        require(f"{float(value):.3f}" in text, f"missing trajectory rho {value}")
    rows = [row for row in read_csv(TRAJECTORY / "decay_summaries.csv") if row["distance"] == "euclidean"]
    starts = {row["system_seed"]: row["stabilization_start_round_abs_le_5"] for row in rows}
    require(starts == {"91001": "", "91002": "220.0", "91003": "250.0"}, f"unexpected neutrality starts: {starts}")
    require("rounds 220 and 250" in text, "manuscript does not report the verified neutrality starts")


def check_direction(text: str) -> None:
    analysis = json.loads((DIRECTION / "analysis.json").read_text(encoding="utf-8"))
    require(analysis["status"] == "complete", "directional analysis incomplete")
    require(not analysis["stable_direction_exclusion_supported"], "claim boundary no longer matches directional gate")
    require(f'{float(analysis["median_euclidean_rho"]):.3f}' in text, "missing directional median rho")
    rows = read_csv(DIRECTION / "system_seed_margins.csv")
    for seed in ("91001", "91002", "91003"):
        euclidean = next(row for row in rows if row["system_seed"] == seed and row["distance"] == "euclidean" and row["window"] == "early_2-29")
        cosine = next(row for row in rows if row["system_seed"] == seed and row["distance"] == "cosine" and row["window"] == "early_2-29")
        expected = (
            f'| {seed} | {signed(float(euclidean["straggler_direction_shift"]), 5)} '
            f'| {signed(float(euclidean["effective_cosine_gap"]), 5)} '
            f'| {signed(float(cosine["selection_disparity_pp"]), 2)} |'
        )
        require(expected in text, f"directional table mismatch for seed {seed}: {expected}")


def check_claim_language(text: str) -> None:
    prohibited = (
        "verified dual mechanism",
        "first work to identify krum selection bias",
        "proves real hardware",
        "guarantees fairness",
    )
    lower = text.lower()
    for phrase in prohibited:
        require(phrase not in lower, f"prohibited claim found: {phrase}")

    stage10_analysis = STAGE10 / "analysis.json"
    pending = "[[STAGE10_RESULTS_PENDING:" in text and "[[STAGE10_SENTENCE_PENDING]]" in text
    if not stage10_analysis.exists():
        require(pending, "Stage 10 is not terminal; manuscript placeholders must remain")


def check_figures(text: str) -> None:
    paths = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    require(len(paths) >= 5, f"expected at least five manuscript figures, found {len(paths)}")
    for raw in paths:
        path = (MANUSCRIPT.parent / raw).resolve()
        require(path.is_file() and path.stat().st_size > 0, f"missing manuscript figure: {path}")
    audit_path = ROOT / "artifacts" / "figures" / "manuscript" / "crossed_early_disparity_matrix.audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    source = Path(audit["source"])
    output = Path(audit["outputs"]["png"]["path"])
    require(source.is_file() and output.is_file(), "crossed-matrix provenance files are missing")
    file_hash = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    require(file_hash(source) == audit["source_sha256"], "crossed-matrix source hash mismatch")
    require(file_hash(output) == audit["outputs"]["png"]["sha256"], "crossed-matrix PNG hash mismatch")


def check_method_conventions(text: str) -> None:
    require(r"d_E(u,v)=\lVert u-v\rVert_2," in text, "Euclidean formula must use unsquared L2 distance")
    require(
        r"d_N(u,v)=\left\lVert\frac{u}{\lVert u\rVert_2}-\frac{v}{\lVert v\rVert_2}\right\rVert_2," in text,
        "normalized-Euclidean formula must use unsquared L2 distance",
    )
    require(r"\rVert_2^2" not in text, "manuscript contains an unsupported squared-L2 distance formula")
    require("retains the lowest \\(m=38\\) scores" in text, "Multi-Krum output cardinality is not explicit")
    require("contains the \\(q=39\\) nearest other updates" in text, "Krum score-neighbor count is not explicit")
    implementation = (ROOT / "vendor" / "FLPoison" / "aggregators" / "aggregator_utils.py").read_text(encoding="utf-8")
    require("updates[i] - updates[j])" in implementation and "np.linalg.norm" in implementation, "audited Euclidean implementation changed")
    supplement = SUPPLEMENTARY.read_text(encoding="utf-8")
    require("| Batch size | 128 |" in supplement, "supplementary batch size does not match formal runs")
    require("batch size 128" in text, "main manuscript omits the formal batch size")
    config_rows = [row for row in read_csv(STAGE9 / "raw_sha256.csv") if row["artifact"] == "resolved_config"]
    require(len(config_rows) == 27, "Stage 9 resolved-config ledger does not contain 27 cells")
    fields = set()
    for row in config_rows:
        config = json.loads(Path(row["path"]).read_text(encoding="utf-8"))
        fields.add((
            config.get("epochs"), config.get("batch_size"), config.get("learning_rate"),
            config.get("local_epochs"), config.get("optimizer"), config.get("momentum"),
            config.get("weight_decay"), config.get("num_clients"), config.get("num_adv"),
            config.get("cache_partition"), config.get("num_workers"),
        ))
    expected = {(300, 128, 0.01, 1, "SGD", 0.9, 0.0001, 50, 0, False, 0)}
    require(fields == expected, f"formal Stage 9 training configurations changed: {fields}")


def check_stage10_terminal_claims(text: str) -> str:
    analysis_path = STAGE10 / "analysis.json"
    if not analysis_path.exists():
        return "pending"
    required = {
        "analysis": analysis_path,
        "independent": STAGE10 / "independent_verification.json",
        "semantic": STAGE10 / "semantic_verification.json",
        "insert_audit": STAGE10 / "manuscript_insert_audit.json",
        "insert": ROOT / "manuscript" / "stage10_verified_insert.md",
    }
    for name, path in required.items():
        require(path.is_file() and path.stat().st_size > 0, f"terminal Stage 10 {name} is missing: {path}")
    analysis = json.loads(required["analysis"].read_text(encoding="utf-8"))
    independent = json.loads(required["independent"].read_text(encoding="utf-8"))
    semantic = json.loads(required["semantic"].read_text(encoding="utf-8"))
    audit = json.loads(required["insert_audit"].read_text(encoding="utf-8"))
    insert = required["insert"].read_text(encoding="utf-8")
    require(independent.get("status") == "passed" and independent.get("verified_cells") == 27, "Stage 10 numeric verification did not pass")
    require(semantic.get("status") == "passed" and semantic.get("verified_rows") == 81000, "Stage 10 semantic verification did not pass")
    require(audit.get("status") == "rendered", "Stage 10 manuscript insert was not audited")
    audit_inputs = audit.get("inputs", {})
    for name, key in (("analysis", "analysis"), ("independent", "independent_verification"), ("semantic", "semantic_verification")):
        require(key in audit_inputs, f"Stage 10 insert audit omits {key} input")
        require(
            hashlib.sha256(required[name].read_bytes()).hexdigest() == audit_inputs[key]["sha256"],
            f"Stage 10 insert {key} input hash mismatch",
        )
    require(hashlib.sha256(required["insert"].read_bytes()).hexdigest() == audit["output_sha256"], "Stage 10 insert hash mismatch")
    require("[[STAGE10_" not in text, "terminal Stage 10 placeholders remain in the main manuscript")
    supplement = SUPPLEMENTARY.read_text(encoding="utf-8")
    require("[[STAGE10_" not in supplement, "terminal Stage 10 placeholders remain in the supplement")
    state = audit["terminal_state"]
    require(state in {"pass", "fail", "invalid"}, f"unknown Stage 10 terminal state: {state}")
    sentence_match = re.search(r"^\*\*Abstract sentence:\*\* (.+)$", insert, flags=re.MULTILINE)
    require(sentence_match is not None, "generated Stage 10 abstract sentence missing")
    sentence = sentence_match.group(1)
    if state in {"pass", "fail"}:
        require(sentence in text, "main abstract does not contain the audited Stage 10 sentence")
        require(f"{float(analysis['crossed_euclidean_disparity_pp']):+.2f} pp" in text, "main manuscript omits crossed Stage 10 disparity")
        euclidean = {int(key): float(value) for key, value in analysis["euclidean_system_margins_pp"].items()}
        controls = {
            name: {int(key): float(value) for key, value in values.items()}
            for name, values in analysis["control_system_margins_pp"].items()
        }
        for seed in (91001, 91002, 91003):
            row = (
                f"| {seed} | {euclidean[seed]:+.2f} | "
                f"{controls['normalized_euclidean'][seed]:+.2f} | {controls['cosine'][seed]:+.2f} |"
            )
            require(row in text, f"main manuscript Stage 10 table mismatch for system seed {seed}")
        if state == "pass":
            require("cross-dataset/model" in text, "Stage 10 pass branch lacks transfer wording")
        else:
            require("negative-transfer boundary" in text, "Stage 10 fail branch lacks boundary wording")
    else:
        require(sentence == "[OMIT STAGE 10 FROM THE ABSTRACT]", "invalid branch must omit Stage 10 abstract result")
        require("scientifically invalid for transfer interpretation" in text, "main manuscript omits Stage 10 invalidity statement")
        require("Crossed Euclidean disparity is at least +5 pp" not in insert, "invalid insert reports an unevaluated effect gate")
        require("Euclidean margin is positive for every system seed" not in insert, "invalid insert reports an unevaluated system-margin gate")
        require("Both control contrasts are negative for every system seed" not in insert, "invalid insert reports unevaluated control gates")
        require("| Transfer-effect gates | Not evaluated |" in insert, "invalid insert omits the non-evaluation boundary")
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", default="manuscript/manuscript_v0.md")
    parser.add_argument("--supplement", default="manuscript/supplementary_v0.md")
    args = parser.parse_args()
    global MANUSCRIPT, SUPPLEMENTARY
    MANUSCRIPT = (ROOT / args.manuscript).resolve()
    SUPPLEMENTARY = (ROOT / args.supplement).resolve()
    text = MANUSCRIPT.read_text(encoding="utf-8")
    bibliography = BIBLIOGRAPHY.read_text(encoding="utf-8")
    check_citations(text, bibliography)
    abstract_words = check_abstract(text)
    check_stage9_tables(text)
    check_trajectory(text)
    check_direction(text)
    check_claim_language(text)
    check_figures(text)
    check_method_conventions(text)
    stage10_state = check_stage10_terminal_claims(text)
    if stage10_state != "pending":
        require(abstract_words <= 200, f"terminal abstract has {abstract_words} words")
    print(json.dumps({
        "status": "passed",
        "manuscript": str(MANUSCRIPT),
        "abstract_words_without_stage10": abstract_words,
        "stage9_numeric_claims_verified": True,
        "citation_sets_match": True,
        "figure_paths_and_crossed_matrix_provenance_verified": True,
        "distance_and_cardinality_conventions_verified": True,
        "all_27_training_hyperparameter_configs_verified": True,
        "stage10_state": stage10_state,
        "stage10_placeholders_required": stage10_state == "pending",
    }, indent=2))


if __name__ == "__main__":
    main()
