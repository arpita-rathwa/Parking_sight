import logging
import os
import time
from threading import Lock, Thread

import numpy as np
import torch
from detector.postprocessing import DetectionPostprocessor
from detector.preprocessing import FramePreprocessor
from detector.types import BoundingBox, DetectionResult

logger = logging.getLogger("detection.model")


class DetectionModel:
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        target_size: tuple[int, int] = (1280, 720),
        half_precision: bool = True,
        device: str = "",
        watch_for_reload: bool = False,
        watch_interval: float = 10.0,
        shadow_model_path: str | None = None,
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.target_size = target_size
        self.half_precision = half_precision
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.shadow_model = None
        self.shadow_model_path = shadow_model_path
        self.preprocessor = FramePreprocessor(target_size=target_size)
        self.postprocessor = DetectionPostprocessor(
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
        )
        self._stream: torch.cuda.Stream | None = None
        self._lock = Lock()
        self._watch_for_reload = watch_for_reload
        self._watch_interval = watch_interval
        self._watcher_thread: Thread | None = None
        self._last_mtime: float = 0.0

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

        if os.path.isfile(self.model_path):
            self._last_mtime = os.path.getmtime(self.model_path)
        if self.shadow_model_path and os.path.isfile(self.shadow_model_path):
            self._load_shadow()
        if self._watch_for_reload:
            self._start_watcher()

    def _warmup(self) -> None:
        dummy = np.zeros(
            (self.preprocessor.target_height, self.preprocessor.target_width, 3),
            dtype=np.uint8,
        )
        with torch.cuda.amp.autocast(enabled=self.half_precision):
            self.predict([dummy])

    def is_loaded(self) -> bool:
        return self.model is not None

    def _load_shadow(self) -> None:
        from ultralytics import YOLO

        try:
            self.shadow_model = YOLO(self.shadow_model_path)
            if self.device == "cuda":
                self.shadow_model.to("cuda")
                if self.half_precision:
                    try:
                        self.shadow_model.half()
                    except Exception:
                        self.shadow_model.float()
            else:
                self.shadow_model.to("cpu")
            logger.info(
                "Shadow model loaded from %s", self.shadow_model_path
            )
        except Exception:
            logger.exception("Failed to load shadow model")
            self.shadow_model = None

    def _run_shadow(
        self, tensor: torch.Tensor
    ) -> list[list[DetectionResult]] | None:
        if self.shadow_model is None:
            return None
        try:
            raw_results = self.shadow_model(tensor, verbose=False)
            parsed: list[list[DetectionResult]] = []
            for i, raw in enumerate(raw_results):
                if raw.boxes is None or len(raw.boxes) == 0:
                    parsed.append([])
                    continue
                boxes = [
                    BoundingBox(
                        x1=float(b[0]), y1=float(b[1]),
                        x2=float(b[2]), y2=float(b[3]),
                        confidence=float(c), class_id=int(cls),
                    )
                    for b, c, cls in zip(
                        raw.boxes.xyxy.cpu().numpy(),
                        raw.boxes.conf.cpu().numpy(),
                        raw.boxes.cls.cpu().numpy(),
                    )
                ]
                detections = self.postprocessor.process(
                    boxes,
                    original_shape=(self.preprocessor.target_height, self.preprocessor.target_width),
                    scale=1.0, pad=(0, 0),
                )
                parsed.append(detections)
            return parsed
        except Exception:
            logger.exception("Shadow inference failed")
            return None

    def reload(self) -> None:
        logger.info("Reloading model from %s", self.model_path)
        with self._lock:
            self.model = None
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
            if os.path.isfile(self.model_path):
                self._last_mtime = os.path.getmtime(self.model_path)
            logger.info("Model reloaded successfully")

    def _watcher_loop(self) -> None:
        import logging

        logger = logging.getLogger("detection.model.watcher")
        while True:
            time.sleep(self._watch_interval)
            try:
                if not os.path.isfile(self.model_path):
                    continue
                current_mtime = os.path.getmtime(self.model_path)
                if current_mtime > self._last_mtime:
                    logger.info(
                        "Model file changed (%s), reloading...", self.model_path
                    )
                    self.reload()
            except Exception:
                logger.exception("Model watcher error")

    def _start_watcher(self) -> None:
        self._watcher_thread = Thread(
            target=self._watcher_loop,
            name="model-watcher",
            daemon=True,
        )
        self._watcher_thread.start()

    def predict(self, frames: list[np.ndarray]) -> list[list[DetectionResult]]:
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load() first.")
        if not frames:
            return []

        batch_tensor, scales, pads, shapes = self.preprocessor.preprocess_batch(frames)
        tensor = torch.from_numpy(batch_tensor).to(self.device)

        with self._lock:
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

        if self.shadow_model is not None:
            shadow_results = self._run_shadow(tensor)
            if shadow_results is not None:
                for i, (champ, shadow) in enumerate(zip(parsed, shadow_results)):
                    if len(champ) != len(shadow):
                        logger.info(
                            "Shadow diff frame %d: champion=%d shadow=%d",
                            i, len(champ), len(shadow),
                        )
                    for c, s in zip(champ, shadow):
                        if abs(c.confidence - s.confidence) > 0.2:
                            logger.debug(
                                "Shadow confidence diff: champ=%.3f shadow=%.3f",
                                c.confidence, s.confidence,
                            )
        return parsed

    def predict_single(self, frame: np.ndarray) -> list[DetectionResult]:
        return self.predict([frame])[0]
