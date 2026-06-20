"""SQLAlchemy models for the ML-platform tables introduced by ML Engineer 3.

These are additive migrations on the existing ParkSight Postgres (Backend owns
the Alembic migration in prod). In demo mode they live in SQLite. JSON columns
keep metrics flexible without a migration per metric.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Base(DeclarativeBase):
    pass


class DatasetVersion(Base):
    """Immutable snapshot of a training dataset (manifest + content hash)."""

    __tablename__ = "dataset_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    version: Mapped[str] = mapped_column(String, unique=True, index=True)
    content_hash: Mapped[str] = mapped_column(String, index=True)
    manifest_uri: Mapped[str] = mapped_column(String)
    n_images: Mapped[int] = mapped_column(Integer)
    n_train: Mapped[int] = mapped_column(Integer)
    n_val: Mapped[int] = mapped_column(Integer)
    class_counts: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class ModelRegistry(Base):
    """Every trained model. status in {candidate, champion, archived, rolled_back}."""

    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    version: Mapped[str] = mapped_column(String, unique=True, index=True)
    weights_uri: Mapped[str] = mapped_column(String)
    dataset_version: Mapped[str] = mapped_column(String, ForeignKey("dataset_versions.version"))
    base_model: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="candidate", index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    promoted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class ModelEvaluation(Base):
    """One row per (model, eval-set) run — powers historical comparison + trend."""

    __tablename__ = "model_evaluations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    model_version: Mapped[str] = mapped_column(String, ForeignKey("model_registry.version"), index=True)
    eval_set: Mapped[str] = mapped_column(String, default="val")
    map50: Mapped[float] = mapped_column(Float)
    map5095: Mapped[float] = mapped_column(Float)
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    f1: Mapped[float] = mapped_column(Float)
    per_class: Mapped[dict] = mapped_column(JSON, default=dict)
    report_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class RetrainingRun(Base):
    """Ledger of every pipeline execution for observability + audit."""

    __tablename__ = "retraining_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    trigger: Mapped[str] = mapped_column(String)  # schedule | feedback_threshold | manual
    status: Mapped[str] = mapped_column(String, default="running", index=True)
    dataset_version: Mapped[str | None] = mapped_column(String, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)
    promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class FeedbackSubmission(Base):
    """An officer's report on an assigned violation. status in {resolved, unresolvable}.
    Only 'unresolvable' + photo evidence feeds the ML relabel loop."""

    __tablename__ = "feedback_submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    violation_id: Mapped[str] = mapped_column(String, index=True)
    camera_id: Mapped[str | None] = mapped_column(String, nullable=True)
    zone_id: Mapped[str | None] = mapped_column(String, nullable=True)
    officer_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)  # resolved | unresolvable
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_class: Mapped[str | None] = mapped_column(String, nullable=True)
    photo_s3_key: Mapped[str | None] = mapped_column(String, nullable=True)
    crop_s3_key: Mapped[str | None] = mapped_column(String, nullable=True)  # prod: violations.crop_s3_key
    event_emitted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)


class LabelReviewQueue(Base):
    """Relabel task for the reviewer (ML Engineer 1). status in {pending, approved, rejected}.
    Approved items are written into the training staging set; rejected are archived."""

    __tablename__ = "label_review_queue"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    feedback_id: Mapped[str] = mapped_column(String, ForeignKey("feedback_submissions.id"), index=True)
    violation_id: Mapped[str] = mapped_column(String, index=True)
    image_s3_key: Mapped[str] = mapped_column(String)  # image to relabel (evidence or crop)
    proposed_class_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proposed_bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # [cx,cy,w,h] normalized
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    reviewer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    corrected_class_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corrected_bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dataset_image_key: Mapped[str | None] = mapped_column(String, nullable=True)  # where it landed in staging
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    decided_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class CongestionScore(Base):
    """EXISTING ParkSight table (owned by ML Eng 2 / Backend, TimescaleDB in prod).
    Defined here so the demo can populate + read it locally; in production the HMM
    reads the real table. Schema mirrors the documented backend schema."""

    __tablename__ = "congestion_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    speed_drop_percent: Mapped[float] = mapped_column(Float)
    violation_count: Mapped[int] = mapped_column(Integer)
    impact_score: Mapped[float] = mapped_column(Float)


class HmmPrediction(Base):
    """Output of the HMM pre-staging forecaster: per-zone hotspot risk for the next window."""

    __tablename__ = "hmm_predictions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    for_timestamp: Mapped[dt.datetime] = mapped_column(DateTime)
    current_state: Mapped[int] = mapped_column(Integer)
    current_state_name: Mapped[str] = mapped_column(String)
    predicted_state: Mapped[int] = mapped_column(Integer)
    predicted_state_name: Mapped[str] = mapped_column(String)
    hotspot_probability: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)
    escalation_probability: Mapped[float] = mapped_column(Float)
    insufficient_history: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
