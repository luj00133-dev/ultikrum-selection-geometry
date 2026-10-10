"""Independently verify the de-identified scientific reproducibility bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

try:
    from .build_scientific_reproducibility_bundle import (
        TEXT_SUFFIXES,
        WINDOWS_ABSOLUTE,
        digest,
        is_forbidden,
        safe_relative,
    )
except ImportError:  # direct script execution
    from build_scientific_reproducibility_bundle import (
        TEXT_SUFFIXES,
        WINDOWS_ABSOLUTE,
        digest,
        is_forbidden,
        safe_relative,
    )


ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"^[0-9a-f]{64}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def bytes_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest_value, separator, name = line.partition("  ")
        require(separator == "  " and HEX.fullmatch(digest_value) is not None and name, f"invalid checksum line: {line}")
        require(name not in result, f"duplicate checksum entry: {name}")
        result[name] = digest_value
    return result


def verify(root: Path, audit_path: Path) -> dict[str, Any]:
    root = root.resolve()
    safe_relative(root, audit_path)
    audit = read_json(audit_path)
    require(audit.get("status") == "built", "bundle audit is not terminal")
    require(audit.get("raw_logs_included") is False, "bundle audit claims raw logs")
    bundle = Path(audit["bundle_dir"]).resolve()
    archive_path = Path(audit["zip"]).resolve()
    bundle_relative = safe_relative(root, bundle)
    safe_relative(root, archive_path)
    require(bundle.is_dir() and archive_path.is_file(), "bundle directory or ZIP is missing")
    require(digest(archive_path) == audit["zip_sha256"], "bundle ZIP hash mismatch")

    closure = root / "results" / "processed" / "stage10_cifar10_early_replication" / "scientific_closure.json"
    require(closure.is_file() and digest(closure) == audit["scientific_closure_sha256"], "scientific closure hash mismatch")
    inventory_path = bundle / "inventory.json"
    sums_path = bundle / "SHA256SUMS.txt"
    require(inventory_path.is_file() and sums_path.is_file(), "bundle inventory or checksum file is missing")
    inventory = read_json(inventory_path)
    require(inventory.get("terminal_state") == audit.get("terminal_state"), "bundle terminal-state mismatch")
    require(inventory.get("raw_logs_included") is False, "inventory claims raw logs")
    rows = inventory.get("files", [])
    require(isinstance(rows, list) and rows, "bundle inventory is empty")
    indexed = {}
    for row in rows:
        name = row["path"]
        require(name not in indexed, f"duplicate inventory path: {name}")
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts, f"unsafe inventory path: {name}")
        require(not is_forbidden(relative), f"forbidden inventory path: {name}")
        path = bundle / relative
        require(path.is_file(), f"inventoried file missing: {name}")
        require(path.stat().st_size == int(row["bytes"]), f"bundle size mismatch: {name}")
        require(digest(path) == row["bundled_sha256"], f"bundle file hash mismatch: {name}")
        if row.get("source_sha256") is not None:
            source = root / relative
            require(source.is_file() and digest(source) == row["source_sha256"], f"source file hash mismatch: {name}")
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8-sig")
            require(WINDOWS_ABSOLUTE.search(text) is None, f"private absolute path remains: {name}")
        indexed[name] = row

    actual = {
        path.relative_to(bundle).as_posix()
        for path in bundle.rglob("*")
        if path.is_file() and path.name not in {"inventory.json", "SHA256SUMS.txt"}
    }
    require(actual == set(indexed), f"bundle directory coverage mismatch: extra={sorted(actual-set(indexed))}, missing={sorted(set(indexed)-actual)}")
    sums = parse_sums(sums_path)
    expected_sums = {name: row["bundled_sha256"] for name, row in indexed.items()}
    expected_sums["inventory.json"] = digest(inventory_path)
    require(sums == expected_sums, "SHA256SUMS content mismatch")

    disk_files = {path.relative_to(bundle).as_posix(): digest(path) for path in bundle.rglob("*") if path.is_file()}
    zip_hashes = {}
    prefix = bundle_relative.name + "/"
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            require(info.filename.startswith(prefix), f"ZIP entry escapes bundle root: {info.filename}")
            name = info.filename[len(prefix):]
            require(name not in zip_hashes, f"duplicate ZIP entry: {name}")
            relative = Path(name)
            require(not relative.is_absolute() and ".." not in relative.parts and not is_forbidden(relative), f"unsafe ZIP entry: {name}")
            zip_hashes[name] = bytes_digest(archive.read(info))
    require(zip_hashes == disk_files, "ZIP and bundle directory differ")
    return {
        "status": "passed",
        "terminal_state": audit["terminal_state"],
        "verified_inventory_files": len(indexed),
        "verified_zip_files": len(zip_hashes),
        "scientific_closure_sha256": audit["scientific_closure_sha256"],
        "zip_sha256": audit["zip_sha256"],
        "raw_and_smoke_excluded": True,
        "private_windows_paths_absent": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--audit", default="artifacts/submission/reproducibility_bundle_audit.json")
    parser.add_argument("--output", default="artifacts/submission/reproducibility_bundle_verification.json")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    audit_path = (root / args.audit).resolve()
    result = verify(root, audit_path)
    output = (root / args.output).resolve()
    safe_relative(root, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
