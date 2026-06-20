# ParkSight — Judge Q&A (Top 30)

Concise, honest answers. Lead with what's real; never overclaim.

**1. What problem does ParkSight solve?** Poor visibility into parking-induced congestion; it makes enforcement targeted and predictive instead of reactive.

**2. What did *you* (ML Eng 3) build?** The learning brain: retraining pipeline, model registry, officer feedback loop, and the HMM hotspot forecaster — all running and tested.

**3. What's NOT yours?** Detection (ML Eng 1), congestion scoring + priority queue (ML Eng 2), officer assignment (Backend), dashboard (Frontend). We define the contracts to them.

**4. Why YOLOv8?** Real-time single-stage detector with a strong speed/accuracy trade-off for CCTV under 2s latency; the registry makes swapping backbones trivial.

**5. Your detection accuracy?** Target mAP@0.5 > 85%, reported by the eval framework each retrain and enforced by the promotion gate (cite the pre-recorded number; it's measured on a held-out set).

**6. How do you handle night/rain/occlusion?** The feedback loop surfaces exactly those misses (officers flag them) and folds them into the next dataset version; drift monitoring would catch regime shifts (Phase 5, designed not built).

**7. Walk me through a retrain.** ingest → validate → version → train → evaluate → promote; fail-closed; every run logged in `retraining_runs`.

**8. How do you decide to ship a model?** Champion/challenger gate: clear an absolute mAP floor, beat the champion by a margin, and regress no class beyond tolerance.

**9. How do you roll back?** The registry keeps every version; rollback restores a prior champion and re-emits `model.promoted`. (Honest: logic done, not yet exercised end-to-end.)

**10. Is a model reproducible?** Yes — each model stores its `dataset_version`, a content hash over the exact training files. Full lineage.

**11. How does officer feedback become training data?** Unresolvable + photo → event → review queue → reviewer corrects the label → written to staging → next dataset version.

**12. What stops bad labels poisoning the model?** Human review before any label enters a dataset; rejects archived; the promotion gate is a second safety net.

**13. What triggers a retrain?** 50 approved corrections since the last run, or a manual trigger. Configurable.

**14. Is the loop actually closed?** Yes — we demo a new content-hashed dataset version built from approved corrections, live.

**15. Who reviews the labels?** ML Engineer 1 acts as reviewer in the MVP.

**16. Why an HMM, not a deep model?** Interpretable latent regimes, trains on little data, fast, and the transition matrix is explainable to a city official. A deep model might win on raw accuracy but loses interpretability and data efficiency.

**17. What are the hidden states?** Four severity-ordered regimes — calm, building, congested, critical — relabeled after training by mean impact so the order is meaningful.

**18. What do you forecast?** Next-30-min hotspot probability + a 0–1 risk score per zone, via one transition step from the current belief.

**19. How is the forecast validated?** Backtesting predicted risk vs. realized congestion is the methodology. (Honest: shown on synthetic data; not yet backtested on real data.)

**20. Where does the data come from?** The existing `congestion_scores` time-series from scoring-service; synthetic in the demo.

**21. Cold start for a new zone?** Falls back to a recent-average heuristic flagged `insufficient_history`.

**22. How does this scale to 500 cameras / many cities?** Event-driven, Kafka partitioned by zone, horizontal detection workers; registry + forecasting are batch and scale independently of the live path.

**23. GDPR / privacy?** Faces and plates purged post-inference; training uses **blurred vehicle-only crops** under a restricted, TTL'd prefix with erasure hooks — we flagged and resolved this conflict in design.

**24. What if the model is wrong and an officer is mis-dispatched?** Forecasts are decision support with an explanation, not autonomous action; humans dispatch; errors feed the loop; every action is audit-logged.

**25. What's production-ready vs prototype?** The learning loop, registry, gate, HMM, and API are real and tested; detection/scoring/queue/dashboard are teammates' services; S3/Postgres/Kafka/GPU are env-flips not yet executed.

**26. Why should a city trust an automated system?** It augments officers, never replaces judgment; it's explainable (every forecast has a reason), auditable, and improves measurably over time.

**27. What's the hardest technical problem you solved?** Closing the loop safely — making officer corrections flow into versioned data and gating model promotion so a bad retrain can't reach production.

**28. What would you build next with one more week?** The CV evaluation framework + drift monitoring (Phase 4/5) and wiring the real Kafka/S3/Postgres path end-to-end.

**29. How much is real vs mocked in this demo?** The code paths are real and tested; the *data* (congestion history, feedback photos) is synthetic, and infra runs locally. We're explicit about that line.

**30. If a judge asks to see live detection?** Honestly: detection is ML Eng 1's service and isn't in this repo; here's the architecture and the contract between us. (Pivot to the figures + the closed-loop demo.)
