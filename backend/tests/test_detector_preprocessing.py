import numpy as np
from detector.preprocessing import FramePreprocessor


def _frame(height=480, width=640) -> np.ndarray:
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)


def test_preprocess_output_shape():
    pre = FramePreprocessor(target_size=(640, 640))
    result = pre.preprocess(_frame(480, 640))
    assert result.shape == (1, 3, 640, 640)
    assert result.dtype == np.float32
    assert 0.0 <= result.min() <= result.max() <= 1.0


def test_preprocess_gray_input():
    pre = FramePreprocessor(target_size=(640, 640))
    gray = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
    result = pre.preprocess(gray)
    assert result.shape == (1, 3, 640, 640)


def test_preprocess_rgba_input():
    pre = FramePreprocessor(target_size=(640, 640))
    rgba = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
    result = pre.preprocess(rgba)
    assert result.shape == (1, 3, 640, 640)


def test_batch_preprocess():
    pre = FramePreprocessor(target_size=(640, 640))
    frames = [_frame(480, 640) for _ in range(2)]
    result = pre.preprocess_batch(frames)
    assert result.shape == (2, 3, 640, 640)


def test_letterbox_maintains_aspect_ratio():
    pre = FramePreprocessor(target_size=(640, 640))
    img, scale, pad = pre.letterbox(_frame(1080, 1920))
    assert img.shape[:2] == (640, 640)
    assert scale[0] == scale[1]
    assert pad[0] >= 0 and pad[1] >= 0


def test_letterbox_small_image():
    pre = FramePreprocessor(target_size=(640, 640))
    img, scale, pad = pre.letterbox(_frame(100, 200))
    assert img.shape[:2] == (640, 640)
    assert scale[0] >= 1.0


def test_stride_alignment():
    pre = FramePreprocessor(target_size=(640, 640), stride=32)
    result = pre.preprocess(_frame(480, 640))
    assert result.shape[2] % 32 == 0
    assert result.shape[3] % 32 == 0


def test_empty_batch():
    pre = FramePreprocessor(target_size=(640, 640))
    import pytest

    with pytest.raises(ValueError):
        pre.preprocess_batch([])
