import importlib.util
import sys
from pathlib import Path

import pytest

DETECTION_SERVICE_DIR = (
    Path(__file__).resolve().parent.parent / "services" / "detection"
)

pytestmark = pytest.mark.skip(
    reason="Requires Kafka running (module-level producer connection)"
)


@pytest.fixture(scope="module")
def detection_app():
    if str(DETECTION_SERVICE_DIR) not in sys.path:
        sys.path.insert(0, str(DETECTION_SERVICE_DIR))
    spec = importlib.util.spec_from_file_location(
        "detection_service_main",
        DETECTION_SERVICE_DIR / "main.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


def test_health(detection_app):
    from fastapi.testclient import TestClient

    client = TestClient(detection_app)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "detection-service"


def test_detect_no_auth(detection_app):
    from fastapi.testclient import TestClient

    client = TestClient(detection_app)
    resp = client.post("/api/v1/detect", params={"camera_id": "test-cam"})
    assert resp.status_code in (401, 403)
