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
        else:
            self.model.to("cpu")
            self.model.float()

    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, frames: list[np.ndarray]) -> list[list[DetectionResult]]:
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load() first.")
        all_results = []
        for frame in frames:
            original_shape = frame.shape[:2]
            preprocessed = self.preprocessor.preprocess(frame)
            preprocessed_tensor = torch.from_numpy(preprocessed).to(self.device)
            if self.half_precision and self.device == "cuda":
                preprocessed_tensor = preprocessed_tensor.half()
            results = self.model(preprocessed_tensor, verbose=False)
            raw_boxes = results[0].boxes
            if raw_boxes is None or len(raw_boxes) == 0:
                all_results.append([])
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
                    raw_boxes.xyxy.cpu().numpy(),
                    raw_boxes.conf.cpu().numpy(),
                    raw_boxes.cls.cpu().numpy(),
                )
            ]
            detections = self.postprocessor.process(
                boxes,
                original_shape=original_shape,
                scale=self.preprocessor.letterbox(frame)[1],
                pad=self.preprocessor.letterbox(frame)[2],
            )
            all_results.append(detections)
        return all_results

    def predict_single(self, frame: np.ndarray) -> list[DetectionResult]:
        return self.predict([frame])[0]
