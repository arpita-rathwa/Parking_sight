---
title: ParkInsight
emoji: 🅿️
colorFrom: blue
colorTo: indigo
sdk: docker
dockerfile: backend/deploy/hf/Dockerfile
app_port: 7860
pinned: false
---

# ParkSight — AI Parking Enforcement

AI-powered parking violation detection, congestion scoring, officer dispatch, and predictive enforcement — built as a SaaS monorepo with 6 microservices, 3 ML pipelines, and a real-time React dashboard.

**🔴 Live Demo:** [voidistaken-parksight-demo.hf.space](https://voidistaken-parksight-demo.hf.space/)

---

## Problem

Illegal parking in dense Indian cities causes chronic congestion, delays emergency vehicles, and wastes thousands of patrol hours. Manual enforcement is reactive, slow, and resource-intensive — officers cannot be everywhere at once, and violations clear before enforcement arrives.

## Solution

ParkSight turns existing CCTV feeds into an automated enforcement pipeline:

1. **Detect** — YOLOv8 spots parking violations in real-time from camera RTSP streams
2. **Score** — LightGBM ranks zones by congestion impact, dispatches officers to the worst offenders first
3. **Forecast** — HMM predicts which zones will be congested in the next 30 minutes
4. **Learn** — Officer feedback triggers automatic model retraining, improving detection over time

---

## Try It Live

The hosted demo runs the full backend on Hugging Face Spaces (Docker SDK):

👉 **[https://voidistaken-parksight-demo.hf.space/](https://voidistaken-parksight-demo.hf.space/)**

Login with the demo credentials below (or `admin / admin123` after running the seed script locally) to explore the live dashboard, congestion heatmap, and dispatch queue.

---

## Architecture

```
CCTV RTSP ──► Detection ──► Scoring ──► Dispatch ──► Officer Mobile App
                │              │            │
                ▼              ▼            ▼
            violations.raw ──► zones.scored
                │                            │
                ▼                            ▼
          [3rd ML Pipeline] ──► model.promoted ──► Scoring (model reload)
                │                            │
                ▼                            ▼
          officer.feedback ◄── Status Updates
                │
                ▼
          Feedback Loop ─► Retrain ─► Promote
                │
                ▼
          HMM Forecast ─► hotspot.predictions ─► Dashboard
```

### Services (8 Docker containers)

| Service       | Port   | Role                                                  |
| ------------- | ------ | ------------------------------------------------------ |
| `traefik`     | 80/443 | Reverse proxy, TLS termination                          |
| `frontend`    | 80     | React 19 + shadcn/ui dashboard                          |
| `detection`   | 8001   | YOLOv8 violation detection (ML Eng 1)                   |
| `scoring`     | 8002   | Congestion scoring + LightGBM (ML Eng 2)                |
| `dispatch`    | 8003   | Priority queue + officer assignment                     |
| `analytics`   | 8004   | Dashboard API + heatmap + insights                      |
| `officers`    | 8005   | Officer mobile API + feedback emission                  |
| `alerts`      | 8006   | WebSocket real-time notifications                       |
| `ml-platform` | 8007   | HMM forecast + feedback loop + retraining (ML Eng 3)     |

### Infrastructure

| Component        | Tech                                            |
| ----------------- | ------------------------------------------------ |
| Database          | PostGIS 16 (spatial queries, zone boundaries)     |
| Cache             | Redis 7 (priority queue, API cache)               |
| Event Bus         | Kafka 7.6 (all service communication)             |
| Model Scoring     | LightGBM 4.6                                      |
| Object Detection  | YOLOv8 (Ultralytics)                              |
| Forecasting       | HMM (hmmlearn)                                    |
| Clustering        | HDBSCAN (scikit-learn)                            |

### Frontend

React 19 + TypeScript, Vite, Tailwind CSS v4, shadcn/ui, Recharts, TanStack Query, Leaflet maps.

---

## Quick Start (Local)

```bash
# 1. Start all services
cd backend
docker compose up -d

# 2. Seed demo data (zones, users, violations, scores)
docker compose run --rm seed

# 3. Open http://localhost
#    Login: admin / admin123
```

### Infrastructure services (started automatically)

- PostGIS on `:5432`
- Redis on `:6379`
- Kafka on `:9092`
- Traefik dashboard on `:8080`

---

## Key Features

- **Real-time detection** — YOLOv8 processes 5+ FPS per camera with ROI polygon filtering
- **Congestion scoring** — LightGBM model + heuristic fallback, scores every 60s per zone
- **Priority dispatch** — Redis ZSET ranks zones by impact, assigns nearest available officer
- **Predictive overlay** — HMM forecasts hotspot risk 30 min ahead, shown on dashboard map
- **Self-improving** — Officer feedback → review → auto-retrain → model promotion (closed loop)
- **WebSocket alerts** — Real-time violation and zone-scored push notifications
- **Role-based auth** — JWT with admin, operator, planner, officer, reviewer roles

---

## ML Pipeline

### ML Engineer 1 — Detection

YOLOv8 trained on Indian traffic data, 7 vehicle classes, RTSP stream management, ROI polygon filtering.

### ML Engineer 2 — Scoring + Clustering

HDBSCAN spatial clustering of violation hotspots → composite impact score → LightGBM validation model. Artifacts (`model.txt`, `cluster_summary.json`) consumed by scoring service.

### ML Engineer 3 — Forecasting + Retraining

- **HMM** — 4-regime traffic model (calm/building/congested/critical), 30-min forecast horizon
- **Feedback Loop** — Officer "unresolvable" reports → LabelReviewQueue → corrected labels → training set
- **Retraining** — Auto-triggered at 50 approved labels, champion/challenger gate with per-class regression checks
- **Promotion** — `model.promoted` Kafka event consumed by scoring service for hot-reload

---

## Event Integration Map

| Kafka Topic            | Producer        | Consumer(s)                |
| ------------------------ | ---------------- | ---------------------------- |
| `violations.raw`         | Detection         | Scoring Worker                |
| `zones.scored`           | Scoring Worker    | Dispatch, Alerts               |
| `officer.feedback`       | Officers API      | ML3 Feedback Loop               |
| `model.promoted`         | ML3 Training      | Scoring Service (reload)         |
| `hotspot.predictions`    | ML3 HMM           | Analytics Service                |
| `enforcement.updates`    | Officers API      | Alerts                            |
| `alerts`                 | All services      | WebSocket clients                  |

---

## Repository Structure

```
├── backend/                  # 6 microservices + shared libs
│   ├── services/
│   │   ├── detection/       # YOLOv8 RTSP pipeline (ML Eng 1)
│   │   ├── scoring/         # Congestion scoring + worker (ML Eng 2)
│   │   ├── dispatch/        # Priority queue + assignments
│   │   ├── analytics/       # Dashboard/heatmap API
│   │   ├── officers/        # Officer mobile API
│   │   ├── alerts/          # WebSocket notification push
│   │   └── ml-platform/     # Dockerfile for ML Eng 3 (forecast/retrain)
│   ├── shared/               # Auth, config, DB, Kafka, Redis, models
│   ├── scripts/               # seed.py demo data
│   ├── deploy/hf/              # Hugging Face Spaces Docker deployment
│   └── docker-compose.yml      # Full stack
├── frontend/                  # React 19 + shadcn/ui dashboard
├── deploy/                     # ECS task def, deployment docs
├── ml-engineer-3/               # ML Eng 3: HMM, retraining, feedback loop
└── ml_engineer_2/                # ML Eng 2: clustering notebook, scoring prototype
```

---

## Deployment

ParkSight is deployed in two ways:

- **Live demo** — [Hugging Face Spaces](https://voidistaken-parksight-demo.hf.space/) (Docker SDK, single-container build via `backend/deploy/hf/Dockerfile`)
- **Production** — see [`deploy/README.md`](deploy/README.md) for:
  - Local development (`docker compose`)
  - EC2 docker-compose production
  - AWS ECS Fargate
  - Environment variables reference

---

## Tech Stack Summary

| Layer        | Technologies                                                              |
| ------------ | ---------------------------------------------------------------------------- |
| Frontend     | React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, Recharts, Leaflet, TanStack Query |
| Backend      | FastAPI (Python), 6 microservices, JWT auth                                    |
| ML / CV      | YOLOv8 (Ultralytics), LightGBM, HDBSCAN, HMM (hmmlearn), scikit-learn            |
| Data         | PostGIS 16, Redis 7, Kafka 7.6                                                   |
| Infra        | Docker Compose, Traefik, AWS ECS Fargate, Hugging Face Spaces                     |
| CI/CD        | GitHub Actions (`.github/workflows`)                                              |



