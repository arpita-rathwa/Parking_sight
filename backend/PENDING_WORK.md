# Pending Work — ML Engineer 1 (Detection) + Backend Dev

## Detection-Service (ML Eng 1)

| # | Task | Why |
|---|------|-----|
| 1 | **Async `POST /detect`** — Move `model.predict_single()` to thread pool | Blocks FastAPI event loop |
| 2 | **Kafka circuit breaker** — Graceful fallback when Kafka is down | `_publish_detection` crashes endpoint if Kafka unreachable |
| 3 | **DB connection resilience** — Buffer to local queue or return 503 | Postgres down → 500 error |
| 4 | **Stream frame cache limit** — Max-age on `_latest_frame` | Frames accumulate indefinitely per camera |
| 5 | **Model hot-reload** — Watch model file, reload without restart | Model updates without service restart |
| 6 | **Prometheus metrics** — detection latency, throughput, model health | Ops observability |
| 7 | **ROI polygon filtering** — `CameraConfig.roi_polygon` exists but unused | Ignore detections outside region of interest |
| 8 | **Thread-safety for model** — Lock around `model.predict()` | YOLO/torch may not be thread-safe under concurrent calls |

## Backend Dev (Shared Infrastructure)

| # | Task | Why |
|---|------|-----|
| 9 | **Mount auth routes** — `shared/auth/routes.py` exists but no service mounts it | Login/register endpoints are orphaned |
| 10 | **Scoring worker** — Missing Kafka consumer: `violations.raw` → `congestion_scores` → `zones.scored` | Critical gap — no scoring pipeline exists |
| 11 | **Per-service Dockerfiles** — Only detection-service has one; others use bloated `Dockerfile.shared` | Bloated images, slow builds |
| 12 | **Per-service requirements** — Shared `requirements.txt` pulls ultralytics/opencv into every service | Unnecessary deps in lightweight services |
| 13 | **Redis-based rate limiter** — Currently in-memory dict | Breaks under multiple replicas |
| 14 | **Dead letter queue** — `violations.dlq` topic defined, nothing produces/consumes it | Failed messages silently dropped |
| 15 | **Kafka consumer in notification-service** — Uses fragile `threading.Thread` + `new_event_loop()` | Race conditions likely |
| 16 | **CI build stage** — Fails from missing AWS secrets | Need conditional step or mock |

## Defects / Code Quality

| # | Issue |
|---|-------|
| 17 | `conftest.py` uses `sys.path.insert` instead of proper packaging |
| 18 | Module-level `producer = ParkSightProducer()` in `shared/kafka/producer.py` — crashes on import if Kafka unreachable |
| 19 | `CameraStream.stop()` 5s join timeout doesn't force-kill stalled threads |
| 20 | All services share one DB connection pool (`pool_size=20`) — should be per-service |
