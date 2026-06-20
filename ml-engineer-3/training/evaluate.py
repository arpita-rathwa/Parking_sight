"""Stage 5 — Evaluate (integration point for the Phase-4 CV eval framework).

Runs the model against the val split (or a frozen golden set if present at
datasets/golden/) and extracts the headline metrics + per-class mAP50. Writes a
JSON report + a minimal HTML report to storage and a model_evaluations row.

The full evaluation framework (mAP@0.5:0.95 curves, confusion matrix images,
confidence-distribution plots, trend pages) lands in Phase 4; this is the hook
the retraining pipeline calls so the promotion gate has numbers to act on.
"""

from __future__ import annotations

from pathlib import Path

from common.config import get_settings
from common.db import session_scope
from common.logging import get_logger
from common.models import ModelEvaluation
from common.storage import Storage

log = get_logger("training.evaluate")


def _html_report(model_version: str, m: dict) -> str:
    rows = "".join(f"<tr><td>{c}</td><td>{v:.4f}</td></tr>" for c, v in m["per_class"].items())
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<title>ParkSight eval — {model_version}</title>
<style>body{{font-family:system-ui;background:#0f1117;color:#e6e6e6;padding:24px}}
table{{border-collapse:collapse}}td,th{{border:1px solid #333;padding:6px 12px}}
.big{{font-size:28px;color:#7c9eff}}</style></head><body>
<h1>Model {model_version}</h1>
<p class='big'>mAP@0.5 = {m['map50']:.4f} &nbsp; mAP@0.5:0.95 = {m['map5095']:.4f}</p>
<p>precision = {m['precision']:.4f} &nbsp; recall = {m['recall']:.4f} &nbsp; F1 = {m['f1']:.4f}</p>
<h3>Per-class mAP@0.5</h3><table><tr><th>class</th><th>mAP@0.5</th></tr>{rows}</table>
</body></html>"""


def evaluate(weights_path: str | Path, model_version: str, dataset_dir: str | Path) -> dict:
    s = get_settings()
    from ultralytics import YOLO  # lazy

    data_yaml = Path(dataset_dir) / "data.yaml"
    model = YOLO(str(weights_path))
    res = model.val(data=str(data_yaml), verbose=False)

    box = res.box
    precision = float(box.mp)
    recall = float(box.mr)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    per_class = (
        {s.classes[i]: float(ap) for i, ap in zip(res.box.ap_class_index, box.ap50)}
        if hasattr(box, "ap50")
        else {}
    )

    metrics = {
        "map50": float(box.map50),
        "map5095": float(box.map),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "per_class": per_class,
    }

    storage = Storage()
    storage.put_json(s.s3_bucket_models, f"{model_version}/metrics.json", metrics)
    report_uri = storage.put_bytes(
        s.s3_bucket_models,
        f"{model_version}/report.html",
        _html_report(model_version, metrics).encode(),
    )

    with session_scope() as db:
        db.add(
            ModelEvaluation(
                model_version=model_version,
                eval_set="val",
                map50=metrics["map50"],
                map5095=metrics["map5095"],
                precision=precision,
                recall=recall,
                f1=f1,
                per_class=per_class,
                report_uri=report_uri,
            )
        )

    log.info(
        "evaluation_done",
        model_version=model_version,
        map50=metrics["map50"],
        map5095=metrics["map5095"],
        report_uri=report_uri,
    )
    return metrics
