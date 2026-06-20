import time
from threading import Event, Lock, Thread

import cv2
import numpy as np


class CameraStream:
    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        frame_interval: float = 5.0,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
        frame_max_age: float = 10.0,
    ):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.frame_interval = frame_interval
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.frame_max_age = frame_max_age

        self._cap: cv2.VideoCapture | None = None
        self._thread: Thread | None = None
        self._stop_event = Event()
        self._lock = Lock()
        self._latest_frame: np.ndarray | None = None
        self._latest_frame_time: float = 0.0
        self._frame_count = 0
        self._reconnect_attempts = 0
        self._connected = False
        self._last_grab_time = 0.0
        self._on_frame_callback = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def latest_frame(self) -> np.ndarray | None:
        with self._lock:
            if self._latest_frame is None:
                return None
            if time.time() - self._latest_frame_time > self.frame_max_age:
                self._latest_frame = None
                return None
            return self._latest_frame.copy()

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def set_on_frame_callback(self, callback):
        self._on_frame_callback = callback

    def _connect(self) -> bool:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
        self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap.set(cv2.CAP_PROP_FPS, 30)
        if not self._cap.isOpened():
            self._cap.release()
            self._cap = None
            self._connected = False
            return False
        self._connected = True
        self._reconnect_attempts = 0
        return True

    def _grab_loop(self):
        while not self._stop_event.is_set():
            if not self._connected:
                current_delay = min(
                    self.reconnect_delay * (2**self._reconnect_attempts),
                    self.max_reconnect_delay,
                )
                if self._reconnect_attempts > 0:
                    time.sleep(current_delay)
                self._reconnect_attempts += 1
                if self._connect():
                    continue
                continue

            now = time.time()
            if now - self._last_grab_time < self.frame_interval:
                time.sleep(0.05)
                continue

            ret, frame = self._cap.read()
            if not ret:
                self._connected = False
                if self._cap is not None:
                    self._cap.release()
                    self._cap = None
                continue

            with self._lock:
                self._latest_frame = frame
                self._latest_frame_time = time.time()
            self._frame_count += 1
            self._last_grab_time = now

            if self._on_frame_callback:
                try:
                    self._on_frame_callback(self.camera_id, frame)
                except Exception:
                    pass

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._grab_loop,
            name=f"camera-{self.camera_id}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        with self._lock:
            self._latest_frame = None
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._connected = False

    def grab_frame(self) -> np.ndarray | None:
        if not self._connected or self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    def get_reconnect_stats(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "connected": self._connected,
            "running": self.is_running,
            "frame_count": self._frame_count,
            "reconnect_attempts": self._reconnect_attempts,
        }
