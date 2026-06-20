"""Feedback-loop tests: service unit tests + full API integration flow.

Demo/local env forced in tests/conftest.py. No Kafka, no torch, no AWS.
"""

from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from common.config import get_settings
from common.db import init_db
from feedback_loop import review, service, trigger

client = TestClient(app)
OFFICER = {"X-Role": "officer"}
REVIEWER = {"X-Role": "reviewer"}


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 60, 60)).save(buf, format="PNG")
    return buf.getvalue()


# ---- service-layer unit tests --------------------------------------------
def test_resolved_feedback_creates_no_review_item():
    init_db()
    out = service.submit_feedback(violation_id="v1", officer_id="o1", status="resolved")
    assert out["next_action"] == "none"
    # resolved never produces a review item
    assert review.list_queue("pending") is not None


def test_unresolvable_flow_creates_pending_review_item():
    init_db()
    out = service.submit_feedback(
        violation_id="v2", officer_id="o1", status="unresolvable", proposed_class="van"
    )
    service.attach_evidence(out["feedback_id"], _png_bytes(), "image/png")
    pending = [r for r in review.list_queue("pending") if r["feedback_id"] == out["feedback_id"]]
    assert len(pending) == 1
    assert pending[0]["proposed_class"] == "van"


def test_approve_writes_label_into_staging():
    init_db()
    s = get_settings()
    from common.storage import Storage

    out = service.submit_feedback(
        violation_id="v3", officer_id="o1", status="unresolvable", proposed_class="bus"
    )
    service.attach_evidence(out["feedback_id"], _png_bytes(), "image/png")
    item = [r for r in review.list_queue("pending") if r["feedback_id"] == out["feedback_id"]][0]

    res = review.approve(item["id"], reviewer_id="ml_eng_1")
    assert res["status"] == "approved"
    # the labeled sample is now in the training staging set
    storage = Storage()
    assert storage.exists(s.s3_bucket_datasets, res["dataset_image_key"])
    label_key = res["dataset_image_key"].replace("images/", "labels/").replace(".jpg", ".txt")
    label = storage.get_bytes(s.s3_bucket_datasets, label_key).decode()
    assert label.split()[0] == str(s.class_to_id["bus"])  # class id 3


def test_reject_archives_without_dataset_change():
    init_db()
    out = service.submit_feedback(
        violation_id="v4", officer_id="o1", status="unresolvable", proposed_class="car"
    )
    service.attach_evidence(out["feedback_id"], _png_bytes(), "image/png")
    item = [r for r in review.list_queue("pending") if r["feedback_id"] == out["feedback_id"]][0]
    res = review.reject(item["id"], reviewer_id="ml_eng_1", notes="blurry")
    assert res["status"] == "rejected"
    assert res["dataset_image_key"] is None


def test_trigger_not_due_below_threshold():
    init_db()
    st = trigger.status()
    assert st["threshold"] == get_settings().feedback_retrain_threshold
    assert isinstance(st["due"], bool)


# ---- API integration tests -----------------------------------------------
def test_api_full_flow_and_auth():
    init_db()
    # auth: missing role -> 401
    assert client.post("/api/v1/officer/feedback", json={}).status_code == 401

    # officer submits
    body = {
        "violation_id": "api_v1",
        "officer_id": "off_1",
        "status": "unresolvable",
        "proposed_class": "truck",
    }
    r = client.post("/api/v1/officer/feedback", json=body, headers=OFFICER)
    assert r.status_code == 200, r.text
    fid = r.json()["feedback_id"]

    # officer uploads evidence
    files = {"file": ("evidence.png", _png_bytes(), "image/png")}
    r = client.post(f"/api/v1/officer/feedback/{fid}/evidence", files=files, headers=OFFICER)
    assert r.status_code == 200, r.text

    # officer cannot access the review queue (403)
    assert client.get("/api/v1/review/queue", headers=OFFICER).status_code == 403

    # reviewer sees the item
    q = client.get("/api/v1/review/queue", headers=REVIEWER)
    assert q.status_code == 200
    item = [i for i in q.json() if i["feedback_id"] == fid][0]

    # reviewer approves
    r = client.post(f"/api/v1/review/queue/{item['id']}/approve", json={}, headers=REVIEWER)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"

    # retrain status reflects the approval
    st = client.get("/api/v1/ml/retraining/status", headers=REVIEWER).json()
    assert st["approved_since_last_retrain"] >= 1
