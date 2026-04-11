# services/ai_opencv/ingestion/stream_reader.py
import logging
import threading
import time

import cv2

from domain.frame_packet import FramePacket


logger = logging.getLogger(__name__)


class StreamLoader:
    def __init__(self, camera_id, rtsp_url, target_fps=2, retry_interval=5):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.retry_interval = retry_interval

        self._latest_frame = None
        self._latest_capture_time = None
        self._latest_width = None
        self._latest_height = None
        self._frame_id = 0
        self._reconnect_count = 0
        self._dropped_frames = 0
        self._lock = threading.Lock()
        self._has_frame = threading.Event()

        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _open(self):
        import os

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer"
        while True:
            logger.info("Connecting source: %s", self.rtsp_url)
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                logger.info("Source connection established.")
                return cap

            cap.release()
            logger.warning("Source connection failed. Retrying in %ss...", self.retry_interval)
            time.sleep(self.retry_interval)

    def _reader_loop(self):
        cap = self._open()
        while True:
            ret, frame = cap.read()
            capture_time = time.time()
            if not ret:
                self._reconnect_count += 1
                logger.warning("Source read failed. Reconnecting...")
                cap.release()
                cap = self._open()
                continue

            with self._lock:
                if self._latest_frame is not None:
                    self._dropped_frames += 1
                self._latest_frame = frame
                self._latest_capture_time = capture_time
                self._latest_height, self._latest_width = frame.shape[:2]
            self._has_frame.set()

    def get_frames(self):
        last_yield_time = 0.0
        while True:
            self._has_frame.wait()
            current_time = time.time()
            if current_time - last_yield_time < self.frame_interval:
                time.sleep(0.01)
                continue

            with self._lock:
                frame = self._latest_frame
                capture_time = self._latest_capture_time
                width = self._latest_width
                height = self._latest_height
                self._frame_id += 1
                frame_id = self._frame_id

            last_yield_time = current_time
            yield FramePacket(
                camera_id=self.camera_id,
                frame_id=frame_id,
                frame=frame,
                capture_timestamp=capture_time,
                source_uri=self.rtsp_url,
                source_fps=float(self.target_fps),
                width=width,
                height=height,
                extra={"decoder_backend": "opencv"},
            )

    def get_stats_snapshot(self):
        return {
            "backend": "cpu",
            "reconnect_count": self._reconnect_count,
            "dropped_frames": self._dropped_frames,
            "source_uri": self.rtsp_url,
        }
