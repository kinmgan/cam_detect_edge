# services/ai_opencv/core/queues_manager.py
from queue import Queue, Empty

class FrameQueueManager:
    def __init__(self, max_size=100):
        # Mỗi camera sẽ có một hàng đợi riêng để tránh nghẽn
        self.queues = {}
        self.max_size = max_size

    def add_frame(self, camera_id, frame):
        if camera_id not in self.queues:
            self.queues[camera_id] = Queue(maxsize=self.max_size)
        
        if not self.queues[camera_id].full():
            self.queues[camera_id].put(frame)

    def get_batch(self, batch_size=1):
        """Lấy một mẻ (batch) dữ liệu để tối ưu GPU RTX 4070"""
        batch_frames = []
        cam_ids = []
        
        for cam_id, q in self.queues.items():
            try:
                frame = q.get_nowait()
                batch_frames.append(frame)
                cam_ids.append(cam_id)
                if len(batch_frames) >= batch_size:
                    break
            except Empty:
                continue
        return cam_ids, batch_frames