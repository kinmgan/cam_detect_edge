# services/ai_opencv/ingestion/stream_reader.py
import cv2
import time

class StreamLoader:
    def __init__(self, rtsp_url, target_fps=2):
        self.rtsp_url = rtsp_url
        self.target_fps = target_fps
        self.cap = cv2.VideoCapture(rtsp_url)
        self.frame_interval = 1.0 / target_fps  # Khoảng cách thời gian giữa các frame cần lấy

    def get_frames(self):
        last_yield_time = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Lỗi kết nối RTSP. Đang thử lại...")
                self.cap.open(self.rtsp_url)
                continue

            current_time = time.time()
            # Chỉ lấy frame nếu đã đến đúng chu kỳ thời gian (2 FPS)
            if current_time - last_yield_time >= self.frame_interval:
                last_yield_time = current_time
                yield frame