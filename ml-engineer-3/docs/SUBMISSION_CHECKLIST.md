# ParkSight — Submission Checklist

Ordered by judging value within each group. Check off as you assemble the package.

## Files required (in repo)
- [ ] `README.md` (quickstart + phase summaries)
- [ ] `docs/FINAL_DELIVERABLES.md` (overview, architecture, limitations)
- [ ] `docs/DEMO_GUIDE.md` (commands, outputs, recovery)
- [ ] `docs/FINAL_AUDIT.md` (integration + readiness audit)
- [ ] `docs/FRONTEND_HANDOFF.md` (API contracts for FE)
- [ ] `docs/JUDGE_QNA.md` (anticipated Q&A)
- [ ] `docs/{training_pipeline,feedback_loop,hmm_prediction}.md`
- [ ] `pyproject.toml`, `Makefile`, `.env.example`, `.gitignore`, CI workflows
- [ ] Clean repo (no `*.db`, `_storage/`, `hmm_reports/`, `__pycache__/` committed)

## Screenshots required
- [ ] **Architecture diagram** (system + ML-plane boxes highlighted) — #1 value
- [ ] `risk_ranking.png` — ranked hotspot forecast
- [ ] `regimes_timeline.png` — HMM segmenting the daily cycle
- [ ] `demo-feedback` terminal — `20 approved → due=True → new dataset_version`
- [ ] `demo-hmm` terminal — ranked table + explanation line
- [ ] Swagger `/docs` — the API surface
- [ ] `report.html` — real mAP + per-class metrics (from pre-recorded run)
- [ ] `transition_matrix.png` — learned regime dynamics
- [ ] `make test` → `22 passed` + green lint

## Videos required
- [ ] **Full retrain on GPU** (train → evaluate → promote) — covers what can't run live
- [ ] (optional) rollback demo, once exercised
- [ ] (optional) 60–90s narrated walkthrough of the live demo as a backup

## Architecture diagrams required
- [ ] One-slide full ParkSight system (6 services + ML plane), ML Eng 3 boxes highlighted
- [ ] Retraining pipeline flow (from `docs/training_pipeline.md`)
- [ ] Feedback loop flow + sequence (from `docs/feedback_loop.md`)
- [ ] HMM data-flow + sequence (from `docs/hmm_prediction.md`)

## Demo assets required
- [ ] Repo cloned + `pip install -e ".[dev]"` working on the demo machine
- [ ] `make weights` run (yolov8n.pt cached for offline)
- [ ] Pre-generated `hmm_reports/*.png`
- [ ] Pre-recorded GPU train video + `report.html` saved locally
- [ ] Slide deck with the architecture + the three figures embedded
- [ ] Clean DB/storage state immediately before walking on stage
