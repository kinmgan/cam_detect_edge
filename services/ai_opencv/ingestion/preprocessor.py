# services/ai_opencv/ingestion/preprocessor.py
import cv2
import numpy as np

from domain.preprocess_result import PreprocessResult


class Preprocessor:
    def __init__(self, motion_threshold=0.5):
        self.fgbg = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True,
        )
        self.motion_threshold = motion_threshold

    def _motion_percent(self, frame):
        fgmask = self.fgbg.apply(frame)
        return float((np.count_nonzero(fgmask) / fgmask.size) * 100)

    def has_motion(self, frame):
        return self._motion_percent(frame) > self.motion_threshold

    def analyze(self, frame_packet):
        frame = frame_packet.frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion_score = self._motion_percent(frame)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))

        return PreprocessResult(
            frame_packet=frame_packet,
            motion_score=motion_score,
            has_motion=motion_score > self.motion_threshold,
            blur_score=blur_score,
            brightness=brightness,
            contrast=contrast,
            hints={
                "source": "opencv_preprocessor",
                "color_format": "bgr",
            },
        )
