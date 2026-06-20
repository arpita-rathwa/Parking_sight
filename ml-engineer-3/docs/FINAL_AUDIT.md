# ParkSight ML Platform — Final Integration & Demo-Readiness Audit
**Reviewer role:** Principal Engineer · **Window:** ~48 h to judging · **Scope:** integration + demo readiness, no new features.

> **The one thing to internalize:** this repository is **ML Engineer 3's slice** — the
> *learning loop* (retraining, feedback, forecasting). It is internally integrated and
> runs end-to-end on a laptop. The other five ParkSight features (detection, scoring,
> priority queue, officer assignment, dashboard) are **not in this repo** — they belong
> to ML Eng 1/2, Backend, and Frontend, and exist here only as **contracts, stubs, or
> synthetic stand-ins**. The demo and the judge answers must be honest about that line.

---

## 1. End-to-End Feature Matrix

| Feature | Backend Complete | API Complete | Tested | Demo Ready | Production Ready | Dependencies |
|---|---|---|---|---|---|---|
| YOLO Detection Pipeline | ❌ not in repo | ❌ (`/detect` is ME1) | ❌ | ❌ | ❌ | **ML Eng 1** (detection-service) |
| Congestion Scoring | ❌ synthetic only | ❌ | ❌ | ⚠️ via synthetic `congestion_scores` | ❌ | **ML Eng 2** (scoring-service) |
| Priority Queue | ❌ not in repo | ❌ | ❌ | ❌ | ❌ | **ML Eng 2** (queue-service) |
| Officer Assignment Flow | ❌ not in repo | ⚠️ our `/officer/feedback` only | ⚠️ feedback path only | ⚠️ feedback only | ❌ | **Backend** (officer-app-api) |
| Feedback Loop | ✅ | ✅ | ✅ 6 tests | ✅ | ⚠️ Kafka no-op, auth stub, default bbox | Backend (real `officer.feedback` producer) |
| Retraining Pipeline | ✅ | ✅ (trigger/status) | ✅ gate+logic; full train executed once | ✅ dry; full needs GPU | ⚠️ | ML Eng 1 (data + model.promoted consumer), GPU |
| Dataset Versioning | ✅ | ➖ internal | ✅ | ✅ | ✅ (S3 path untested) | — |
| Model Registry | ✅ | ⚠️ partial (status/trigger) | ✅ executed | ✅ | ⚠️ SQLite only; S3 path unexecuted | Backend (Postgres, S3) |
| Model Promotion | ✅ | ⚠️ trigger only | ✅ unit + executed | ✅ | ⚠️ | **ML Eng 1** (must consume `model.promoted`) |
| HMM Forecasting | ✅ | ✅ | ✅ 5 tests | ✅ | ⚠️ synthetic data | ML Eng 2 (real `congestion_scores`), Frontend (overlay) |
| Dashboard Integration | ❌ not in repo | ➖ API ready | ❌ | ❌ | ❌ | **Frontend** |

Legend: ✅ done · ⚠️ partial/with caveats · ❌ not built · ➖ n/a.
**Honest tally: 6 of 11 features are real and ours (feedback, retraining, dataset versioning, registry, promotion, HMM). 5 are other engineers' and absent here.**

---

## 2. Demo Flow Validation — the strongest 5-minute demo

Lead with forecasting (the wow), then prove the closed learning loop. **Everything below was executed and verified.** Do all prep before you walk on stage.

### Prep (do NOT do live)
```bash
pip install -e ".[dev]"          # core + hmmlearn + sklearn + fastapi
make weights                     # cache yolov8n.pt while you have internet (offline-proofs the train demo)
# Pre-record once on a GPU/connected machine: make install-train && make seed && make retrain  -> capture report.html + terminal
rm -f *.db && rm -rf _storage hmm_reports   # clean state so output is crisp
```

### Live script
1. **Forecasting (90s).**
   ```bash
   make demo-hmm
   ```
   Expected: a ranked hotspot table (zone_04/05/03 **critical, risk 0.92**; zone_00–02 congested 0.61), one plain-language explanation line, and three figures written to `hmm_reports/`. Open `hmm_reports/regimes_timeline.png` — "the model segmented the daily cycle into calm→building→congested→critical, unsupervised."

2. **API surface (45s).**
   ```bash
   make serve     # then open http://localhost:8001/docs
   ```
   Show the grouped endpoints (forecast / officer-feedback / review / retraining). Hit `POST /forecast/hotspots` from Swagger with `X-Role: operator` → live JSON.

