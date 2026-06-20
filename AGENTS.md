# ParkSight — AI Parking Enforcement SaaS

**Goal**: Build a fully-integrated, deployable AI SaaS for parking enforcement — CCTV → YOLOv8 detection → congestion scoring → officer dispatch → predictive analytics → self-improving retraining loop.

**Status**: ~60% complete. All core services built, wired, and deployable via Docker Compose + ECS. Remaining work is production hardening (Phase C), scale/observability (Phase D), and business features (Phase E).

---

## Full Conversation History

### Session 1 — Frontend Wiring (Phase A/B completion)

**What was done:**
- All 7 dashboard pages (Dashboard, Analytics, Dispatch, Cameras, Alerts, AIInsights, Login) wired to live API endpoints. Zero static mock data.
- 6 new React hooks: `useCongestionHeat`, `useViolationTypes`, `useRadarData`, `useFactorWeights`, `useAnalyticsInsights`, `usePredictedHotspots` — each backed by a dedicated backend endpoint.
- `Analytics.tsx` fully wired: congestion heat map, violation types pie+legend, AI insights card, predicted hotspots.
- `AIInsights.tsx` fully wired: radar chart with dynamic zone names/colors, factor analysis, insight text.

**Scoring worker built:**
- Kafka consumer → 60s buffer → LightGBM/heuristic scoring → `congestion_scores` persist → `zones.scored` Kafka produce.
- Camera→zone cache (5-min TTL) eliminates per-violation GIS queries.
- Batch GIS resolution for violations without camera→zone mapping.
- Consumer error recovery with proper close.

**Seed data (`scripts/seed.py`):**
- 14 zones, 8 users (4 officers), violations from CSV, 72h CongestionScore entries per zone, EnforcementLog entries.
- Destructive (`TRUNCATE ... CASCADE`) — fresh DB only.

**Detection Kafka event** now includes `zone_id` (resolved from camera DB lookup).

**JWT secret**: Default `""` with import-time `RuntimeError` + token generation command if unset.

**ROI polygon filtering**: `roi_polygon` column on Camera model, `point_in_polygon` + `filter_detections_by_roi` utilities, applied in `/detect` endpoint and pipeline callback.

### Session 2 — Deployment Infrastructure

**Per-service Dockerfiles:**
- `requirements.common.txt`, `requirements.detection.txt`, `requirements.scoring.txt`
- Detection + scoring have own Dockerfiles; other services share `Dockerfile.base`
- `docker-compose.yml` updated for all services

**Alembic migrations**: `shared/utils/migrations.py` → `run_migrations()` calls `alembic upgrade head` from `alembic.ini`. Runs in all 6 service startups (replaces `Base.metadata.create_all`).

**Sentry**: `shared/utils/sentry.py` → `init_sentry(service_name)` with FastAPI + SQLAlchemy integrations. Called in all 6 services.

**CORS**: `CORS_ORIGINS` env var (default `"*"`), parsed as comma-separated list in all 6 services.

**Traefik reverse proxy**: v3.1 with Let's Encrypt, path-based routing to all services, API dashboard, automatic TLS.

**Frontend Dockerfile**: Multi-stage build (Node → nginx), `nginx.conf` proxies `/api/` to Traefik.

**Production docker-compose**: `backend/docker-compose.prod.yml` — resource limits, CloudWatch logging driver, `restart: unless-stopped`.

**ECS Fargate**: `deploy/ecs/task-definition.json` — all 8 containers (traefik, frontend, 6 microservices).

**CI/CD**: `.github/workflows/ci.yml` — per-service Dockerfiles in build step, frontend build, path triggers for `frontend/**`, deploy script exports `DOMAIN` for Traefik routing.

**`.env.example`**: All 15 configurable vars with defaults and docs.

### Session 3 — Restructuring & Renaming

- `Dockerfile.shared` → `Dockerfile.base`
- `requirements.base.txt` → `requirements.common.txt`
- `scripts/seed_data.py` → `scripts/seed.py`
- `services/queue/` → `services/dispatch/`
- `services/dashboard/` → `services/analytics/`
- `services/officer-app/` → `services/officers/`
- `services/notification/` → `services/alerts/`
- `deploy/docker-compose.prod.yml` moved to `backend/docker-compose.prod.yml`
- Updated all 12 files referencing old names (docker-compose, CI, ECS, deploy docs, Dockerfiles, service main.py titles/health checks)
- Removed `ml_engineer_2/` from git tracking

### Session 4 — ML Engineer 2 Debugging

