# ParkSight — Final Deliverables (ML Engineer 3)

## Project Overview
ParkSight is an AI-powered parking-intelligence and enforcement platform that detects
illegal parking from CCTV feeds, quantifies each zone's impact on traffic congestion,
ranks zones for enforcement, dispatches officers, and **learns continuously** from their
feedback. This repository is the **ML platform (ML Engineer 3)** — the learning and
forecasting brain of the system: the retraining pipeline, the officer feedback loop, and
the HMM predictive pre-staging engine.

## Problem Statement
Cities have poor visibility into **parking-induced congestion**. Enforcement is reactive
and untargeted: officers are dispatched after jams form, with no data on which zones
matter most or which are about to spike. ParkSight turns CCTV into a ranked, predictive
enforcement signal — and crucially, gets smarter every week instead of degrading.

## Solution Architecture
Event-driven microservices on a Kafka backbone. Six live-path services (detection,
scoring, queue, notification, dashboard-api, officer-app-api) run in real time; the
**ML platform plane (this repo)** runs on batch + event + scheduled cadences beside them
and closes two loops back into the live path: a **better detection model** and **hotspot
forecasts**.

```
CCTV → detection (YOLOv8) → violations.raw → scoring → zones.scored → queue → dashboard → officer
                                                                                     │
        ┌────────────────────── ML PLATFORM (this repo) ─────────────────────┐      │
        │ feedback loop ← officer.feedback ───────────────────────────────────┼──────┘
        │   approved labels → datasets/staging → retraining → model registry  │
        │   → model.promoted → detection hot-reload                           │
        │ HMM ← congestion_scores → hotspot.predictions → dashboard overlay   │
        └─────────────────────────────────────────────────────────────────────┘
```

## Feature List (this repo)
- **Weekly retraining pipeline** — ingest → validate → version → train → evaluate → promote, fail-closed.
- **Dataset versioning** — immutable, content-hashed dataset snapshots with full lineage.
- **Model registry** — S3 + DB, single champion, promote/rollback.
- **Promotion gate** — champion/challenger: absolute floor + improvement margin + no per-class regression.
- **Officer feedback loop** — unresolvable + photo → review queue → reviewer correction → training data → retrain trigger.
- **HMM predictive pre-staging** — 4-regime forecast of next-30-min hotspot risk per zone, with explanations.
- **FastAPI surface** — feedback, review console, retraining status/trigger, forecast endpoints.

## Tech Stack
- **CV / ML:** YOLOv8 (Ultralytics 8.3.0), hmmlearn, scikit-learn, NumPy, Pandas-style processing.
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2.
- **Data:** PostgreSQL + PostGIS + TimescaleDB (prod) / SQLite (demo); S3 (prod) / local FS (demo).
- **Streaming:** Kafka / AWS MSK (prod) — no-op in demo.
- **Infra:** Docker, GitHub Actions (CI + weekly retrain), AWS EC2 g4dn.xlarge for training.
- **Viz:** Matplotlib (regime/transition/risk figures).

## ML Workflow
1. Officers flag misdetections (unresolvable + photo).
2. Reviewer (ML Eng 1) corrects labels in a review queue.
3. Approved labels land in `datasets/staging/`.
4. At 50 approved labels (or manual), the pipeline runs: validate → version → train YOLOv8 → evaluate.
5. The promotion gate ships the model only if it beats the champion and regresses no class.
6. `model.promoted` tells detection-service to hot-reload — the loop is closed.
7. In parallel, the HMM trains on `congestion_scores` and forecasts hotspot risk per zone.

## Data Flow
`congestion_scores` (ML Eng 2) → HMM features → forecast → `hmm_predictions` + `hotspot.predictions`.
`officer.feedback` (Backend) → `feedback_submissions` → `label_review_queue` → approved →
`datasets/staging/` → `dataset_versions` → `model_registry` → `model.promoted`.

## API Overview (`/api/v1`, `X-Role` auth in demo)
- `POST /officer/feedback`, `POST /officer/feedback/{id}/evidence`
- `GET /review/queue`, `GET/POST /review/queue/{id}[/approve|/reject]`
- `GET /ml/retraining/status`, `POST /ml/retraining/trigger`
- `POST /forecast/hotspots`, `GET /forecast/heatmap`, `GET /forecast/zones/{id}`
Full contracts in `docs/FRONTEND_HANDOFF.md`; OpenAPI at `/docs`.

## Future Scope
- CV evaluation framework (Phase 4) + drift monitoring (Phase 5) — designed, not built.
- Event-aware HMM (match-day/holiday feed); multi-step forecasting.
- CVAT-based bounding-box relabeling (currently a default box).
- Multi-city scoping, SLA reporting, public congestion API for navigation apps.
- DVC dataset versioning; SageMaker training option.

## Known Limitations (honest)
- **Only ML Eng 3's slice is built here.** Detection, scoring, priority queue, officer
  assignment, and the dashboard are teammates' services and are **not** in this repo.
- **Demo runs on local FS + SQLite + no-op Kafka.** The S3/Postgres/MSK code paths exist
  but were **never executed**.
- **`model.promoted` has no consumer yet** — detection-service (ML Eng 1) must add it.
- **Feedback/HMM data is synthetic** in the demo; reads the real tables in production.
- **Auth is an `X-Role` header**, a stand-in for Backend's JWT.
- **Retraining's production data source** (`violations.crop_s3_key`) is a stub pending ME1 + Backend.
- **Rollback and the real-broker/S3 paths** are implemented but not yet exercised end-to-end.
