import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class VehicleType(str, Enum):
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    AUTO_RICKSHAW = "auto_rickshaw"
    VAN = "van"
    SUV = "suv"
    UNKNOWN = "unknown"


VEHICLE_TYPE_MAP: dict[int, VehicleType] = {
    0: VehicleType.UNKNOWN,
    1: VehicleType.BICYCLE,
    2: VehicleType.MOTORCYCLE,
    3: VehicleType.CAR,
    4: VehicleType.TRUCK,
    5: VehicleType.BUS,
    6: VehicleType.VAN,
    7: VehicleType.SUV,
    8: VehicleType.AUTO_RICKSHAW,
}


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def area(self) -> float:
        return max(0, self.width) * max(0, self.height)

    def iou(self, other: "BoundingBox") -> float:
        x_left = max(self.x1, other.x1)
        y_top = max(self.y1, other.y1)
        x_right = min(self.x2, other.x2)
        y_bottom = min(self.y2, other.y2)
        inter = max(0, x_right - x_left) * max(0, y_bottom - y_top)
        union = self.area() + other.area() - inter
        return inter / union if union > 0 else 0.0


@dataclass
class DetectionResult:
    detection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    bbox: BoundingBox | None = None
    vehicle_type: VehicleType = VehicleType.UNKNOWN
    confidence: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    violation_type: str = ""
    frame_path: str = ""


@dataclass
class CameraConfig:
    camera_id: str
    rtsp_url: str
    latitude: float
    longitude: float
    frame_interval: int = 5
    roi_polygon: list[tuple[float, float]] | None = None