3. **Closed learning loop (120s).**
   ```bash
   make demo-feedback
   ```
   Expected: `approved=20 rejected=5 → approved_since_last_retrain=20 threshold=20 due=True → RETRAIN TRIGGERED → new dataset_version`. Narrate: officer flags a bad detection → reviewer corrects it → it's written into training data → at threshold a **new content-hashed dataset version** is built from those corrections.

4. **Eval gate (45s) — pre-recorded.** Show `report.html` (real mAP from the GPU run) and the promotion gate: "a new model is promoted only if it beats the champion and regresses no class; otherwise it's rejected and the old one stays."

5. **Architecture + close (30s).** Show the system diagram, point to the three boxes you own, and deliver the loop sentence: *"bad detection in → officer correction → better model next cycle, fully automated; and the HMM pre-stages officers before the jam forms."*

### Avoid demonstrating live
- Real GPU YOLO **training** (slow, network for weights) — pre-record.
- Any **S3 / Postgres / MSK Kafka** path — never executed; explain via diagram only.
- **Detection on a real video** — not in this repo (ML Eng 1).
- Rollback (`make rollback`) — logic sound but never executed; pre-record if you must show it.
- Anything requiring **internet** at the venue.

---

## 3. Architecture Consistency Review — real issues only

**Verified consistent:** 8 tables defined and created (FK-enforced even on SQLite); 11 API routes wired; 3 event producers (`model.promoted`, `officer.feedback`, `hotspot.predictions`) all stamped `schema_version: 1`; S3 key layout is internally coherent (`datasets/staging/{images,labels}`, `datasets/{version}/`, `models/{version}/`, `models/champion.json`, `models/hmm/`). No code-level circular imports.

**Real issues / broken assumptions:**

1. **`model.promoted` has no consumer.** We emit it; detection-service (ML Eng 1) must consume it to hot-reload the champion. **The last hop of the retraining loop is unbuilt** — this is the #1 integration gap. *Mitigation: it's a contract; state it explicitly, don't imply it's wired.*
2. **`officer.feedback` producer is ours, not Backend's.** In production, officer-app-api must emit it on `/officer/status=unresolvable`. We emit it from our own endpoint as a stand-in. *Contract defined; Backend side not wired.*
3. **`congestion_scores` is double-owned.** It's ML Eng 2's table; we both *define* and *populate* it locally for the demo. Against the real Postgres, our `init_db()` must **not** create it (read-only in prod). *Integration note for deployment.*
4. **Retraining's real data source is a stub.** `ingest.py` reads `datasets/staging/` (fed by feedback). The production path — `violations` joined on `crop_s3_key` — is a documented TODO and depends on a **`violations.crop_s3_key` column that doesn't exist yet** (ME1 + Backend migration).
5. **No S3/Postgres/Kafka execution.** Everything ran on local FS + SQLite + no-op Kafka. The `STORAGE_BACKEND=s3` and real-broker code paths are written but **never executed** — treat as unverified.
6. **Auth is an `X-Role` header** across all endpoints — a stand-in for Backend's JWT, not real authz.
7. **Minor:** only `officer.feedback` has a JSON-schema file; `model.promoted` and `hotspot.predictions` are schema'd only in code. Low risk, worth a note.

No circular **code** dependencies. The feedback→retrain→model→detection→violation→feedback cycle is the intended *data* loop, not a build cycle.

---

## 4. Frontend Integration Requirements
See **`docs/FRONTEND_HANDOFF.md`** (standalone, hand it to the FE dev). Covers every endpoint with real request/response examples, polling-vs-realtime guidance, and the five dashboard widgets for this slice.

---

## 5. The 25 most likely judge questions

Format: **Q — ideal answer / weak answer / follow-up risk.**

### Computer Vision
1. **Why YOLOv8?** *Ideal:* single-stage real-time detector, strong speed/accuracy trade-off for CCTV at <2s latency, mature tooling for retraining. *Weak:* "it's popular." *Follow-up:* "v8 vs v9/v10/RT-DETR?" — know that nano was chosen for latency and that the registry makes swapping the backbone trivial.
2. **How do you handle night / rain / occlusion?** *Ideal:* the feedback loop surfaces exactly these failure cases (officer flags a miss) and folds them into the next dataset version; per-class drift would flag a regime change. *Weak:* "YOLO handles it." *Follow-up:* "show night accuracy" — you can't; concede it's roadmap.
3. **What's your detection accuracy?** *Ideal:* target mAP@0.5 > 85%; the eval framework reports it each retrain and the gate enforces it; cite the pre-recorded number. *Weak:* quote a synthetic-data number as if real. *Follow-up:* "on what data?" — be clear it's the held-out eval set.
4. **How are classes defined?** *Ideal:* frozen 7-class taxonomy (car, motorcycle, auto_rickshaw, bus, truck, van, other) shared with detection-service. *Weak:* vague. *Follow-up:* "why those 7?" — Indian street mix.

