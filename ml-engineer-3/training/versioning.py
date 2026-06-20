"""Stage 3 — Version.

Makes the dataset immutable + reproducible:
  * compute a content hash over the sorted (relpath, sha256) manifest
  * upload images/labels + manifest.json to datasets/<version>/ in storage
  * record a dataset_versions row

The content hash means an identical dataset never creates a new version, and any
model can be traced back to the exact bytes it trained on.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

from common.config import get_settings
from common.db import session_scope
from common.logging import get_logger
from common.models import DatasetVersion
from common.storage import Storage

log = get_logger("training.versioning")


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _build_manifest(root: Path) -> tuple[dict[str, str], dict]:
    manifest: dict[str, str] = {}
    counts = {"n_images": 0, "n_train": 0, "n_val": 0}
    for split in ("train", "val"):
        for img in sorted((root / "images" / split).glob("*")):
            if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            rel = f"images/{split}/{img.name}"
            manifest[rel] = _sha256_file(img)
            counts["n_images"] += 1
            counts[f"n_{split}"] += 1
        for lbl in sorted((root / "labels" / split).glob("*.txt")):
            manifest[f"labels/{split}/{lbl.name}"] = _sha256_file(lbl)
    return manifest, counts


def version_dataset(dataset_dir: str | Path, class_counts: dict[str, int]) -> str:
    s = get_settings()
    storage = Storage()
    root = Path(dataset_dir)

    manifest, counts = _build_manifest(root)
    content_hash = hashlib.sha256(
        "\n".join(f"{k}:{v}" for k, v in sorted(manifest.items())).encode()
    ).hexdigest()
    version = f"ds_{dt.datetime.now(dt.timezone.utc):%Y%m%d_%H%M%S}_{content_hash[:8]}"

    # upload data + manifest
    for rel in manifest:
        storage.put_file(s.s3_bucket_datasets, f"{version}/{rel}", root / rel)
    manifest_uri = storage.put_json(
        s.s3_bucket_datasets,
        f"{version}/manifest.json",
        {
            "version": version,
            "content_hash": content_hash,
            "files": manifest,
            **counts,
            "class_counts": class_counts,
        },
    )

    with session_scope() as db:
        db.add(
            DatasetVersion(
                version=version,
                content_hash=content_hash,
                manifest_uri=manifest_uri,
                n_images=counts["n_images"],
                n_train=counts["n_train"],
                n_val=counts["n_val"],
                class_counts=class_counts,
            )
        )

    log.info("dataset_versioned", version=version, content_hash=content_hash[:12], **counts)
    return version
