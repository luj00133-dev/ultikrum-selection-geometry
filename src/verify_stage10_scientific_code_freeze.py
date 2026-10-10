"""Verify the frozen Stage 10 scientific protocol and implementation ledger."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from .freeze_stage10_scientific_code import MANIFEST_SHA256, digest_bytes, normalized_digest, scientific_paths
except ImportError:
    from freeze_stage10_scientific_code import MANIFEST_SHA256, digest_bytes, normalized_digest, scientific_paths


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs" / "stage10_scientific_code_freeze.json"
OUTPUT = ROOT / "results" / "processed" / "stage10_cifar10_early_replication" / "scientific_code_verification.json"


def verify(root: Path, ledger_path: Path) -> dict:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("status") != "frozen" or ledger.get("manifest_sha256") != MANIFEST_SHA256:
        raise ValueError("scientific-code ledger header mismatch")
    expected = {path.relative_to(root).as_posix(): path for path in scientific_paths(root)}
    rows = ledger.get("files", [])
    indexed = {row["path"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed) != set(expected):
        raise ValueError("scientific-code ledger path set mismatch")
    for relative, path in expected.items():
        row = indexed[relative]
        value = path.read_bytes()
        if len(value) != int(row["bytes"]):
            raise ValueError(f"scientific-code byte count mismatch: {relative}")
        if digest_bytes(value) != row["sha256"]:
            raise ValueError(f"scientific-code SHA-256 mismatch: {relative}")
        if normalized_digest(path) != row["normalized_text_sha256"]:
            raise ValueError(f"scientific-code normalized hash mismatch: {relative}")
    manifest = root / "results" / "manifests" / "stage10_cifar10_early_replication.csv"
    if digest_bytes(manifest.read_bytes()) != MANIFEST_SHA256:
        raise ValueError("formal manifest hash mismatch")
    return {
        "status": "passed",
        "verified_files": len(expected),
        "ledger_sha256": digest_bytes(ledger_path.read_bytes()),
        "manifest_sha256": MANIFEST_SHA256,
    }


def main() -> None:
    result = verify(ROOT, LEDGER)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

