# services/ai_opencv/output_handler/redis_publisher.py
import json
import time

import redis


class RedisPublisher:
    def __init__(self, host="redis", port=6379, db=0):
        self.r = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def publish_preprocess_result(self, result):
        payload = {
            "camera_id": result.frame_packet.camera_id,
            "frame_id": result.frame_packet.frame_id,
            "capture_timestamp": result.frame_packet.capture_timestamp,
            "publish_timestamp": time.time(),
            "source_fps": result.frame_packet.source_fps,
            "frame_size": [result.frame_packet.width, result.frame_packet.height],
            "quality": {
                "motion_score": result.motion_score,
                "has_motion": result.has_motion,
                "blur_score": result.blur_score,
                "brightness": result.brightness,
                "contrast": result.contrast,
            },
            "hints": result.hints,
            "transport": {
                "frame_payload": "not_embedded",
                "status": "preprocess_only",
            },
        }
        self.r.set(f"camera:preprocess:{result.frame_packet.camera_id}", json.dumps(payload))

    def publish_metadata(self, camera_id, detections, capture_time):
        payload = {
            "camera_id": camera_id,
            "capture_timestamp": capture_time,
            "publish_timestamp": time.time(),
            "detections": {
                "yolo11_default": detections,
            },
            "metadata": {
                "fps_inference": 2.0,
            },
        }
        self.r.set(f"camera:metadata:{camera_id}", json.dumps(payload))
