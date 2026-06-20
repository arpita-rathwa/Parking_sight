"""Model registry — S3-backed artifacts + DB status, with a single champion.

Layout in the models bucket:
    <version>/best.pt
    <version>/metrics.json
    <version>/report.html
    champion.json            <- pointer file detection-service can also read

DB `model_registry.status` is the source of truth; champion.json mirrors it for
services that prefer a flat pointer over a DB query.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from common.config import get_settings
from common.db import session_scope
from common.logging import get_logger
from common.models import ModelRegistry
from common.storage import Storage

log = get_logger("training.registry")
CHAMPION_KEY = "champion.json"


def register_candidate(
    version: str, weights_path: str | Path, dataset_version: str, metrics: dict | None = None
) -> str:
    s = get_settings()
    storage = Storage()
    weights_uri = storage.put_file(s.s3_bucket_models, f"{version}/best.pt", weights_path)

    with session_scope() as db:
        db.add(
            ModelRegistry(
                version=version,
                weights_uri=weights_uri,
                dataset_version=dataset_version,
                base_model=s.base_model,
                status="candidate",
                metrics=metrics or {},
            )
        )
    log.info("model_registered", version=version, weights_uri=weights_uri, status="candidate")
    return weights_uri


def set_model_metrics(version: str, metrics: dict) -> None:
    """Backfill metrics onto the registry row after evaluation completes."""
    with session_scope() as db:
        row = db.query(ModelRegistry).filter_by(version=version).one()
        row.metrics = metrics
    log.info("model_metrics_set", version=version, map50=metrics.get("map50"))


def get_champion() -> ModelRegistry | None:
    with session_scope() as db:
        return db.query(ModelRegistry).filter_by(status="champion").one_or_none()


def set_champion(version: str) -> None:
    s = get_settings()
    storage = Storage()
    with session_scope() as db:
        current = db.query(ModelRegistry).filter_by(status="champion").one_or_none()
        if current and current.version != version:
            current.status = "archived"
        target = db.query(ModelRegistry).filter_by(version=version).one()
        target.status = "champion"
        target.promoted_at = dt.datetime.now(dt.timezone.utc)
        weights_uri, metrics = target.weights_uri, target.metrics

    storage.put_json(
        s.s3_bucket_models, CHAMPION_KEY, {"version": version, "weights_uri": weights_uri, "metrics": metrics}
    )
    log.info("champion_set", version=version)


def get_champion_metrics() -> dict | None:
    champ = get_champion()
    return champ.metrics if champ else None
