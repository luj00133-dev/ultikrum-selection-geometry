"""Create the one-time Stage 10 scientific-code SHA-256 ledger before completion."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = (
    "configs/stage10_cifar10_early_replication.json",
    "docs/stage10_cifar10_early_replication_protocol.md",
    "results/manifests/stage10_cifar10_early_replication.csv",
    "scripts/run_stage10_cifar10_early_replication.ps1",
    "src/audit_stage10_progress.py",
    "src/analyze_stage10_cifar10.py",
    "src/verify_stage10_independent.py",
    "src/verify_stage10_semantics_independent.py",
    "src/verify_stage10_scientific_code_freeze.py",
)
MANIFEST_SHA256 = "bcfa8cc9204d537756dbddb25fb8feaf48154d707f06f8f256b1f92d11724f8a"


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalized_digest(path: Path) -> str | None:
    if path.suffix.lower() not in {".py", ".ps1", ".json", ".yaml", ".yml", ".md", ".csv"}:
        return None
    text = path.read_text(encoding="utf-8-sig")
    return digest_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def scientific_paths(root: Path) -> list[Path]:
    paths = {*(root / relative for relative in CORE)}
    vendor = root / "vendor" / "FLPoison"
    for pattern in ("*.py", "*.yaml", "*.yml"):
        paths.update(path for path in vendor.rglob(pattern) if path.is_file())
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"scientific code inputs missing: {missing}")
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def create(root: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError(f"scientific-code ledger already exists: {output}")
    files = []
    for path in scientific_paths(root):
        value = path.read_bytes()
        files.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": len(value),
            "sha256": digest_bytes(value),
            "normalized_text_sha256": normalized_digest(path),
        })
    manifest = root / "results" / "manifests" / "stage10_cifar10_early_replication.csv"
    if digest_bytes(manifest.read_bytes()) != MANIFEST_SHA256:
        raise ValueError("formal Stage 10 manifest hash changed")
    result = {
        "status": "frozen",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": MANIFEST_SHA256,
        "file_count": len(files),
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--output", default="configs/stage10_scientific_code_freeze.json")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    output = (root / args.output).resolve()
    print(json.dumps(create(root, output), indent=2))


if __name__ == "__main__":
    main()

