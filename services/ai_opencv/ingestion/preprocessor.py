# services/ai_opencv/ingestion/preprocessor.py
import cv2
import numpy as np

class Preprocessor:
    def __init__(self):
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

    def has_motion(self, frame):
        """
        [Task 3] Logic hướng sự kiện: Bỏ qua khung hình nếu không có chuyển động.
        """
        fgmask = self.fgbg.apply(frame)
        # Tính toán phần trăm điểm ảnh thay đổi
        motion_percent = (np.count_nonzero(fgmask) / fgmask.size) * 100
        return motion_percent > 0.5 # Ví dụ: trên 0.5% diện tích ảnh thay đổi thì mới coi là có sự kiện