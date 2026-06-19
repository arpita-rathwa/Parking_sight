import numpy as np
import torch
from detector.postprocessing import DetectionPostprocessor
from detector.preprocessing import FramePreprocessor
from detector.types import BoundingBox, DetectionResult


class DetectionModel:
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        target_size: tuple[int, int] = (1280, 720),
        half_precision: bool = True,
        device: str = "",
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.target_size = target_size
        self.half_precision = half_precision
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.preprocessor = FramePreprocessor(target_size=target_size)
        self.postprocessor = DetectionPostprocessor(
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
        )
        self._stream: torch.cuda.Stream | None = None

    @property
    def stream(self) -> torch.cuda.Stream | None:
        if self.device == "cuda" and self._stream is None:
            self._stream = torch.cuda.Stream(device=self.device)
        return self._stream

    def load(self) -> None:
        from ultralytics import YOLO

        self.model = YOLO(self.model_path)
        if self.device == "cuda":
            self.model.to("cuda")
            if self.half_precision:
                try:
                    self.model.half()
                except Exception:
                    self.model.float()
            self._warmup()
        else:
            self.model.to("cpu")
            self.model.float()

    def _warmup(self) -> None:
        dummy = np.zeros(
            (self.preprocessor.target_height, self.preprocessor.target_width, 3),
            dtype=np.uint8,
        )
        with torch.cuda.amp.autocast(enabled=self.half_precision):
            self.predict([dummy])

    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, frames: list[np.ndarray]) -> list[list[DetectionResult]]:
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load() first.")
        if not frames:
            return []

        batch_tensor, scales, pads, shapes = self.preprocessor.preprocess_batch(frames)
        tensor = torch.from_numpy(batch_tensor).to(self.device)

        if self.device == "cuda":
            if self.half_precision:
                tensor = tensor.half()
            stream = self.stream
            if stream is not None:
                with torch.cuda.stream(stream):
                    with torch.cuda.amp.autocast(enabled=self.half_precision):
                        raw_results = self.model(tensor, verbose=False)
                    stream.synchronize()
            else:
                with torch.cuda.amp.autocast(enabled=self.half_precision):
                    raw_results = self.model(tensor, verbose=False)
        else:
            raw_results = self.model(tensor, verbose=False)

        parsed: list[list[DetectionResult]] = []
        for i, raw in enumerate(raw_results):
            if raw.boxes is None or len(raw.boxes) == 0:
                parsed.append([])
                continue
            boxes = [
                BoundingBox(
                    x1=float(b[0]),
                    y1=float(b[1]),
                    x2=float(b[2]),
                    y2=float(b[3]),
                    confidence=float(c),
                    class_id=int(cls),
                )
                for b, c, cls in zip(
                    raw.boxes.xyxy.cpu().numpy(),
                    raw.boxes.conf.cpu().numpy(),
                    raw.boxes.cls.cpu().numpy(),
                )
            ]
            detections = self.postprocessor.process(
                boxes,
                original_shape=shapes[i],
                scale=scales[i],
                pad=pads[i],
            )
            parsed.append(detections)
        return parsed

    def predict_single(self, frame: np.ndarray) -> list[DetectionResult]:
        return self.predict([frame])[0]
