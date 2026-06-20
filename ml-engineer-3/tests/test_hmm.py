"""HMM pre-staging tests. Skipped automatically if hmmlearn isn't installed
(keeps the torch-free CI green even without the forecast extra)."""

from __future__ import annotations

import pytest

pytest.importorskip("hmmlearn")
pytest.importorskip("sklearn")

from common.config import get_settings  # noqa: E402
from common.db import init_db  # noqa: E402
from hmm_prediction import features, infer, train_hmm  # noqa: E402
from scripts.seed_hmm_data import seed  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _seed_and_train():
    init_db()
    seed(zones=4, days=5)
    infer.reset_cache()
    train_hmm.train(n_iter=40)
    yield


def test_model_artifact_and_severity_ordering():
    _, _, meta = infer._load()
    assert meta["n_states"] == get_settings().hmm_n_states
    # severity means must be non-decreasing after relabeling (calm -> critical)
    sev = meta["severity_impact_means"]
    assert sev == sorted(sev)


def test_forecast_zone_outputs_are_valid_probabilities():
    z = features.list_zones()[0]
    p = infer.forecast_zone(z, persist=False)
    assert 0.0 <= p["risk_score"] <= 1.0
    assert 0.0 <= p["hotspot_probability"] <= 1.0
    assert 0.0 <= p["escalation_probability"] <= 1.0
    assert p["current_state_name"] in meta_names()
    assert p["explanation"]


def test_forecast_all_sorted_by_risk_desc():
    preds = infer.forecast_all(persist=False)
    risks = [p["risk_score"] for p in preds]
    assert risks == sorted(risks, reverse=True)
    assert len(preds) == len(features.list_zones())


def test_cold_start_zone_does_not_crash():
    p = infer.forecast_zone("zone_does_not_exist", persist=False)
    assert p["insufficient_history"] is True
    assert 0.0 <= p["risk_score"] <= 1.0


def test_hotter_zone_has_higher_risk():
    preds = {p["zone_id"]: p for p in infer.forecast_all(persist=False)}
    # zone_03 is seeded much hotter than zone_00
    assert preds["zone_03"]["risk_score"] >= preds["zone_00"]["risk_score"]


def meta_names():
    return infer._load()[2]["state_names"]
