import time
from threading import Event, Thread
from typing import Callable

import numpy as np
from detector.model import DetectionModel
from detector.types import DetectionResult

DetectionCallback = Callable[[str, list[DetectionResult]], None]


class BatchInferencePipeline:
    def __init__(self, model: DetectionModel, interval: float = 2.0):
        self.model = model
        self.interval = interval
        self._thread: Thread | None = None
        self._stop_event = Event()
        self._callbacks: dict[str, DetectionCallback] = {}

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def active_callbacks(self) -> list[str]:
        return list(self._callbacks.keys())

    def set_callback(self, camera_id: str, callback: DetectionCallback) -> None:
        self._callbacks[camera_id] = callback

    def remove_callback(self, camera_id: str) -> None:
        self._callbacks.pop(camera_id, None)

    def tick(self, frames: dict[str, np.ndarray]) -> None:
        if not frames:
            return
        camera_ids = list(frames.keys())
        frame_list = [frames[cid] for cid in camera_ids]
        results = self.model.predict(frame_list)
        for cid, detections in zip(camera_ids, results):
            cb = self._callbacks.get(cid)
            if cb is None:
                continue
            try:
                cb(cid, detections)
            except Exception:
                pass

    def _loop(self, get_frames: Callable[[], dict[str, np.ndarray]]) -> None:
        while not self._stop_event.is_set():
            tick_start = time.time()
            frames = get_frames()
            self.tick(frames)
            elapsed = time.time() - tick_start
            sleep_time = max(0, self.interval - elapsed)
            if sleep_time > 0:
                self._stop_event.wait(sleep_time)

    def start(self, get_frames: Callable[[], dict[str, np.ndarray]]) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._loop,
            args=(get_frames,),
            name="batch-pipeline",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
