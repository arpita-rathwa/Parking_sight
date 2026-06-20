# ParkSight ML-platform — hackathon demo commands
.PHONY: install install-train db seed dry-run retrain rollback test lint up down demo

install:        ## core deps (no torch) — fast, runs logic + demo seeding
	pip install -e ".[dev]"

install-train:  ## add YOLO/torch (needed for actual training on g4dn)
	pip install -e ".[train]"

db:             ## create ML-platform tables
	python scripts/init_db.py

seed:           ## generate synthetic demo dataset into storage staging/
	python scripts/seed_demo_data.py --n 120

dry-run:        ## ingest+validate+version only (no torch) — proves the spine in ~3s
	python -m training.pipeline --trigger manual --skip-train

retrain:        ## full pipeline: ingest->validate->version->train->eval->promote
	python -m training.pipeline --trigger schedule

retrain-fast:   ## live-demo-safe full pipeline: 3 epochs, small img (needs cached weights)
	TRAIN_EPOCHS=3 IMG_SIZE=320 BATCH=8 python -m training.pipeline --trigger schedule

weights:        ## pre-cache yolov8n.pt so the live train demo works OFFLINE
	python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" && echo "weights cached"

rollback:       ## roll champion back: make rollback V=yolov8_20260619_120000
	python -m training.promote rollback $(V)

serve:          ## run the feedback-loop API (docs at :8001/docs)
	uvicorn api.main:app --reload --port 8001

demo-feedback:  ## end-to-end feedback loop: submit -> review -> approve -> trigger retrain
	python scripts/demo_feedback.py --n 25 --threshold 20

consumer:       ## run the officer.feedback Kafka consumer (production path)
	python -m feedback_loop.consumer

seed-hmm:       ## seed synthetic congestion history (ends at evening rush)
	python scripts/seed_hmm_data.py --zones 6 --days 7

train-hmm:      ## train the HMM pre-staging model
	python -m hmm_prediction.train_hmm

demo-hmm:       ## end-to-end forecast: seed -> train -> rank hotspots -> figures
	python scripts/demo_hmm.py --zones 6 --days 7 --retrain

test:
	pytest

lint:
	black --check . && isort --check-only . && flake8 .

up:             ## local infra (postgres + minio) for the "prod-like" demo
	docker compose up -d

down:
	docker compose down

# One-liner for the judges: tables -> data -> spine
demo: db seed dry-run
	@echo "\n>>> Spine proven (no GPU). For the full train run: make install-train && make retrain"