- **`scoring_service.py`**: Added CORS, fixed model path to `os.path.join(os.path.dirname(__file__), ...)`, added error handling
- **`queue-service.py`**: Moved `import pandas` to top level, added file-existence + Redis error handling, fixed model path
- **`kafka_service.py`**: **Critical fix** — Switched from `confluent_kafka` (not installed) to `kafka-python-ng` API (matches requirements.txt and notebook). Added model path fix, `finally` cleanup block, SIGTERM handler
- **`requirements.txt`**: Removed `annotated-doc==0.0.4` (nonexistent PyPI package)

### Session 5 — Integration Wiring (All 3 ML Engineers)

Wired all 8 documented-but-never-implemented integration contracts from `ml-engineer-3/docs/INTEGRATION_PACKAGE.md`:

**Kafka topics**: Added `officer.feedback`, `model.promoted`, `hotspot.predictions` to `shared/kafka/topics.py`

**Officer feedback → ML3**: Backend officers API now emits `officer.feedback` event (with full schema) on "unresolvable" status. ML3 FastAPI lifespan starts feedback consumer daemon thread.

**Model promoted → Scoring**: Scoring service starts consumer thread → calls `reload_scoring_engine()` on receipt (fresh `lgb.Booster` load).

**Hotspot predictions → Dashboard**: Analytics service starts consumer → stores latest HMM predictions in memory → serves via `/predicted-hotspots` with heuristic fallback.

**Shared database**: ML3 config now points to shared Postgres (`postgres:5432/parksight`). Added `psycopg2-binary` to ML3 deps.

**Docker Compose**: Added `ml-platform-api` service (ML3 API) with Traefik routing + resource limits.

**Scoring engine**: Added `reload_scoring_engine()` for hot-reload on `model.promoted` event.

### Session 6 — README

Comprehensive root `README.md` with problem statement, solution, architecture diagram, all 9 services, tech stack, quick start, ML pipeline breakdown, event integration map, repo structure.

### Commits Pushed to `origin/main`

| Commit | Message | Files | Delta |
|---|---|---|---|
| `084012d` | *(prior, before our session)* | — | — |
| `de193f4` | Restructure + wire all 3 ML engineers + debug fixes | 25 | +295 / -111 |
| `5d7fb8d` | Add root README with problem statement, solution, architecture, quick start | 1 | +172 |

**Total**: ~50 files changed, ~4,400 lines added, ~460 lines removed across entire conversation.

---

## Completed Items (from original PENDING_WORK.md)

