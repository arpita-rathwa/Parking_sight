from detector.types import VEHICLE_TYPE_MAP, BoundingBox, VehicleType


def test_bounding_box_properties():
    bbox = BoundingBox(x1=10, y1=20, x2=100, y2=200, confidence=0.9, class_id=3)
    assert bbox.width == 90
    assert bbox.height == 180
    assert bbox.center == (55, 110)
    assert bbox.area() == 16200


def test_bounding_box_iou_overlapping():
    a = BoundingBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9, class_id=3)
    b = BoundingBox(x1=5, y1=5, x2=15, y2=15, confidence=0.8, class_id=3)
    iou = a.iou(b)
    assert 0.14 < iou < 0.15


def test_bounding_box_iou_no_overlap():
    a = BoundingBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9, class_id=3)
    b = BoundingBox(x1=20, y1=20, x2=30, y2=30, confidence=0.8, class_id=3)
    assert a.iou(b) == 0.0


def test_bounding_box_iou_identical():
    a = BoundingBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9, class_id=3)
    assert a.iou(a) == 1.0


def test_vehicle_type_mapping():
    assert VEHICLE_TYPE_MAP[2] == VehicleType.MOTORCYCLE
    assert VEHICLE_TYPE_MAP[3] == VehicleType.CAR
    assert VEHICLE_TYPE_MAP[4] == VehicleType.TRUCK
    assert VEHICLE_TYPE_MAP[5] == VehicleType.BUS
    assert VEHICLE_TYPE_MAP.get(99, VehicleType.UNKNOWN) == VehicleType.UNKNOWN


def test_vehicle_type_values():
    assert VehicleType.CAR.value == "car"
    assert VehicleType.MOTORCYCLE.value == "motorcycle"
    assert VehicleType.AUTO_RICKSHAW.value == "auto_rickshaw"
    assert VehicleType.UNKNOWN.value == "unknown"
