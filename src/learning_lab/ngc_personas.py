"""Pinned Singapore Extended assets, local provenance and aggregate-only auditing.

The manifest records a locally measured digest; it is not an NVIDIA signature.
No persona records or credentials are returned by these metadata helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import stat

import pyarrow.parquet as pq

from .personas import OCEAN

RESOURCE = "nvidia/nemotron-personas/nemotron-personas-dataset-en_sg"
VERSION = "0.0.1"
LOCALE = "en_SG"
FILENAME = "en_SG.parquet"
CATALOGUE_URL = "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg"
FILES_URL = (
    "https://api.ngc.nvidia.com/v2/org/nvidia/team/nemotron-personas/resources/"
    f"nemotron-personas-dataset-en_sg/versions/{VERSION}/files"
)
LICENSE_URL = "https://assets.ngc.nvidia.com/products/api-catalog/legal/Personas-Dataset-NVIDIA-Training-Dataset-License-Agreement-2025-11-26.pdf"


def install_folder(root: Path) -> Path:
    return root / "data" / "ngc" / LOCALE / VERSION


def file_sha256(path: Path) -> str:
    """Read ordinary files without following a final-component symlink."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("The installed asset must be an ordinary file")
        return hashlib.file_digest(source, "sha256").hexdigest()


def audit_source(path: Path) -> dict:
    """Check every original ID and trait object, emitting aggregates only."""
    parquet = pq.ParquetFile(path)
    names = parquet.schema_arrow.names
    missing = {"uuid", *OCEAN} - set(names)
    if missing:
        raise ValueError("Required source fields missing: " + ", ".join(sorted(missing)))
    counts = {key: {"valid": 0, "missing": 0, "invalid": 0, "minimum_t_score": None,
                    "maximum_t_score": None} for key in OCEAN}
    identities, missing_ids, row_count = set(), 0, 0
    for batch in parquet.iter_batches(batch_size=2048, columns=["uuid", *OCEAN]):
        for row in batch.to_pylist():
            row_count += 1
            identity = row["uuid"]
            if isinstance(identity, str) and identity:
                identities.add(identity)
            else:
                missing_ids += 1
            for key in OCEAN:
                count, raw = counts[key], row[key]
                if raw is None or raw == "":
                    count["missing"] += 1
                    continue
                try:
                    value = json.loads(raw) if isinstance(raw, str) else raw
                    score = value["t_score"]
                    valid = (
                        isinstance(value, dict) and type(score) in (int, float)
                        and math.isfinite(score)
                        and all(isinstance(value.get(field), str) and bool(value[field].strip())
                                for field in ("label", "description"))
                    )
                except (ValueError, TypeError, KeyError, OverflowError):
                    valid = False
                if not valid:
                    count["invalid"] += 1
                    continue
                count["valid"] += 1
                low, high = count["minimum_t_score"], count["maximum_t_score"]
                count["minimum_t_score"] = score if low is None else min(low, score)
                count["maximum_t_score"] = score if high is None else max(high, score)
    return {
        "row_count": row_count,
        "distinct_ids": len(identities),
        "missing_ids": missing_ids,
        "columns": [{"name": field.name, "type": str(field.type)} for field in parquet.schema_arrow],
        "row_groups": parquet.num_row_groups,
        "ocean": counts,
        "ready": row_count > 0 and len(identities) == row_count and missing_ids == 0
        and all(value["valid"] == row_count for value in counts.values()),
    }


@dataclass(frozen=True)
class NgcLocation:
    path: Path | None
    revision: str
    origin: str
    reason: str | None = None
    audit: dict | None = None
    sha256: str | None = None


def _signature(path: Path) -> tuple:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Pinned source and provenance must be ordinary files")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


@lru_cache(maxsize=8)
def _cached_source_audit(path: Path, signature: tuple) -> dict:
    return audit_source(path)


def audit_installed_source(path: Path) -> dict:
    """Audit the actual selected asset, invalidating readiness when its bytes change."""
    resolved = path.resolve(strict=True)
    return _cached_source_audit(resolved, _signature(resolved))


@lru_cache(maxsize=8)
def _verify_pinned(path: Path, manifest_path: Path, asset_signature: tuple,
                   manifest_signature: tuple) -> dict:
    # Signatures invalidate the cache after either file changes; never trust a filename alone.
    if manifest_signature[2] > 64 * 1024:
        raise ValueError("Pinned source provenance is too large")
    manifest = json.loads(manifest_path.read_text())
    expected = {"format": "persona-lab-ngc-install-v1", "resource": RESOURCE,
                "version": VERSION, "locale": LOCALE, "filename": FILENAME}
    if not isinstance(manifest, dict) or any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Pinned source provenance has an unsupported resource or revision")
    digest = manifest.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Pinned source provenance has an invalid SHA-256")
    if type(manifest.get("size_bytes")) is not int or manifest["size_bytes"] != asset_signature[2]:
        raise ValueError("Pinned source byte size differs from its provenance")
    if file_sha256(path) != digest:
        raise ValueError("Pinned source SHA-256 differs from its provenance")
    # Recompute the behavioural audit from actual bytes rather than trusting claimed readiness.
    actual = audit_installed_source(path)
    if not actual["ready"]:
        raise ValueError("Pinned source contains missing or invalid original IDs or OCEAN values")
    if manifest.get("audit") != actual:
        raise ValueError("Pinned source audit differs from its provenance")
    return manifest


def resolve_ngc(root: Path) -> NgcLocation:
    """Operator override, existing SDK managed asset, then verified pinned install.

    An explicit missing override fails closed. Browser inputs never select paths.
    """
    revision = os.getenv("LAB_NGC_PERSONAS_REVISION") or "local-unversioned"
    override = os.getenv("LAB_NGC_PERSONAS_PATH")
    if override is not None:
        path = Path(override).expanduser() if override.strip() else None
        return NgcLocation(path if path and path.is_file() else None, revision, "operator-override",
                           None if path and path.is_file() else "Explicit NGC persona path is not installed locally")
    managed = Path(os.getenv("DATA_DESIGNER_MANAGED_ASSETS_PATH")
                   or str(Path.home() / ".data-designer/managed-assets")) / "datasets" / FILENAME
    if managed.is_file():
        return NgcLocation(managed, revision, "designer-managed")
    folder = install_folder(root)
    path, manifest_path = folder / FILENAME, folder / "provenance.json"
    if not path.exists() and not manifest_path.exists():
        return NgcLocation(None, VERSION, "pinned-install", "Dataset is not installed locally")
    try:
        manifest = verify_pinned_install(root)
    except (OSError, ValueError, TypeError, KeyError):
        return NgcLocation(None, VERSION, "pinned-install",
                           "Pinned NGC source or provenance is missing, invalid or inconsistent; rerun its audit")
    return NgcLocation(path, VERSION, "pinned-install", audit=manifest["audit"], sha256=manifest["sha256"])


def verify_pinned_install(root: Path) -> dict:
    """Verify the fixed local original independently of operator path overrides."""
    folder = install_folder(root)
    path, manifest_path = folder / FILENAME, folder / "provenance.json"
    if path.resolve().parent != folder.absolute() or manifest_path.resolve().parent != folder.absolute():
        raise ValueError("Pinned source installation contains a symbolic-link path")
    return _verify_pinned(path, manifest_path, _signature(path), _signature(manifest_path))
