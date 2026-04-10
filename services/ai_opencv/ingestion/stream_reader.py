# services/ai_opencv/ingestion/stream_reader.py
import cv2
import time
import logging
import threading

logger = logging.getLogger(__name__)

class StreamLoader:
    def __init__(self, rtsp_url, target_fps=2, retry_interval=5):
        self.rtsp_url = rtsp_url
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.retry_interval = retry_interval

        self._latest_frame = None
        self._latest_capture_time = None
        self._lock = threading.Lock()
        self._has_frame = threading.Event()

        # Background thread: liên tục đọc frame vào buffer
        # → không bao giờ để RTSP idle dù YOLO đang predict
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _open(self):
        """Mở hoặc mở lại RTSP, retry vô hạn cho đến khi thành công."""
        # Ép dùng TCP: tránh UDP packet loss gây timeout 30s
        import os
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer"
        while True:
            logger.info(f"Đang kết nối RTSP: {self.rtsp_url} ...")
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer tối thiểu, giảm lag
                logger.info("Kết nối RTSP thành công.")
                return cap
            cap.release()
            logger.warning(f"Kết nối RTSP thất bại. Thử lại sau {self.retry_interval}s...")
            time.sleep(self.retry_interval)

    def _reader_loop(self):
        """
        Chạy trên background thread.
        Liên tục đọc frame từ RTSP stream vào bộ nhớ đệm (_latest_frame).
        Không bao giờ dừng dù YOLO đang chạy trên main thread.
        """
        cap = self._open()
        while True:
            ret, frame = cap.read()
            capture_time = time.time()
            if not ret:
                logger.warning("Mất kết nối RTSP. Đang thử kết nối lại...")
                cap.release()
                cap = self._open()
                continue

            with self._lock:
                self._latest_frame = frame
                self._latest_capture_time = capture_time
            self._has_frame.set()

    def get_frames(self):
        """
        Generator cho main thread.
        Lấy frame mới nhất từ buffer mỗi frame_interval giây.
        """
        last_yield_time = 0
        while True:
            self._has_frame.wait()  # Chờ đến khi có frame đầu tiên
            current_time = time.time()
            if current_time - last_yield_time >= self.frame_interval:
                with self._lock:
                    frame = self._latest_frame
                    capture_time = self._latest_capture_time
                last_yield_time = current_time
                yield frame, capture_time
            else:
                # Ngủ ngắn tránh busy-wait
                time.sleep(0.01)