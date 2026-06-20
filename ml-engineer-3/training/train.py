"""Stage 4 — Train.

Wraps Ultralytics YOLOv8. Writes the data.yaml YOLO expects, runs training, and
returns the path to best.pt. Ultralytics is imported lazily so the rest of the
pipeline (validate/version/promote logic + tests) runs without torch installed.

Hackathon note: defaults to yolov8n + few epochs for a fast demo on g4dn or CPU.
Scale epochs/model via env (TRAIN_EPOCHS, BASE_MODEL) for production.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from common.config import get_settings
from common.logging import get_logger

log = get_logger("training.train")


def write_data_yaml(dataset_dir: str | Path) -> Path:
    s = get_settings()
    root = Path(dataset_dir).resolve()
    cfg = {
        "path": str(root),
        "train": "images/train",
        "val": "images/val",
        "names": {i: c for i, c in enumerate(s.classes)},
    }
    out = root / "data.yaml"
    out.write_text(yaml.safe_dump(cfg, sort_keys=False))
    return out


def train(dataset_dir: str | Path, run_dir: str | Path) -> Path:
    s = get_settings()
    from ultralytics import YOLO  # lazy

    data_yaml = write_data_yaml(dataset_dir)
    log.info(
        "training_start", base_model=s.base_model, epochs=s.train_epochs, img=s.img_size, device=s.device
    )

    model = YOLO(s.base_model)
    model.train(
        data=str(data_yaml),
        epochs=s.train_epochs,
        imgsz=s.img_size,
        batch=s.batch,
        device=s.device,
        project=str(run_dir),
        name="train",
        exist_ok=True,
        verbose=False,
    )
    best = Path(run_dir) / "train" / "weights" / "best.pt"
    log.info("training_done", weights=str(best))
    return best
