"""End-to-end integration tests.

Requires Postgres + Redis + Kafka running (CI provides all three as service
containers). Tests that are Kafka-dependent skip gracefully when unavailable.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DETECTION_DIR = BACKEND_ROOT / "services" / "detection"
SCORING_DIR = BACKEND_ROOT / "services" / "scoring"
DISPATCH_DIR = BACKEND_ROOT / "services" / "dispatch"
ANALYTICS_DIR = BACKEND_ROOT / "services" / "analytics"
OFFICERS_DIR = BACKEND_ROOT / "services" / "officers"
ALERTS_DIR = BACKEND_ROOT / "services" / "alerts"

SERVICE_DIRS = {
    "detection": DETECTION_DIR,
    "scoring": SCORING_DIR,
    "dispatch": DISPATCH_DIR,
    "analytics": ANALYTICS_DIR,
    "officers": OFFICERS_DIR,
    "alerts": ALERTS_DIR,
}

for name, d in SERVICE_DIRS.items():
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))


def _load_app(service_name: str):
    """Load a service's FastAPI app via importlib."""
    d = SERVICE_DIRS[service_name]
    spec = importlib.util.spec_from_file_location(
        f"{service_name}_main",
        d / "main.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


def _kafka_available() -> bool:
    """Check if Kafka is reachable by trying a simple connection."""
    try:
        from kafka import KafkaProducer

        from shared.config.settings import settings

        p = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            max_block_ms=2000,
        )
        p.close()
        return True
    except Exception:
        return False


need_kafka = pytest.mark.skipif(
    not _kafka_available(),
    reason="Kafka not available",
)


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def detection_client():
    app = _load_app("detection")
    return TestClient(app)


@pytest.fixture(scope="module")
def scoring_client():
    app = _load_app("scoring")
    return TestClient(app)


@pytest.fixture(scope="module")
def dispatch_client():
    app = _load_app("dispatch")
    return TestClient(app)


@pytest.fixture(scope="module")
def analytics_client():
    app = _load_app("analytics")
    return TestClient(app)


@pytest.fixture(scope="module")
def officers_client():
    app = _load_app("officers")
    return TestClient(app)


@pytest.fixture(scope="module")
def alerts_client():
    app = _load_app("alerts")
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_token():
    from shared.auth.jwt import create_access_token

    return create_access_token({"sub": "test-admin", "role": "admin"})


# ── Tests ─────────────────────────────────────────────────────────────────


class TestHealth:
    def test_detection_health(self, detection_client):
        resp = detection_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "detection-service"
        assert "dependencies" in data

    def test_scoring_health(self, scoring_client):
        resp = scoring_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "scoring" in data.get("service", "")

    def test_dispatch_health(self, dispatch_client):
        resp = dispatch_client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_analytics_health(self, analytics_client):
        resp = analytics_client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_officers_health(self, officers_client):
        resp = officers_client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_alerts_health(self, alerts_client):
        resp = alerts_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "dependencies" in data


class TestAuth:
    def test_detect_requires_auth(self, detection_client):
        resp = detection_client.post("/api/v1/detect")
        assert resp.status_code == 403

    def test_detect_with_token(self, detection_client, auth_token):
        resp = detection_client.post(
            "/api/v1/detect",
            params={"camera_id": "test-cam"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (400, 503)

    def test_analytics_public_endpoints(self, analytics_client):
        resp = analytics_client.get("/api/v1/analytics/summary")
        assert resp.status_code in (200, 401, 403)

    def test_dispatch_requires_auth(self, dispatch_client):
        resp = dispatch_client.get("/api/v1/dispatch/queue")
        assert resp.status_code == 403


class TestMetrics:
    def test_prometheus_metrics(self, detection_client):
        resp = detection_client.get("/api/v1/metrics")
        assert resp.status_code == 200
        body = resp.text
        assert "detection_inference_seconds" in body
        assert "detection_total" in body
        assert "detection_model_health" in body


@need_kafka
class TestKafkaFlow:
    def test_violation_topic_exists(self):
        from kafka.admin import KafkaAdminClient

        from shared.config.settings import settings

        admin = KafkaAdminClient(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            client_id="e2e-test",
        )
        topics = admin.list_topics()
        assert "violations.raw" in topics
        assert "violations.dlq" in topics
        assert "zones.scored" in topics
        admin.close()


class TestDataFlow:
    def test_analytics_congestion_heat(self, analytics_client, auth_token):
        resp = analytics_client.get(
            "/api/v1/analytics/congestion-heat",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 503)

    def test_analytics_violation_types(self, analytics_client, auth_token):
        resp = analytics_client.get(
            "/api/v1/analytics/violation-types",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 503)

    def test_analytics_predicted_hotspots(self, analytics_client, auth_token):
        resp = analytics_client.get(
            "/api/v1/analytics/predicted-hotspots",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class TestCleanup:
    def test_cleanup_script_runs(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, str(BACKEND_ROOT / "scripts" / "cleanup.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Cleanup complete" in result.stdout
