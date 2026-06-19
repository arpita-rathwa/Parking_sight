from detector.types import VEHICLE_TYPE_MAP, BoundingBox, DetectionResult, VehicleType


class DetectionPostprocessor:
    def __init__(self, confidence_threshold: float = 0.5, iou_threshold: float = 0.45):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold

    def nms(self, boxes: list[BoundingBox]) -> list[BoundingBox]:
        if not boxes:
            return []
        boxes_sorted = sorted(boxes, key=lambda b: b.confidence, reverse=True)
        keep = []
        while boxes_sorted:
            best = boxes_sorted.pop(0)
            keep.append(best)
            boxes_sorted = [b for b in boxes_sorted if best.iou(b) < self.iou_threshold]
        return keep

    def scale_boxes(
        self,
        boxes: list[BoundingBox],
        original_shape: tuple[int, int],
        scale: tuple[float, float],
        pad: tuple[float, float],
    ) -> list[BoundingBox]:
        orig_h, orig_w = original_shape
        scaled = []
        for b in boxes:
            x1 = (b.x1 - pad[0]) / scale[0]
            y1 = (b.y1 - pad[1]) / scale[1]
            x2 = (b.x2 - pad[0]) / scale[0]
            y2 = (b.y2 - pad[1]) / scale[1]
            x1 = max(0, min(x1, orig_w))
            y1 = max(0, min(y1, orig_h))
            x2 = max(0, min(x2, orig_w))
            y2 = max(0, min(y2, orig_h))
            scaled.append(
                BoundingBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=b.confidence,
                    class_id=b.class_id,
                )
            )
        return scaled

    def _map_vehicle_type(self, class_id: int) -> VehicleType:
        return VEHICLE_TYPE_MAP.get(class_id, VehicleType.UNKNOWN)

    def process(
        self,
        boxes: list[BoundingBox],
        original_shape: tuple[int, int],
        scale: tuple[float, float],
        pad: tuple[float, float],
    ) -> list[DetectionResult]:
        filtered = [b for b in boxes if b.confidence >= self.confidence_threshold]
        filtered = self.nms(filtered)
        scaled = self.scale_boxes(filtered, original_shape, scale, pad)
        return [
            DetectionResult(
                bbox=b,
                vehicle_type=self._map_vehicle_type(b.class_id),
                confidence=b.confidence,
            )
            for b in scaled
        ]

    def from_ultralytics(
        self,
        result,
        original_shape: tuple[int, int],
        scale: tuple[float, float],
        pad: tuple[float, float],
    ) -> list[DetectionResult]:
        if result.boxes is None or len(result.boxes) == 0:
            return []
        boxes = [
            BoundingBox(
                x1=float(box[0]),
                y1=float(box[1]),
                x2=float(box[2]),
                y2=float(box[3]),
                confidence=float(conf),
                class_id=int(cls),
            )
            for box, conf, cls in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.conf.cpu().numpy(),
                result.boxes.cls.cpu().numpy(),
            )
        ]
        return self.process(boxes, original_shape, scale, pad)
