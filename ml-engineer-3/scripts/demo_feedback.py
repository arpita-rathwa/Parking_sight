"""End-to-end feedback-loop demo — the 'continuous learning' showpiece.

Runs the whole loop via the service layer (no server needed):
  submit unresolvable feedback (+ synthetic evidence photo)
    -> officer.feedback event -> review item
    -> reviewer approves (writes labeled sample into training staging)
    -> retraining trigger fires at threshold -> dataset version bumps

    python scripts/demo_feedback.py --n 25 --threshold 20

Use a small --threshold so the trigger fires quickly on stage. By default the
triggered retrain is GPU-safe (skip-train) and just proves the dataset grew +
versioned; pass --full to run real YOLOv8 training.
"""

from __future__ import annotations

import argparse
import io
import random

from PIL import Image, ImageDraw

from common.config import get_settings
from common.db import init_db
from feedback_loop import review, service, trigger

CLASS_COLORS = [
    (220, 60, 60),
    (60, 200, 90),
    (240, 200, 40),
    (70, 120, 240),
    (170, 90, 220),
    (240, 140, 40),
    (160, 160, 160),
]
W = H = 416


def _evidence_photo(seed: int) -> tuple[bytes, int, dict]:
    rng = random.Random(seed)
    cls = rng.randint(0, len(CLASS_COLORS) - 1)
    img = Image.new("RGB", (W, H), (48, 50, 54))
    d = ImageDraw.Draw(img)
    bw, bh = rng.randint(70, 140), rng.randint(50, 100)
    cx, cy = rng.randint(bw, W - bw), rng.randint(bh, H - bh)
    d.rectangle(
        [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2],
        fill=CLASS_COLORS[cls],
        outline=(20, 20, 20),
        width=2,
    )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    bbox = {"cx": cx / W, "cy": cy / H, "w": bw / W, "h": bh / H}
    return buf.getvalue(), cls, bbox


def run(n: int, threshold: int, approve_ratio: float, full: bool) -> None:
    s = get_settings()
    object.__setattr__(s, "feedback_retrain_threshold", threshold)
    init_db()
    classes = s.classes

    print(f"\n=== Officer Feedback Loop demo: {n} submissions, threshold={threshold} ===\n")
    approved = rejected = 0
    for i in range(n):
        photo, cls, bbox = _evidence_photo(i)
        # 1. officer submits unresolvable
        fb = service.submit_feedback(
            violation_id=f"v_demo_{i:04d}",
            officer_id="off_009",
            status="unresolvable",
            camera_id="cam_042",
            zone_id="zone_17",
            reason="vehicle departed before arrival",
            proposed_class=classes[cls],
        )
        # 2. officer uploads evidence -> event -> review item
        service.attach_evidence(fb["feedback_id"], photo)

    # 3. reviewer (ML Eng 1) works the queue
    queue = review.list_queue(status="pending", limit=n + 5)
    for idx, item in enumerate(queue):
        if random.Random(idx).random() < approve_ratio:
            review.approve(item["id"], reviewer_id="ml_eng_1", class_id=item["proposed_class_id"])
            approved += 1
        else:
            review.reject(item["id"], reviewer_id="ml_eng_1", notes="blurry / not a vehicle")
            rejected += 1

    st = trigger.status()
    print(f"approved={approved}  rejected={rejected}")
    print(
        f"approved_since_last_retrain={st['approved_since_last_retrain']}  "
        f"threshold={st['threshold']}  due={st['due']}\n"
    )

    # 4. trigger retrain if due
    result = trigger.maybe_trigger(reason="feedback_threshold", skip_train=not full)
    if result["triggered"]:
        run_info = result["run"]
        print(
            "RETRAIN TRIGGERED ->",
            {k: run_info.get(k) for k in ("dataset_version", "model_version", "promoted")},
        )
    else:
        print("retrain not due yet")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--threshold", type=int, default=20)
    ap.add_argument("--approve-ratio", type=float, default=0.9)
    ap.add_argument("--full", action="store_true", help="run real YOLOv8 training on trigger")
    a = ap.parse_args()
    run(a.n, a.threshold, a.approve_ratio, a.full)
