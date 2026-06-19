from detector.postprocessing import DetectionPostprocessor
from detector.types import BoundingBox, VehicleType


def _make_box(x1, y1, x2, y2, conf, cls_id=3):
    return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2, confidence=conf, class_id=cls_id)


def test_nms_removes_overlapping():
    post = DetectionPostprocessor(confidence_threshold=0.0, iou_threshold=0.3)
    boxes = [
        _make_box(0, 0, 100, 100, 0.9),
        _make_box(10, 10, 110, 110, 0.8),
        _make_box(200, 200, 300, 300, 0.7),
    ]
    result = post.nms(boxes)
    assert len(result) == 2
    assert result[0].confidence == 0.9


def test_nms_keeps_separate():
    post = DetectionPostprocessor(confidence_threshold=0.0, iou_threshold=0.5)
    boxes = [
        _make_box(0, 0, 50, 50, 0.8),
        _make_box(100, 100, 150, 150, 0.7),
    ]
    result = post.nms(boxes)
    assert len(result) == 2


def test_nms_identical_detections():
    post = DetectionPostprocessor(confidence_threshold=0.0, iou_threshold=0.5)
    boxes = [
        _make_box(0, 0, 100, 100, 0.9),
        _make_box(0, 0, 100, 100, 0.8),
    ]
    result = post.nms(boxes)
    assert len(result) == 1
    assert result[0].confidence == 0.9


def test_nms_empty():
    post = DetectionPostprocessor()
    assert post.nms([]) == []


def test_confidence_filtering():
    post = DetectionPostprocessor(confidence_threshold=0.5, iou_threshold=0.5)
    boxes = [
        _make_box(0, 0, 50, 50, 0.9),
        _make_box(10, 10, 60, 60, 0.3),
        _make_box(100, 100, 150, 150, 0.6),
    ]
    result = post.process(boxes, (480, 640), scale=(1, 1), pad=(0, 0))
    assert len(result) == 2
    assert all(d.confidence >= 0.5 for d in result)


def test_scale_boxes():
    post = DetectionPostprocessor(confidence_threshold=0.0, iou_threshold=0.5)
    boxes = [_make_box(10, 20, 100, 200, 0.9)]
    scaled = post.scale_boxes(
        boxes, original_shape=(480, 640), scale=(0.5, 0.5), pad=(10, 20)
    )
    assert len(scaled) == 1
    s = scaled[0]
    assert s.x1 == 0
    assert s.y1 == 0
    assert s.x2 == 180
    assert s.y2 == 360


def test_scale_boxes_clamps():
    post = DetectionPostprocessor(confidence_threshold=0.0, iou_threshold=0.5)
    boxes = [_make_box(-10, -20, 700, 500, 0.9)]
    scaled = post.scale_boxes(
        boxes, original_shape=(480, 640), scale=(1.0, 1.0), pad=(0, 0)
    )
    assert scaled[0].x1 == 0
    assert scaled[0].y1 == 0
    assert scaled[0].x2 == 640
    assert scaled[0].y2 == 480


def test_vehicle_type_mapping():
    post = DetectionPostprocessor()
    assert post._map_vehicle_type(3) == VehicleType.CAR
    assert post._map_vehicle_type(2) == VehicleType.MOTORCYCLE
    assert post._map_vehicle_type(99) == VehicleType.UNKNOWN
