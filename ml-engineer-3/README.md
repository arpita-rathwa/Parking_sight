# ParkSight — ML Platform (ML Engineer 3)

Retraining, model registry, dataset versioning, evaluation, drift, and HMM pre-staging
for the ParkSight parking-intelligence platform. **Phase 2 (this drop): the weekly
YOLOv8 retraining pipeline + dataset versioning + model registry + evaluation hook + CI/CD.**

Built to run two ways from the same code:
- **demo** — local filesystem + SQLite + no Kafka. Runs on a laptop, no AWS, no GPU needed for the spine.
- **prod** — MinIO/S3 + Postgres + MSK Kafka + g4dn.xlarge GPU. Flip with env vars only.

---

## 60-second demo (no GPU)

```bash
pip install -e ".[dev]"          # core deps, no torch
make demo                        # = init db -> seed synthetic data -> run pipeline spine
```

`make demo` runs **ingest → validate → version** end-to-end and prints structured JSON
logs the whole way. It proves the pipeline, registry tables, dataset versioning, and
validation gate without needing a GPU.

To run the **full** pipeline (real YOLOv8 training → eval → promotion gate):

```bash
make install-train               # adds ultralytics + torch
make seed
make retrain                     # ingest -> validate -> version -> TRAIN -> eval -> promote
```

On the `g4dn.xlarge` set `DEVICE=0`, `TRAIN_EPOCHS=100` in `.env`.

---

## Pipeline

```mermaid
flowchart LR
    A[Ingest\nlabeled violations + crops] --> B[Validate\nclass range, bbox, splits]
    B -->|fail closed| X[(abort, champion untouched)]
    B --> C[Version\ncontent-hash + manifest -> S3]
    C --> D[Train\nYOLOv8 on g4dn]
    D --> E[Evaluate\nmAP@0.5, mAP@0.5:0.95, per-class]
    E --> F{Promotion gate}
    F -->|better + no regression| G[Set champion\nmodel.promoted event]
    F -->|worse| H[(stay candidate)]
    G -.hot reload.-> DET[detection-service / ML Eng 1]
```

Every run is logged to `retraining_runs`. The pipeline **fails closed**: a validation
error or a failed gate never overwrites the production champion.

## Promotion gate

A candidate replaces the champion only if **all** hold (`training/configs/promotion.yaml`):
1. `mAP@0.5 ≥ 0.50` — absolute floor
2. `mAP@0.5 ≥ champion + 0.005` — actually better
3. no per-class `mAP@0.5` regression beyond `0.10` — don't trade a class away

First-ever model only needs the floor. **Rollback:** `make rollback V=<model_version>`.

## What this hands to the rest of the team

| Output | Consumer |
|---|---|
| `model.promoted` Kafka event + `champion.json` | detection-service (ML Eng 1) hot-reloads |
| `dataset_versions` / `model_registry` / `model_evaluations` rows | dashboards, SLA reporting |
| `report.html` per model in the models bucket | eval framework (Phase 4) + presentation |

## Layout

```
common/      config, storage (local|s3), db, models, logging, kafka producer
training/    ingest -> validate -> version -> train -> evaluate -> registry -> promote -> pipeline
scripts/     seed_demo_data.py (synthetic), init_db.py
tests/       torch-free logic tests (validation, versioning hash, promotion gate)
docker/      Dockerfile.training (g4dn / SageMaker)
.github/     ci.yml (lint+test+spine smoke), weekly-retrain.yml (Sun 02:00 cron)
```

## Production seams kept intact (from Phase 1)

- **GDPR (Conflict C1):** ingest expects blurred vehicle crops via `crop_s3_key`; raw frames stay purged.
- **Frame contract (R2):** ingest's production source is `violations.crop_s3_key` (documented TODO in `ingest.py`).
- **Model-load contract (R5):** promotion emits `model.promoted`; detection-service reloads the champion.
- **Class taxonomy (R3):** frozen in `common/config.py` — `car, motorcycle, auto_rickshaw, bus, truck, van, other`.

Phases 3–7 (feedback loop, full eval framework, drift, HMM, testing/deploy/docs) build on these tables and events.

---

## Phase 3: Officer Feedback Loop

Turns officer field actions into approved training labels that feed Phase 2 — the
continuous-learning mechanism. Full design in `docs/feedback_loop.md`.

```bash
make serve            # feedback-loop API at http://localhost:8001/docs
make demo-feedback    # end-to-end: submit -> review -> approve -> trigger retrain
```

**The loop:** officer marks a violation `unresolvable` + uploads a photo → `officer.feedback`
event → pending `label_review_queue` item → reviewer (ML Eng 1) approves with a corrected
label → the sample is written into `datasets/staging/` → at `FEEDBACK_RETRAIN_THRESHOLD`
approved labels (default 50) the Phase-2 pipeline retrains on the augmented dataset.

`make demo-feedback` proves it: 25 submissions → 20 approved → threshold hit → a new
content-hashed dataset version built **from the approved feedback samples**. New tables
(`feedback_submissions`, `label_review_queue`) are additive; auth is an `X-Role` stand-in
for Backend's JWT.

---

## Phase 6: HMM Predictive Pre-Staging (v2.0)

Forecasts each zone's **hotspot risk for the next 30 min** so officers are pre-staged
before congestion peaks. A 4-state Hidden Markov Model (calm -> building -> congested ->
critical) learns traffic regimes from congestion history. Full math in `docs/hmm_prediction.md`.

```bash
pip install -e ".[dev]"     # now includes hmmlearn + sklearn + matplotlib
make demo-hmm               # seed -> train -> rank hotspots -> write figures
make serve                  # forecast endpoints at /api/v1/forecast/*
```

`make demo-hmm` trains on synthetic congestion history and prints a risk-ranked hotspot
table + a plain-language explanation, and writes three figures to `hmm_reports/`:
regimes-over-time, the learned transition matrix, and the per-zone risk ranking. Reads
the existing `congestion_scores` table (ML Eng 2); outputs land in `hmm_predictions` and
the `hotspot.predictions` event for the dashboard overlay.
