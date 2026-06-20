# Training Pipeline

The weekly YOLOv8 retraining pipeline. One command (`python -m training.pipeline`),
six idempotent stages, fail-closed semantics, full audit trail.

## Stages

| # | Stage | Module | Output | Fails closed? |
|---|---|---|---|---|
| 1 | Ingest | `training/ingest.py` | YOLO dataset dir (`images/{train,val}`, `labels/{train,val}`) | n/a |
| 2 | Validate | `training/validate.py` | `ValidationReport` | **yes** — abort on any error |
| 3 | Version | `training/versioning.py` | immutable `dataset_versions` row + manifest in S3 | n/a |
| 4 | Train | `training/train.py` | `best.pt` | training error aborts |
| 5 | Evaluate | `training/evaluate.py` | metrics + `report.html` + `model_evaluations` row | n/a |
| 6 | Promote | `training/promote.py` | champion change + `model.promoted` event | **yes** — failed gate keeps old champion |

## Triggers

- **Schedule:** GitHub Actions cron, Sundays 02:00 UTC (`.github/workflows/weekly-retrain.yml`) — low-traffic window.
- **Feedback threshold:** when the officer feedback loop (Phase 3) accumulates N approved relabels, it calls `--trigger feedback_threshold`.
- **Manual:** `workflow_dispatch` / `make retrain` for the demo.

## Dataset versioning

`version_dataset()` computes a SHA-256 over the sorted `(relpath, file-hash)` manifest.
Identical data → identical hash → no duplicate version. Every model row stores its
`dataset_version`, so any production model is traceable to the exact bytes it trained on.

Version id format: `ds_<UTC-timestamp>_<hash[:8]>`.

## Model registry

S3 artifacts (`<version>/best.pt`, `metrics.json`, `report.html`) + a `model_registry`
row whose `status` ∈ `{candidate, champion, archived, rolled_back}`. Exactly one champion.
A flat `champion.json` pointer mirrors the DB for services that prefer not to query Postgres.

## Compatibility contract with detection-service (ML Eng 1)

On promotion, `model.promoted` carries `{model_version, weights_uri, metrics}`.
detection-service consumes it, downloads the champion weights, and hot-reloads —
no redeploy. Class index order is fixed by `common/config.py` and must match the
detection-service decode side.

## Demo vs production knobs

| Setting | demo | production |
|---|---|---|
| `BASE_MODEL` | `yolov8n.pt` | `yolov8s/m.pt` |
| `TRAIN_EPOCHS` | 30 | 100+ |
| `DEVICE` | `cpu` | `0` (g4dn GPU) |
| storage | local FS | S3 |
| db | SQLite | Postgres |
| Kafka | no-op | MSK |
