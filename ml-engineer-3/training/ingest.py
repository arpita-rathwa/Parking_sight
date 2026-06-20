"""Stage 1 — Ingest.

Pulls labeled samples and materializes a YOLO-format dataset on local disk.

Sources (in priority order):
  1. storage `staging/` prefix in the datasets bucket  -> images/ + labels/
     (seeded for the demo; in Phase 3 the feedback loop writes approved labels here)
  2. [production seam] the `violations` table joined to approved feedback labels,
     using crop_s3_key to fetch the image. Left as a documented TODO so the demo
     stays self-contained but the production path is obvious.

Output: a directory  <out>/images/{train,val}  +  <out>/labels/{train,val}
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from common.config import get_settings
from common.logging import get_logger
from common.storage import Storage

log = get_logger("training.ingest")


def _split_for(name: str, val_ratio: float) -> str:
    """Deterministic train/val split by filename hash (stable across runs -> no leakage)."""
    h = int(hashlib.sha256(name.encode()).hexdigest(), 16) % 1000
    return "val" if h < val_ratio * 1000 else "train"


def ingest(out_dir: str | Path, staging_prefix: str = "staging") -> dict:
    s = get_settings()
    storage = Storage()
    out = Path(out_dir)

    image_keys = [
        k
        for k in storage.list(s.s3_bucket_datasets, f"{staging_prefix}/images")
        if k.endswith((".jpg", ".jpeg", ".png"))
    ]
    if not image_keys:
        raise RuntimeError(
            f"No staged images under {staging_prefix}/images. Run scripts/seed_demo_data.py first, "
            "or wire the violations-table source (see ingest.py production seam)."
        )

    counts = {"train": 0, "val": 0, "missing_labels": 0}
    for img_key in sorted(image_keys):
        stem = Path(img_key).stem
        label_key = f"{staging_prefix}/labels/{stem}.txt"
        if not storage.exists(s.s3_bucket_datasets, label_key):
            counts["missing_labels"] += 1
            continue
        split = _split_for(stem, s.train_val_split)
        ext = Path(img_key).suffix
        storage.get_file(s.s3_bucket_datasets, img_key, out / "images" / split / f"{stem}{ext}")
        storage.get_file(s.s3_bucket_datasets, label_key, out / "labels" / split / f"{stem}.txt")
        counts[split] += 1

    log.info(
        "ingest_complete",
        n_train=counts["train"],
        n_val=counts["val"],
        missing_labels=counts["missing_labels"],
        out_dir=str(out),
    )
    return counts


if __name__ == "__main__":
    import sys

    ingest(sys.argv[1] if len(sys.argv) > 1 else "./_run/dataset")
