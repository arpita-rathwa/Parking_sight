# ParkSight — Demo Guide (ML Engineer 3)

A 5-minute demo of the learning loop + forecasting. Everything here was executed and
verified. Lead with forecasting (the wow), then prove the closed loop.

## 0. Prep BEFORE judging (not on stage)
```bash
pip install -e ".[dev]"                 # core + hmmlearn + sklearn + fastapi
make weights                            # cache yolov8n.pt while you have internet
rm -f *.db && rm -rf _storage hmm_reports   # clean state
# Pre-record on a GPU/connected machine: make install-train && make seed && make retrain
#   -> capture report.html + the train→eval→promote terminal as a short video
```

## 1. Forecasting (90s)
```bash
make demo-hmm
```
**Expected:** a ranked hotspot table —
```
zone       current      predicted    hotspot%  risk
zone_04    critical     critical          92%  0.92
zone_05    critical     critical          92%  0.92
zone_03    critical     critical          92%  0.92
zone_02    congested    congested         88%  0.61
zone_01    congested    congested         88%  0.61
zone_00    congested    congested         87%  0.61
```
plus an explanation line and three figures in `hmm_reports/`. Open
`hmm_reports/regimes_timeline.png` and say: *"the HMM segmented the daily cycle into
calm→building→congested→critical, unsupervised."*

## 2. API surface (45s)
```bash
make serve     # then open http://localhost:8001/docs
```
**Show:** the grouped endpoints (forecast / officer-feedback / review / retraining). In
Swagger, run `POST /forecast/hotspots` with header `X-Role: operator` → live JSON.

## 3. Closed learning loop (120s)
```bash
make demo-feedback
```
**Expected:**
```
approved=20  rejected=5
approved_since_last_retrain=20  threshold=20  due=True
RETRAIN TRIGGERED -> {'dataset_version': 'ds_2026...', 'model_version': None, 'promoted': False}
```
**Narrate:** officer flags a bad detection → reviewer corrects it → it's written into
training data → at threshold a **new content-hashed dataset version** is built from those
corrections. *"Every officer in the field quietly improves the model."*

## 4. Eval gate (45s) — PRE-RECORDED
Show `report.html` (real mAP from the GPU run) + the promotion gate rule: *"a new model
ships only if it beats the champion and regresses no class; otherwise it's rejected and
the old one stays."*

## 5. Architecture + close (30s)
Show the system diagram, highlight the three boxes you own, deliver the loop sentence:
*"bad detection in → officer correction → better model next cycle, fully automated; and
the HMM pre-stages officers before the jam forms."*

---

## What to SHOW judges
- `make demo-hmm` live + the three figures.
- Swagger `/docs` + one live forecast call.
- `make demo-feedback` live (the closed loop).
- Pre-recorded `report.html` + train→promote video.
- The architecture slide.
- `make test` → `22 passed` (credibility).

## What NOT to show live
- Real GPU YOLO **training** (slow + needs network for weights) → pre-recorded only.
- **S3 / Postgres / MSK Kafka** paths → never executed; explain via diagram.
- **Detection on a real video** → not in this repo (ML Eng 1).
- **Rollback** (`make rollback`) → logic sound but unexercised; pre-record if needed.
- Anything needing **internet** at the venue.

## Recovery steps if something breaks
| Symptom | Fix |
|---|---|
| Confusing/stale output | `rm -f *.db && rm -rf _storage hmm_reports`, rerun. |
| `make demo-hmm` shows all "calm" | you used old data; run `make demo-hmm` (it reseeds with `--retrain`). |
| `no trained HMM yet` (409) on forecast API | run `make demo-hmm` or `make train-hmm` first. |
| `yolov8n.pt` download fails | you skipped `make weights`; demo `make demo-feedback` (no weights needed) + play the pre-recorded train clip. |
| API "no such table" | use `make serve` (uvicorn fires startup); don't hand-roll a TestClient. |
| Import errors | `pip install -e ".[dev]"` from the repo root. |
| Everything is on fire | fall back to **slides + the three PNGs + the pre-recorded video**; they tell the whole story without a live run. |
