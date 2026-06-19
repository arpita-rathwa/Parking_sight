import numpy as np
import pytest

from pipeline.batcher import BatchInferencePipeline
from detector.types import BoundingBox, DetectionResult


class _FakeModel:
    def __init__(self):
        self.called_with = None

    def predict(self, frames):
        self.called_with = frames
        return [
            [DetectionResult(bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9, class_id=3))],
            [],
        ]


def test_tick_dispatches_per_camera():
    model = _FakeModel()
    pipeline = BatchInferencePipeline(model=model)

    results_a = []
    results_b = []

    def cb_a(cid, dets):
        results_a.append((cid, dets))

    def cb_b(cid, dets):
        results_b.append((cid, dets))

    pipeline.set_callback("cam_1", cb_a)
    pipeline.set_callback("cam_2", cb_b)

    frames = {
        "cam_1": np.zeros((480, 640, 3), dtype=np.uint8),
        "cam_2": np.zeros((480, 640, 3), dtype=np.uint8),
    }
    pipeline.tick(frames)

    assert len(results_a) == 1
    assert results_a[0][0] == "cam_1"
    assert len(results_a[0][1]) == 1
    assert results_a[0][1][0].bbox.confidence == 0.9

    assert len(results_b) == 1
    assert results_b[0][0] == "cam_2"
    assert len(results_b[0][1]) == 0


def test_tick_empty_frames():
    model = _FakeModel()
    pipeline = BatchInferencePipeline(model=model)
    pipeline.tick({})
    assert model.called_with is None


def test_tick_no_callback():
    model = _FakeModel()
    pipeline = BatchInferencePipeline(model=model)
    frames = {"cam_1": np.zeros((480, 640, 3), dtype=np.uint8)}
    pipeline.tick(frames)
    assert model.called_with is not None


def test_tick_callback_exception_does_not_crash():
    model = _FakeModel()

    def failing_cb(cid, dets):
        raise RuntimeError("boom")

    pipeline = BatchInferencePipeline(model=model)
    pipeline.set_callback("cam_1", failing_cb)
    frames = {"cam_1": np.zeros((480, 640, 3), dtype=np.uint8)}
    pipeline.tick(frames)


def test_active_callbacks():
    model = _FakeModel()
    pipeline = BatchInferencePipeline(model=model)
    assert pipeline.active_callbacks == []

    pipeline.set_callback("cam_1", lambda c, d: None)
    assert pipeline.active_callbacks == ["cam_1"]

    pipeline.remove_callback("cam_1")
    assert pipeline.active_callbacks == []


def test_is_running_initially_false():
    model = _FakeModel()
    pipeline = BatchInferencePipeline(model=model)
    assert not pipeline.is_running


def test_start_stop():
    model = _FakeModel()
    pipeline = BatchInferencePipeline(model=model)

    frames_holder = {"cam_1": np.zeros((480, 640, 3), dtype=np.uint8)}

    def get_frames():
        return frames_holder

    pipeline.start(get_frames)
    assert pipeline.is_running

    pipeline.stop()
    assert not pipeline.is_running
