"""Tests for the deterministic stages — these run in CI with no torch/GPU/AWS.

Demo/local env is forced in tests/conftest.py before any app module imports.
"""

from __future__ import annotations

from pathlib import Path

from training.promote import evaluate_gate
from training.validate import validate
from training.versioning import _build_manifest  # noqa: WPS450 (white-box test)


def _write_sample(root: Path, split: str, stem: str, label: str):
    img_dir = root / "images" / split
    lbl_dir = root / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    (img_dir / f"{stem}.jpg").write_bytes(b"\xff\xd8\xff\xd9")  # minimal jpeg bytes
    (lbl_dir / f"{stem}.txt").write_text(label)


# ---- validation -----------------------------------------------------------
def test_validate_passes_on_clean_dataset(tmp_path):
    _write_sample(tmp_path, "train", "a", "0 0.5 0.5 0.2 0.2")
    _write_sample(tmp_path, "val", "b", "1 0.4 0.4 0.1 0.1")
    report = validate(tmp_path)
    assert report.ok
    assert report.class_counts == {"car": 1, "motorcycle": 1}


def test_validate_flags_out_of_range_class(tmp_path):
    _write_sample(tmp_path, "train", "a", "99 0.5 0.5 0.2 0.2")
    _write_sample(tmp_path, "val", "b", "1 0.4 0.4 0.1 0.1")
    report = validate(tmp_path)
    assert not report.ok
    assert any("out of range" in e for e in report.errors)


def test_validate_flags_unnormalized_bbox(tmp_path):
    _write_sample(tmp_path, "train", "a", "0 1.5 0.5 0.2 0.2")
    _write_sample(tmp_path, "val", "b", "1 0.4 0.4 0.1 0.1")
    report = validate(tmp_path)
    assert not report.ok
    assert any("not normalized" in e for e in report.errors)


def test_validate_flags_missing_val(tmp_path):
    _write_sample(tmp_path, "train", "a", "0 0.5 0.5 0.2 0.2")
    report = validate(tmp_path)
    assert not report.ok


# ---- versioning determinism ----------------------------------------------
def test_manifest_hash_is_deterministic(tmp_path):
    _write_sample(tmp_path, "train", "a", "0 0.5 0.5 0.2 0.2")
    m1, c1 = _build_manifest(tmp_path)
    m2, c2 = _build_manifest(tmp_path)
    assert m1 == m2 and c1 == c2
    assert c1["n_images"] == 1 and c1["n_train"] == 1


# ---- promotion gate -------------------------------------------------------
def test_first_model_promoted_above_floor():
    res = evaluate_gate({"map50": 0.61, "per_class": {}}, champion=None)
    assert res.promote


def test_first_model_rejected_below_floor():
    res = evaluate_gate({"map50": 0.40, "per_class": {}}, champion=None)
    assert not res.promote


def test_candidate_must_beat_champion():
    champ = {"map50": 0.80, "per_class": {"car": 0.8}}
    res = evaluate_gate({"map50": 0.801, "per_class": {"car": 0.8}}, champ)
    assert not res.promote  # below min_delta


def test_candidate_promoted_when_better():
    champ = {"map50": 0.70, "per_class": {"car": 0.7}}
    res = evaluate_gate({"map50": 0.78, "per_class": {"car": 0.75}}, champ)
    assert res.promote


def test_class_regression_blocks_promotion():
    champ = {"map50": 0.70, "per_class": {"car": 0.9, "bus": 0.8}}
    cand = {"map50": 0.85, "per_class": {"car": 0.9, "bus": 0.5}}  # bus collapses
    res = evaluate_gate(cand, champ)
    assert not res.promote
    assert any("regression" in r for r in res.reasons)


def test_unmeasured_class_does_not_block_promotion():
    # 'bus' had no val instances this cycle -> absent from candidate metrics.
    # That must NOT be treated as a regression (was the sparse-class bug).
    champ = {"map50": 0.70, "per_class": {"car": 0.9, "bus": 0.8}}
    cand = {"map50": 0.85, "per_class": {"car": 0.92}}  # bus simply not measured
    res = evaluate_gate(cand, champ)
    assert res.promote