### MLOps
5. **Walk me through a retrain.** *Ideal:* ingest→validate→version→train→evaluate→promote, fail-closed, every run logged in `retraining_runs`. *Weak:* "we retrain weekly." *Follow-up:* "what if validation fails?" — pipeline aborts, champion untouched.
6. **How do you decide to ship a new model?** *Ideal:* champion/challenger gate — must clear an absolute mAP floor, beat the champion by a margin, and regress no class beyond tolerance. *Weak:* "if it's better." *Follow-up:* "define better" — the three gate conditions.
7. **How do you roll back?** *Ideal:* registry keeps every version; `rollback` restores a prior champion and re-emits `model.promoted`. *Weak:* "redeploy." *Follow-up:* "have you tested it?" — honest: logic implemented, not yet exercised end-to-end.
8. **How is a model reproducible?** *Ideal:* each model row stores its `dataset_version`, which is a content hash over the exact files — full lineage. *Weak:* "we save weights." *Follow-up:* "data versioning tool?" — S3 manifest + hash (DVC later).
9. **Where does training run?** *Ideal:* g4dn.xlarge via a scheduled GitHub Actions job; artifacts to S3 registry. *Weak:* "the cloud." *Follow-up:* "cost?" — spot + weekly cadence.
10. **How do you monitor the model in production?** *Ideal:* drift monitoring (confidence/precision/recall, class distribution) on a Grafana panel — *honest:* that's Phase 5, not built yet. *Weak:* claim it's done. *Follow-up:* "show the dashboard" — concede it's designed, not built.

### Feedback Loop
11. **How does officer feedback become training data?** *Ideal:* unresolvable + photo → event → review queue → reviewer corrects the label → written to staging → next dataset version. *Weak:* "officers retrain it." *Follow-up:* "who labels?" — ML Eng 1 reviews.
12. **What stops bad labels poisoning the model?** *Ideal:* every label passes human review (approve/reject) before entering a dataset; rejects are archived; the promotion gate is a second safety net. *Weak:* "we trust officers." *Follow-up:* "reviewer bottleneck?" — threshold batching + future CVAT.
13. **What triggers a retrain?** *Ideal:* 50 approved corrections since the last run, or a manual trigger. *Weak:* "automatically." *Follow-up:* "why 50?" — configurable; balances freshness vs. churn.
14. **Is the loop actually closed?** *Ideal:* yes — show `demo-feedback` producing a new content-hashed dataset version built from approved corrections. *Weak:* "conceptually." *Follow-up:* none — you can prove it live.

### HMM Forecasting
15. **Why an HMM, not an LSTM/transformer?** *Ideal:* interpretable latent regimes, trains on little data, fast, and the transition matrix is explainable to a city official — right tool for a hackathon-scale, explainability-first feature. *Weak:* "it was simple." *Follow-up:* "accuracy vs deep model?" — concede a deep model could win on raw accuracy but lose interpretability and data efficiency.
16. **What are the hidden states?** *Ideal:* four severity-ordered regimes (calm/building/congested/critical), relabeled post-training by mean impact so the order is meaningful. *Weak:* "four states." *Follow-up:* "why four?" — maps to enforcement urgency tiers; configurable.
17. **What exactly do you forecast?** *Ideal:* next-30-min hotspot probability + a 0–1 risk score per zone via one transition step from the current belief. *Weak:* "future congestion." *Follow-up:* "horizon?" — one 30-min bin; multi-step is a roll-forward.
18. **How do you validate the forecast?** *Ideal:* held-out backtest comparing predicted risk to realized congestion is the methodology — *honest:* not yet run on real data; shown on synthetic. *Weak:* claim validated. *Follow-up:* "ground truth?" — zone exceeding impact threshold next window.
19. **Where does the input data come from?** *Ideal:* the existing `congestion_scores` time-series from scoring-service; synthetic in the demo. *Weak:* imply it's live. *Follow-up:* "is it live now?" — no, synthetic; reads the real table in prod.
20. **Cold start for a new zone?** *Ideal:* falls back to a recent-average heuristic flagged `insufficient_history`. *Weak:* "it works." *Follow-up:* none.

