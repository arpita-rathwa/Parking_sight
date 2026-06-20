# Frontend Integration Handoff — ParkSight ML Platform

Scope: the endpoints owned by the **ML platform (ML Engineer 3)** — feedback loop,
review console, retraining status, and HMM forecasting. Detection, scoring, priority
queue, alerts, and officer assignment are served by other services (detection-service,
scoring-service, queue-service, officer-app-api) and are **not** covered here.

**Base URL:** `http://<host>:8001`  ·  **Prefix:** `/api/v1`  ·  **Docs:** `/docs` (OpenAPI)

## Auth (MVP)
Every request needs an `X-Role` header. This is a demo stand-in for Backend's JWT —
when JWT lands, the role comes from the token and this header goes away.
Roles used: `officer`, `reviewer`, `operator`, `planner`, `admin`.

---

## Forecast endpoints (operator / planner / admin)

### POST `/api/v1/forecast/hotspots` — ranked forecast for all zones
Response:
```json
{
  "zones": [
    {
      "zone_id": "zone_04",
      "current_state": 3, "current_state_name": "critical",
      "predicted_state": 3, "predicted_state_name": "critical",
      "hotspot_probability": 0.92,
      "risk_score": 0.92,
      "escalation_probability": 0.0,
      "insufficient_history": false,
      "for_timestamp": "2026-06-19T18:30:00+00:00",
      "explanation": "Zone zone_04 is in a 'critical' regime ... 92% chance ..."
    }
  ]
}
```

### GET `/api/v1/forecast/heatmap` — map-overlay payload
```json
{ "horizon_minutes": 30,
  "zones": [ {"zone_id": "zone_04", "risk_score": 0.92, "hotspot_probability": 0.92, "state": "critical"} ] }
```
Join `zone_id` to the zone boundary (PostGIS) to render. Color by `risk_score`:
`>=0.66` red, `>=0.33` orange, else green.

### GET `/api/v1/forecast/zones/{zone_id}` — single zone + explanation
Same object shape as one element of `/hotspots` `zones[]`, including `explanation`
(use it as a tooltip / detail-panel string).

---

## Feedback endpoints (officer)

### POST `/api/v1/officer/feedback`
```json
// request
{ "violation_id": "v_88213", "officer_id": "off_009", "status": "unresolvable",
  "camera_id": "cam_042", "zone_id": "zone_17", "reason": "vehicle gone", "proposed_class": "van" }
// response
{ "feedback_id": "f3a9c1e2b4d5", "status": "unresolvable", "next_action": "upload_evidence" }
```
`status` is `resolved` or `unresolvable`. `proposed_class` ∈
`car, motorcycle, auto_rickshaw, bus, truck, van, other`.

### POST `/api/v1/officer/feedback/{feedback_id}/evidence` — multipart
Form field `file` (image). Response: `{ "feedback_id", "photo_s3_key", "event": "officer.feedback emitted" }`.

---

## Review console endpoints (reviewer = ML Eng 1)

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/v1/review/queue?status=pending` | — | `ReviewItem[]` |
| GET | `/api/v1/review/queue/{id}` | — | `ReviewItem` |
| POST | `/api/v1/review/queue/{id}/approve` | `{class_id?, bbox?, notes?}` | `ReviewItem` |
| POST | `/api/v1/review/queue/{id}/reject` | `{notes?}` | `ReviewItem` |

`ReviewItem`:
```json
{ "id": "...", "feedback_id": "...", "violation_id": "...", "image_s3_key": "evidence/...jpg",
  "proposed_class": "van", "proposed_class_id": 5, "proposed_bbox": {"cx":0.5,"cy":0.5,"w":0.6,"h":0.6},
  "status": "pending", "reviewer_id": null, "corrected_class": null, "dataset_image_key": null }
```
`bbox` is normalized `{cx, cy, w, h}` in `[0,1]`.

---

## Retraining status (reviewer / operator / admin)

GET `/api/v1/ml/retraining/status` →
```json
{ "approved_since_last_retrain": 23, "threshold": 50, "due": false, "last_retrain_started": "2026-06-19T..." }
```
POST `/api/v1/ml/retraining/trigger?full=false` → triggers a retrain (admin/reviewer).

---

## Polling vs realtime

| Data | Strategy |
|---|---|
| Forecast heatmap / hotspots | **Poll** every 30–60 s (horizon is 30 min) or refetch on demand. In prod, subscribe to the `hotspot.predictions` topic via the notification-service WebSocket. |
| Review queue | **Poll** every 15–30 s, or refetch after each approve/reject. |
| Retraining status badge | **Poll** every 30–60 s. |
| Live alerts / assignment | **WebSocket** — owned by notification-service / officer-app-api, not this API. |

---

## Dashboard widgets required (this slice)

1. **Predictive heatmap overlay** — `risk_score` per zone → color on the Leaflet map (the v2.0 pre-staging layer).
2. **Top-N hotspot panel** — ranked list from `/forecast/hotspots` with `predicted_state_name` + `explanation` tooltip.
3. **Review console** — queue table with the evidence image, proposed class, and approve/reject actions (reviewer view).
4. **Retraining status badge** — `approved_since_last_retrain / threshold`, "retrain due" indicator.
5. **Model card (optional)** — current champion version + headline metrics (from `model_registry` / SLA panel).

All payloads above are real response shapes from the running API (`/docs` is the source of truth).
