"""Central configuration for the ParkSight ML platform.

Everything is env-driven so the same code runs in three modes:
  * demo   -> local filesystem storage + SQLite + no Kafka  (laptop, zero AWS)
  * staging/prod -> MinIO/S3 + Postgres + MSK Kafka

Nothing here is hackathon-specific; the production switch is just env vars.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["demo", "staging", "prod"] = "demo"

    # ---- storage ----------------------------------------------------------
    storage_backend: Literal["local", "s3"] = "local"
    local_storage_dir: str = "./_storage"
    s3_endpoint_url: str | None = None  # set for MinIO, leave None for real S3
    s3_bucket_models: str = "parksight-models"
    s3_bucket_datasets: str = "parksight-datasets"
    s3_bucket_frames: str = "parksight-frames"
    aws_region: str = "ap-south-1"

    # ---- database ---------------------------------------------------------
    database_url: str = "postgresql+psycopg2://parksight:parksight@postgres:5432/parksight"

    # ---- kafka (optional in demo) ----------------------------------------
    kafka_bootstrap: str | None = None
    topic_model_promoted: str = "model.promoted"
    topic_officer_feedback: str = "officer.feedback"
    topic_hotspot_predictions: str = "hotspot.predictions"

    # ---- training ---------------------------------------------------------
    base_model: str = "yolov8n.pt"  # smallest model -> fast hackathon demo
    train_epochs: int = 30
    img_size: int = 640
    batch: int = 16
    device: str = "0"  # "0" for g4dn GPU, "cpu" for laptop demo
    train_val_split: float = 0.2

    # ---- HMM pre-staging (v2.0) -------------------------------------------
    hmm_n_states: int = 4  # calm / building / congested / critical
    hmm_window: int = 16  # recent bins fed to the forward pass
    hmm_min_history: int = 8  # below this -> cold-start fallback
    hmm_bin_minutes: int = 30  # forecast horizon = one bin ahead

    # ---- feedback loop ----------------------------------------------------
    feedback_retrain_threshold: int = 50  # approved labels that trigger a retrain
    reviewer_roles: tuple[str, ...] = ("admin", "reviewer")  # ML Eng 1 reviews as "reviewer"

    # ---- promotion gate ---------------------------------------------------
    promotion_min_map50: float = 0.50  # absolute floor a candidate must clear
    promotion_min_delta: float = 0.005  # must beat champion mAP50 by this much
    promotion_per_class_tolerance: float = 0.10  # max allowed per-class mAP50 regression

    # canonical class taxonomy (frozen, shared with detection-service / ML Eng 1)
    classes: tuple[str, ...] = (
        "car",
        "motorcycle",
        "auto_rickshaw",
        "bus",
        "truck",
        "van",
        "other",
    )

    @property
    def class_to_id(self) -> dict[str, int]:
        return {c: i for i, c in enumerate(self.classes)}


@lru_cache
def get_settings() -> Settings:
    return Settings()