| # | Task | Status |
|---|---|---|
| 7 | ROI polygon filtering (detection) | DONE |
| 9 | Mount auth routes in all services | DONE |
| 10 | Scoring worker (Kafka consumer → buffer → score → persist → produce) | DONE |
| 11 | Per-service Dockerfiles | DONE |
| 12 | Per-service requirements files | DONE |
| 21 | Scoring worker (duplicate of #10) | DONE |
| 23 | Deployment (CI, Docker, ECS, Traefik, HTTPS, Sentry, CORS, migrations, .env) | DONE |
| 24 | JWT secret — default `""` with clear error | DONE |
| 25 | CORS lockdown via `CORS_ORIGINS` env var | DONE |
| 29 | Health checks on all 8 services | DONE |
| 31 | Alembic migrations auto-run on startup | DONE |
| 32 | ECS Fargate task definition | DONE |
| 33 | CloudWatch log aggregation | DONE |
| 34 | Sentry in all 6 services | DONE |
| 35 | Frontend CI build | DONE |
| 39 | All 7 dashboard pages wired to live API | DONE |
| 42 | Seed data script (14 zones, 8 users, violations, 72h scores) | DONE |

---

## A — Completed Features (Phase A/B)

### Frontend (7 pages, live API)
- Dashboard, Analytics, Dispatch, Cameras, Alerts, AIInsights, Login
- 6 custom hooks for analytics data
- Real-time congestion heatmap, violation types, radar chart, factor weights
- AI insights card with zone explanations
- Predicted hotspots from HMM or historical fallback

### Backend (6 microservices)
- **Detection**: YOLOv8 RTSP pipeline, ROI filtering, Kafka event production
- **Scoring**: Kafka consumer → 60s buffer → LightGBM → persist → `zones.scored`
- **Dispatch**: Redis priority ZSET, officer assignment API
- **Analytics**: Heatmap, violation types, congestion trends, factor analysis, predicted hotspots
- **Officers**: Assignment API, status updates, `officer.feedback` event emission
- **Alerts**: WebSocket push for violations + zone scores

### Common Infrastructure
- JWT auth with role-based access (admin, operator, planner, officer, reviewer)
- Redis caching layer
- Rate limiting (currently in-memory)
- Structured logging middleware
- CORS lockdown via env var
- Alembic migrations on startup (all services)
- Sentry error tracking (all services)

### Deployment
- Docker Compose (9 services: traefik, frontend, 6 microservices, ml-platform)
- Production overrides (resource limits, CloudWatch)
- ECS Fargate task definition
- CI/CD with per-service Docker builds + frontend build
- `.env.example` with all 15 vars documented

### ML Integration (all 3 engineers wired)
- `officer.feedback` → ML3 feedback loop → review queue → retraining
- `hotspot.predictions` → analytics dashboard (HMM or fallback)
- `model.promoted` → scoring engine hot-reload
- Shared Postgres for ML3 (was SQLite)
- ml-platform-api in docker-compose with Traefik routing

---

## B — Remaining Tasks

### Phase C — Production Hardening (HIGH priority)

#### Detection Service (ML Eng 1)
| # | Task | Details |
|---|---|---|
| 1 | **Async `POST /detect`** | Move `model.predict_single()` to thread pool — blocks FastAPI event loop |
| 2 | **Kafka circuit breaker** | Graceful fallback when Kafka is down — `_publish_detection` crashes endpoint today |
| 3 | **DB connection resilience** | Buffer to local queue or return 503 when Postgres is down |
| 4 | **Stream frame cache limit** | Max-age on `_latest_frame` — frames accumulate indefinitely per camera |
| 5 | **Model hot-reload (YOLO)** | Watch model file, reload without service restart |
| 6 | **Prometheus metrics** | detection latency, throughput, model health — ops observability |
| 8 | **Thread-safety for YOLO** | Lock around `model.predict()` — torch may not be thread-safe under concurrent calls |

#### Backend Infrastructure
| # | Task | Details |
|---|---|---|
| 13 | **Redis-based rate limiter** | Currently in-memory dict — breaks under multiple replicas |
| 14 | **Dead letter queue** | `violations.dlq` topic defined but nothing produces/consumes it — failed messages silently dropped |
| 15 | **Notification consumer rewrite** | Uses fragile `threading.Thread` + `new_event_loop()` — race conditions likely |
| 16 | **CI conditional steps** | Build stage fails from missing AWS secrets — needs conditional or mock |
| 22 | **Auth end-to-end** | Password reset, email verification, proper onboarding — basic auth only today |

#### Defects / Code Quality
| # | Issue |
|---|---|
| 17 | `conftest.py` uses `sys.path.insert` instead of proper packaging |
| 18 | Module-level `producer = ParkSightProducer()` in `shared/kafka/producer.py` — crashes on import if Kafka unreachable |
| 19 | `CameraStream.stop()` 5s join timeout doesn't force-kill stalled threads |
| 20 | All services share one DB connection pool (`pool_size=20`) — should be per-service |

#### Security
| # | Task |
|---|---|
| 26 | Rate limiter in Redis (moved from #13 if not done) |
| 27 | Upload input validation (image size/type limits) |

#### Reliability
| # | Task |
|---|---|
| 28 | Per-service DB connection pool limits |
| 30 | Graceful degradation for Kafka/Postgres/Redis partial outage |

---

### Phase D — Scale & Observability (MEDIUM priority)

| # | Task | Details |
|---|---|---|
| 41 | **End-to-end tests** | Integration tests with real Kafka + Postgres + Redis — currently only unit tests |
| 43 | **Data retention / cleanup policy** | Violations, frames accumulate indefinitely — storage bloat |
| — | **JWT auth in ml-engineer-3** | Swap `X-Role` header for real JWT verification (`api/deps.py` — documented 1-file swap) |
| — | **CI → GHCR** | Switch from ECR (needs AWS) to free GitHub Container Registry |
| — | **Supabase + Upstash .env template** | Free PostGIS (Supabase), Redis (Upstash), Kafka (Upstash) — zero-cost production |
| — | **Move ml-platform Dockerfile** | Currently at `backend/services/ml-platform/Dockerfile` → should be `ml-engineer-3/Dockerfile` |
| — | **Update ECS task def** | Add `ml-platform-api` container + update old service names |
| — | **Frontend HMM display** | `predicted-hotspots` returns `state` + `hotspot_probability` — dashboard cards could show them |

---

### Phase E — Business Features (LOW priority)

| # | Task | Details |
|---|---|---|
| 36 | **Billing / subscriptions** | Can't monetize without it |
| 37 | **Multi-tenant isolation** | Organizations/workspaces — one tenant only today |
| 38 | **Granular user roles** | Beyond admin/operator/planner/officer/reviewer |
| 40 | **Mobile app** | `officers` API exists but no mobile client |
| 44 | **Model versioning / A/B testing** | Can't rollback bad YOLO models |
| — | **Deploy to Oracle Cloud** | Always Free VM + SSH deploy script |
| — | **`ml_engineer_2/` gitignore** | Re-remove from tracking or add to `.gitignore` |
| — | **Health check on ml-platform** | Ensure `/health` endpoint exists |
