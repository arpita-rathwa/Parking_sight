import cv2
import numpy as np


class FramePreprocessor:
    def __init__(self, target_size: tuple[int, int] = (1280, 720), stride: int = 32):
        self.target_width, self.target_height = target_size
        self.stride = stride

    def letterbox(
        self,
        img: np.ndarray,
        color: tuple[int, int, int] = (114, 114, 114),
    ) -> tuple[np.ndarray, tuple[float, float], tuple[float, float]]:
        shape = img.shape[:2]
        r = min(self.target_height / shape[0], self.target_width / shape[1])
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        dw = self.target_width - new_unpad[0]
        dh = self.target_height - new_unpad[1]
        dw, dh = (
            dw % self.stride,
            dh % self.stride,
        )
        if r != 1:
            interpolation = cv2.INTER_LINEAR if r > 1 else cv2.INTER_AREA
            img = cv2.resize(img, new_unpad, interpolation=interpolation)
        top, bottom = dh // 2, dh - dh // 2
        left, right = dw // 2, dw - dw // 2
        img = cv2.copyMakeBorder(
            img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )
        return img, (r, r), (dw / 2, dh / 2)

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        if frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        img, _, _ = self.letterbox(frame)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return img

    def preprocess_batch(self, frames: list[np.ndarray]) -> np.ndarray:
        return np.concatenate([self.preprocess(f) for f in frames], axis=0)
