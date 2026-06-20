"""Seed a tiny synthetic YOLO dataset into storage `staging/` so the whole
pipeline runs end-to-end on a laptop with no cameras and no AWS.

Each image is a road-grey canvas with a few colored rectangles standing in for
vehicles; the matching YOLO label has the correct class + normalized bbox. The
model genuinely learns to separate the classes, so the demo shows real metrics.

    python scripts/seed_demo_data.py --n 120
"""

from __future__ import annotations

import argparse
import io
import random

from PIL import Image, ImageDraw

from common.config import get_settings
from common.logging import get_logger
from common.storage import Storage

log = get_logger("scripts.seed")

# distinct colour per class id -> learnable signal
CLASS_COLORS = [
    (220, 60, 60),  # car
    (60, 200, 90),  # motorcycle
    (240, 200, 40),  # auto_rickshaw
    (70, 120, 240),  # bus
    (170, 90, 220),  # truck
    (240, 140, 40),  # van
    (160, 160, 160),  # other
]
W = H = 416


def _make_sample(seed: int):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), (48, 50, 54))
    draw = ImageDraw.Draw(img)
    lines = []
    n_obj = rng.randint(1, 3)
    n_classes = len(CLASS_COLORS)
    for _ in range(n_obj):
        cls = rng.randint(0, n_classes - 1)
        bw, bh = rng.randint(60, 130), rng.randint(40, 90)
        cx, cy = rng.randint(bw, W - bw), rng.randint(bh, H - bh)
        x0, y0, x1, y1 = cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2
        draw.rectangle([x0, y0, x1, y1], fill=CLASS_COLORS[cls], outline=(20, 20, 20), width=2)
        lines.append(f"{cls} {cx / W:.6f} {cy / H:.6f} {bw / W:.6f} {bh / H:.6f}")
    return img, "\n".join(lines)


def seed(n: int = 120) -> None:
    s = get_settings()
    storage = Storage()
    for i in range(n):
        img, label = _make_sample(i)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        stem = f"demo_{i:04d}"
        storage.put_bytes(s.s3_bucket_datasets, f"staging/images/{stem}.jpg", buf.getvalue())
        storage.put_bytes(s.s3_bucket_datasets, f"staging/labels/{stem}.txt", label.encode())
    log.info("seed_complete", n=n, bucket=s.s3_bucket_datasets, prefix="staging/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120)
    seed(ap.parse_args().n)
