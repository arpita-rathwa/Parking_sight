# Repository Cleanup & Final Structure

## Files to delete / never commit (runtime artifacts — all already in `.gitignore`)
| Path | Type | Action |
|---|---|---|
| `*.db` (e.g. `parksight_ml.db`, `demo.db`) | Generated SQLite (demo) | delete before zip; gitignored |
| `_storage/` | Local storage backend (datasets/models) | delete before zip; gitignored |
| `_run/`, `_test_storage/` | Pipeline + test scratch | delete; gitignored |
| `hmm_reports/` | Generated figures (regenerate via `make demo-hmm`) | delete from repo; keep copies as demo assets; gitignored |
| `runs/` | Ultralytics training output | delete; gitignored |
| `__pycache__/`, `*.egg-info/`, `build/` | Python build/cache | delete; gitignored |
| `.pytest_cache/` | pytest cache | delete; gitignored |
| `.env` | Real secrets (if ever created) | never commit; gitignored (`.env.example` is the template) |

**One-liner to clean before zipping/submitting:**
```bash
rm -rf _storage _run _test_storage hmm_reports runs *.db *.egg-info build .pytest_cache
find . -name __pycache__ -type d -prune -exec rm -rf {} +
```

## Duplicate files
None. (`seed_demo_data.py` = detection/feedback synthetic images; `seed_hmm_data.py` =
congestion time-series — different purposes, not duplicates.)

## Unused code
None dead. Two deliberate, documented stubs that are *not* dead code:
- `training/ingest.py` — the `violations`-table production source is a TODO seam (demo uses `staging/`).
- `feedback_loop/consumer.py::run_consumer` + the real-broker branch in `kafka_producer.py` — production Kafka paths, no-op in demo by design.

## Generated artifacts (keep as DEMO ASSETS, outside the repo)
`hmm_reports/regimes_timeline.png`, `transition_matrix.png`, `risk_ranking.png`, and the
pre-recorded `report.html` — copy these into your slide deck / submission folder, but keep
them out of the committed source tree.

## Clean final repository structure
```
parksight-ml-platform/
├── README.md
├── pyproject.toml · Makefile · .env.example · .gitignore · docker-compose.yml
├── .github/workflows/        ci.yml · weekly-retrain.yml
├── docker/                   Dockerfile.training
├── common/                   config · db · models · storage · logging · kafka_producer
│   └── schemas/officer_feedback.json
├── training/                 ingest · validate · versioning · train · evaluate · registry · promote · pipeline
│   └── configs/              train.yaml · promotion.yaml
├── feedback_loop/            service · consumer · review · trigger
├── hmm_prediction/           features · train_hmm · infer · states · visualize
│   └── configs/hmm.yaml
├── api/                      main · deps · schemas
│   └── routers/              feedback · review · retraining · forecast
├── scripts/                  init_db · seed_demo_data · seed_hmm_data · demo_feedback · demo_hmm
├── tests/                    conftest · test_pipeline_logic · test_feedback_flow · test_hmm   (22 tests)
└── docs/
    ├── FINAL_DELIVERABLES.md · DEMO_GUIDE.md · TEAM_STATUS.md
    ├── SUBMISSION_CHECKLIST.md · JUDGE_QNA.md · TEAM_UPDATE_WHATSAPP.md
    ├── FINAL_AUDIT.md · FRONTEND_HANDOFF.md · CLEANUP.md
    └── training_pipeline.md · feedback_loop.md · hmm_prediction.md
```
~52 source files. Everything else is generated and gitignored.