### Scalability / Privacy / Smart City
21. **Scale to 500 cameras / many cities?** *Ideal:* event-driven, Kafka-partitioned by zone, horizontal detection workers, registry/forecast are batch — scales independently of the live path. *Weak:* "add servers." *Follow-up:* "bottleneck?" — GPU inference; addressed by a g4dn pool.
22. **GDPR / privacy?** *Ideal:* faces/plates purged post-inference; training uses **blurred vehicle-only crops** under a restricted, TTL'd prefix — we flagged and resolved this exact conflict in design. *Weak:* "we don't store faces." *Follow-up:* "but you retrain on images?" — yes, blurred crops only, with erasure hooks.
23. **What if the model is wrong and an officer is mis-dispatched?** *Ideal:* forecasts are decision support with an explanation, not autonomous action; humans dispatch; errors feed the loop. *Weak:* "the model is accurate." *Follow-up:* "accountability?" — audit log of every action.
24. **How does a city adopt this?** *Ideal:* per-city zone configs/thresholds, shared detection model, phased rollout; SLA reporting built into the roadmap. *Weak:* "they install it." *Follow-up:* "integration with existing CCTV?" — RTSP ingestion, standard.
25. **What's actually production-ready vs prototype?** *Ideal (this is the trust question):* the learning loop — feedback, versioning, registry, promotion gate, HMM, and the API — is real and tested; detection/scoring/queue/dashboard are teammates' services; S3/Postgres/Kafka/GPU are env-flips not yet executed. *Weak:* "it's all production-ready." *Follow-up:* the honest answer *prevents* the follow-up; the dishonest one invites a fatal one.

---

## 6. Final Risk Register (demo-affecting only)

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Judge asks to see live **detection on video** (not in repo) | High | High | Pre-frame scope up front: "we own the learning loop; detection is a teammate's service — here's the contract." Have the architecture slide ready. |
| `yolov8n.pt` won't download at venue (no/poor internet) | Med | High | `make weights` beforehand; demo the GPU-safe dry pipeline; keep a pre-recorded full-train clip. |
| Live GPU training too slow / fails on stage | Med | High | Never train live; use `make demo-feedback` (dry) + pre-recorded `make retrain`. |
| Stale `*.db` / `_storage` makes demo output confusing | Med | Med | `rm -f *.db && rm -rf _storage hmm_reports` immediately before each run. |
| Judge probes "is the data real?" on HMM/feedback | High | Med | Answer honestly: synthetic for the demo, reads real tables in prod; don't oversell. |
| Someone opens the S3/Postgres/Kafka path that was never run | Low | Med | Don't open it; explain via diagram; it's an env-flip, unverified. |
| Overclaiming "production-ready" invites a fatal follow-up | Med | High | Use the Q25 framing; lead with what's real. |
| `make serve` bare-TestClient lifespan gotcha | Low | Low | Use `make serve` (uvicorn fires lifespan); don't hand-roll TestClient. |
| numpy/opencv version-warning noise in logs | Low | Low | Cosmetic; ignore or filter; doesn't affect function. |

---

## 7. Final Submission Checklist (ordered by judging value)

1. **Architecture diagram** — one slide: full ParkSight system with the three ML-platform boxes you own highlighted.
2. **`risk_ranking.png`** — the ranked hotspot forecast (your headline visual).
3. **`regimes_timeline.png`** — HMM segmenting the daily cycle (your explainability proof).
4. **`demo-feedback` terminal capture** — `20 approved → due=True → new dataset_version` (closed-loop proof).
5. **`demo-hmm` terminal capture** — ranked table + the plain-language explanation line.
6. **Swagger `/docs` screenshot** — the API surface (looks like a real product).
7. **`report.html`** from the pre-recorded real-training run — actual mAP + per-class table.
8. **Pre-recorded full-retrain video** — train→eval→promote on the GPU (covers what you can't run live).
9. **`transition_matrix.png`** — learned regime dynamics.
10. **Test output screenshot** — `22 passed` + green lint/CI.
11. **Forecast API JSON responses** — `/forecast/hotspots`, `/heatmap`, `/zones/{id}`.
12. **Structured-log snippet** — showing `officer.feedback`, `model.promoted`, `hotspot.predictions` events firing.
13. **The four docs** — `README.md`, `docs/{training_pipeline,feedback_loop,hmm_prediction}.md` + `FRONTEND_HANDOFF.md`.

Top 6 carry the demo; 7–13 are depth/credibility for Q&A.
