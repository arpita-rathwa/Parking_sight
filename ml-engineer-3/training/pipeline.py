"""Weekly retraining pipeline orchestrator.

    ingest -> validate -> version -> train -> evaluate -> promote(gate)

Every run is recorded in retraining_runs for observability. The pipeline is
idempotent at the dataset level (identical data -> same version hash) and fails
closed (a validation error or a failed gate never touches the champion).

CLI:
    python -m training.pipeline --trigger manual
    python -m training.pipeline --trigger schedule --run-dir ./_run
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path

from common.db import init_db, session_scope
from common.logging import get_logger
from common.models import RetrainingRun
from training import evaluate as eval_stage
from training import ingest as ingest_stage
from training import promote as promote_stage
from training import train as train_stage
from training import validate as validate_stage
from training import versioning as version_stage

log = get_logger("training.pipeline")


def run(trigger: str = "manual", run_dir: str = "./_run", skip_train: bool = False) -> dict:
    init_db()
    rd = Path(run_dir)
    if rd.exists():
        shutil.rmtree(rd)
    dataset_dir = rd / "dataset"

    with session_scope() as db:
        run_row = RetrainingRun(trigger=trigger, status="running")
        db.add(run_row)
        db.flush()
        run_id = run_row.id
    log.info("pipeline_start", run_id=run_id, trigger=trigger)

    try:
        # 1. ingest
        ingest_stage.ingest(dataset_dir)

        # 2. validate (fail closed)
        report = validate_stage.validate(dataset_dir)
        if not report.ok:
            raise RuntimeError(f"dataset validation failed: {report.errors[:5]}")

        # 3. version
        ds_version = version_stage.version_dataset(dataset_dir, report.class_counts)

        # write data.yaml even if we skip training (eval needs it)
        train_stage.write_data_yaml(dataset_dir)

        if skip_train:
            log.info("train_skipped_dry_run", run_id=run_id, dataset_version=ds_version)
            _finish(run_id, "success_dry_run", ds_version, None, False, "validation+versioning only")
            return {"run_id": run_id, "dataset_version": ds_version, "promoted": False}

        # 4. train
        weights = train_stage.train(dataset_dir, rd)
        model_version = f"yolov8_{dt.datetime.now(dt.timezone.utc):%Y%m%d_%H%M%S}"

        # 5. register candidate FIRST so the model_evaluations FK is satisfied
        #    on Postgres (SQLite doesn't enforce FKs, which hid this ordering).
        from training.registry import register_candidate, set_model_metrics

        register_candidate(model_version, weights, ds_version)

        # 6. evaluate (inserts model_evaluations -> FK to model_registry now valid)
        metrics = eval_stage.evaluate(weights, model_version, dataset_dir)
        set_model_metrics(model_version, metrics)

        # 7. promotion gate
        gate = promote_stage.promote_if_better(model_version, metrics)

        _finish(run_id, "success", ds_version, model_version, gate.promote, "; ".join(gate.reasons))
        return {
            "run_id": run_id,
            "dataset_version": ds_version,
            "model_version": model_version,
            "metrics": metrics,
            "promoted": gate.promote,
            "reasons": gate.reasons,
        }

    except Exception as e:  # noqa: BLE001
        log.error("pipeline_failed", run_id=run_id, error=str(e))
        _finish(run_id, "failed", None, None, False, str(e))
        raise


def _finish(run_id: str, status: str, ds_version, model_version, promoted: bool, notes: str) -> None:
    with session_scope() as db:
        row = db.query(RetrainingRun).filter_by(id=run_id).one()
        row.status = status
        row.dataset_version = ds_version
        row.model_version = model_version
        row.promoted = promoted
        row.notes = notes[:2000] if notes else None
        row.finished_at = dt.datetime.now(dt.timezone.utc)
    log.info("pipeline_finish", run_id=run_id, status=status, promoted=promoted)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", default="manual", choices=["manual", "schedule", "feedback_threshold"])
    ap.add_argument("--run-dir", default="./_run")
    ap.add_argument(
        "--skip-train",
        action="store_true",
        help="ingest+validate+version only (no torch needed) — great for CI / quick demo",
    )
    args = ap.parse_args()
    out = run(trigger=args.trigger, run_dir=args.run_dir, skip_train=args.skip_train)
    print(out)
