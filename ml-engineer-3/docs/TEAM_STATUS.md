# ParkSight — Team Status

Honest cross-team status as of submission prep. Only **ML Engineer 3** is represented by
actual code in this repository; the others are inferred from the work-distribution docs
and the integration contracts ML Eng 3 depends on. Confirm their real status with them.

## ML Engineer 3 (this repo) — Model Training, Evaluation, Feedback, Forecasting
**Completed:**
- Retraining pipeline (ingest→validate→version→train→evaluate→promote), fail-closed, executed once with real YOLOv8.
- Dataset versioning (content-hash + manifest) and model registry (champion/challenger + rollback).
- Promotion gate (floor + margin + per-class regression guard) — unit-tested.
- Officer feedback loop: API + service + review console + threshold trigger — 6 tests, runs end-to-end.
- HMM pre-staging: 4-regime forecaster + explanations + 3 figures + API — 5 tests.
- 22 tests passing, lint green, CI workflows, docs.

**Pending:**
- Verify S3/Postgres/MSK code paths (never executed).
- Exercise rollback end-to-end; add JSON schemas for `model.promoted` / `hotspot.predictions`.
- CV evaluation framework (Phase 4) + drift monitoring (Phase 5) — designed, not built.

**Integration needed (from others):**
- ML Eng 1 to **consume `model.promoted`** and hot-reload; provide `crop_s3_key` data.
- ML Eng 2 to populate the real `congestion_scores` the HMM reads.
- Backend to emit `officer.feedback` from officer-app-api and provision Kafka/S3/Postgres + the table migrations.

## ML Engineer 1 — YOLOv8 Detection Pipeline
**Completed (assumed):** detection-service, RTSP integration, `violations.raw` producer.
**Pending / unverified here:** writing `crop_s3_key` into `violations`; **consuming `model.promoted`** to hot-reload the champion; confirming the shared class taxonomy + artifact format.
**Integration needed:** the model-reload contract with ML Eng 3 (this is the loop's last hop, currently unbuilt).

## ML Engineer 2 — Congestion Scoring & Priority Queue
**Completed (assumed):** scoring-service (`zones.scored`), priority queue, `congestion_scores` writer.
**Pending / unverified here:** confirming `congestion_scores` cadence + field semantics the HMM relies on.
**Integration needed:** ML Eng 3's HMM consumes `congestion_scores`; agree on the write interval.

## Backend — APIs, Database, Infrastructure
**Completed (assumed):** core FastAPI endpoints, Postgres+PostGIS+TimescaleDB schema, OAuth2/JWT, Kafka wiring.
**Pending / unverified here:** Alembic migrations for the 4 new ML tables; **`officer.feedback` producer** on `/officer/status=unresolvable`; new Kafka topics; S3 buckets; the `violations.crop_s3_key` column.
**Integration needed:** provision MSK/S3/RDS; emit `officer.feedback`; apply migrations; wire JWT into the ML API (replacing the `X-Role` stand-in).

## Frontend — Web Dashboard + Officer App
**Completed (assumed):** control-room dashboard shell, officer app.
**Pending / unverified here:** the **predictive heatmap overlay** (HMM risk), the **review console** (approve/reject), the **retraining status badge**.
**Integration needed:** consume the endpoints in `docs/FRONTEND_HANDOFF.md`; subscribe to `hotspot.predictions` for realtime overlay.

---

### The single most important integration gap
**`model.promoted` → detection-service hot-reload (ML Eng 1).** Without it, the retraining
loop produces a better model that never reaches production. It's a defined contract; it is
not yet wired. Everything else is provisioning or frontend consumption.
