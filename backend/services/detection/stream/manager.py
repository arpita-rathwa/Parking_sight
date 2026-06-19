from typing import Callable

import numpy as np
from detector.types import CameraConfig
from stream.camera import CameraStream

FrameCallback = Callable[[str, object], None]


class StreamManager:
    def __init__(self):
        self._cameras: dict[str, CameraStream] = {}

    @property
    def active_cameras(self) -> list[str]:
        return list(self._cameras.keys())

    @property
    def camera_count(self) -> int:
        return len(self._cameras)

    def add_camera(self, config: CameraConfig) -> CameraStream:
        if config.camera_id in self._cameras:
            raise ValueError(f"Camera {config.camera_id} already registered")
        stream = CameraStream(
            camera_id=config.camera_id,
            rtsp_url=config.rtsp_url,
            frame_interval=config.frame_interval,
        )
        self._cameras[config.camera_id] = stream
        return stream

    def remove_camera(self, camera_id: str) -> None:
        stream = self._cameras.pop(camera_id, None)
        if stream is not None:
            stream.stop()

    def get_camera(self, camera_id: str) -> CameraStream | None:
        return self._cameras.get(camera_id)

    def start_all(self) -> None:
        for stream in self._cameras.values():
            stream.start()

    def stop_all(self) -> None:
        for stream in self._cameras.values():
            stream.stop()
        self._cameras.clear()

    def start_camera(self, camera_id: str) -> None:
        stream = self._cameras.get(camera_id)
        if stream is not None:
            stream.start()

    def stop_camera(self, camera_id: str) -> None:
        stream = self._cameras.get(camera_id)
        if stream is not None:
            stream.stop()

    def set_global_callback(self, callback: FrameCallback) -> None:
        for stream in self._cameras.values():
            stream.set_on_frame_callback(callback)

    def set_camera_callback(self, camera_id: str, callback: FrameCallback) -> None:
        stream = self._cameras.get(camera_id)
        if stream is not None:
            stream.set_on_frame_callback(callback)

    def get_latest_frames(self) -> dict[str, np.ndarray]:
        frames = {}
        for cid, stream in self._cameras.items():
            frame = stream.latest_frame
            if frame is not None:
                frames[cid] = frame
        return frames

    def get_all_stats(self) -> list[dict]:
        return [s.get_reconnect_stats() for s in self._cameras.values()]

    def get_camera_stats(self, camera_id: str) -> dict | None:
        stream = self._cameras.get(camera_id)
        if stream is None:
            return None
        return stream.get_reconnect_stats()
