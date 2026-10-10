"""Independent raw-log verification for Stage 8; does not read analysis tables."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results" / "manifests" / "stage8_a05_converged_5seed.csv"
OUTPUT = ROOT / "results" / "processed" / "stage8_a05_converged_5seed" / "independent_verification.json"
EPOCH = re.compile(r"^Epoch\s+(\d+)\s+.*?Test Acc:\s*([0-9.]+)", re.MULTILINE)


def main() -> None:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    if len(manifest) != 15:
        raise SystemExit("independent verifier expected 15 runs")
    findings = []
    for row in manifest:
        log = Path(row["output"])
        system = Path(row["system_log"])
        resolved = Path(row["resolved_config"])
        text = log.read_text(encoding="utf-8", errors="replace")
        epochs = [(int(a), float(b)) for a, b in EPOCH.findall(text)]
        if "Training finished on" not in text or [x[0] for x in epochs] != list(range(300)):
            raise SystemExit(f"log verification failed: {row['run_id']}")
        config = json.loads(resolved.read_text(encoding="utf-8"))
        keys = (config.get("seed_train"), config.get("seed_partition"), config.get("system_seed"), config.get("defense"), config.get("epochs"))
        expected = (int(row["train_seed"]), int(row["partition_seed"]), int(row["system_seed"]), row["vendor_aggregator"], 300)
        if keys != expected:
            raise SystemExit(f"resolved config verification failed: {row['run_id']}")
        counts = defaultdict(lambda: [0, set()])
        selected = defaultdict(lambda: [0, 0])
        with system.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for item in reader:
                round_id, client_id = int(item["round"]), int(item["client_id"])
                counts[round_id][0] += 1; counts[round_id][1].add(client_id)
                if 200 <= round_id <= 299 and item["resource_group"] in ("strong", "straggler"):
                    bucket = selected[item["resource_group"]]
                    bucket[0] += int(item["selected"]); bucket[1] += 1
        if set(counts) != set(range(300)) or any(size != 50 or len(ids) != 50 for size, ids in counts.values()):
            raise SystemExit(f"system CSV verification failed: {row['run_id']}")
        disparity = 100 * (selected["straggler"][0] / selected["straggler"][1] - selected["strong"][0] / selected["strong"][1])
        findings.append({"run_id": row["run_id"], "seed": int(row["train_seed"]), "distance": row["distance"],
                         "final_accuracy": epochs[-1][1], "late_disparity_pp": disparity, "rows": sum(v[0] for v in counts.values())})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"status": "passed", "verified_runs": 15, "findings": findings}, indent=2), encoding="utf-8")
    print("independent Stage 8 verification passed: 15/15")


if __name__ == "__main__":
    main()
