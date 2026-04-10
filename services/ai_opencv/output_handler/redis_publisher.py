# services/ai_opencv/output_handler/redis_publisher.py
import redis
import json
import time

class RedisPublisher:
    def __init__(self, host='redis', port=6379, db=0):
        self.r = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def publish_metadata(self, camera_id, detections):
        payload = {
            "camera_id": camera_id,
            "timestamp": time.time(),
            "detections": {
                "yolo11_default": detections
            },
            "metadata": {
                "fps_inference": 2.0
            }
        }
        # Đẩy dữ liệu vào channel hoặc key tùy backend thiết kế
        self.r.set(f"camera:metadata:{camera_id}", json.dumps(payload))