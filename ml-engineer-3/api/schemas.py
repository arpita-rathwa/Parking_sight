"""Pydantic models for the feedback-loop API (FastAPI request/response validation)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from common.config import get_settings

_CLASSES = get_settings().classes


class FeedbackCreate(BaseModel):
    violation_id: str
    officer_id: str
    status: Literal["resolved", "unresolvable"]
    camera_id: str | None = None
    zone_id: str | None = None
    reason: str | None = None
    proposed_class: str | None = None
    crop_s3_key: str | None = None

    @field_validator("proposed_class")
    @classmethod
    def _valid_class(cls, v):
        if v is not None and v not in _CLASSES:
            raise ValueError(f"proposed_class must be one of {_CLASSES}")
        return v


class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str
    next_action: str


class BBox(BaseModel):
    cx: float = Field(ge=0, le=1)
    cy: float = Field(ge=0, le=1)
    w: float = Field(ge=0, le=1)
    h: float = Field(ge=0, le=1)


class ApproveRequest(BaseModel):
    class_id: int | None = Field(default=None, ge=0, le=len(_CLASSES) - 1)
    bbox: BBox | None = None
    notes: str | None = None


class RejectRequest(BaseModel):
    notes: str | None = None


class ReviewItem(BaseModel):
    id: str
    feedback_id: str
    violation_id: str
    image_s3_key: str
    proposed_class: str | None = None
    proposed_class_id: int | None = None
    proposed_bbox: dict | None = None
    status: str
    reviewer_id: str | None = None
    corrected_class: str | None = None
    corrected_class_id: int | None = None
    dataset_image_key: str | None = None
    decision_notes: str | None = None
    created_at: dt.datetime | None = None
    decided_at: dt.datetime | None = None


class RetrainStatus(BaseModel):
    approved_since_last_retrain: int
    threshold: int
    due: bool
    last_retrain_started: dt.datetime | None = None
