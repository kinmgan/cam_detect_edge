import json
import logging
import os
import time

import redis
import cv2
import numpy as np

from utils.frame_store import load_frame
from core.person_detector import PersonDetector

logger = logging.getLogger(__name__)

def ensure_group(client, stream_name: str, group_name: str):
    """Giúp tạo consumer group an toàn mà không lỗi nếu group đã tồn tại"""
    try:
        client.xgroup_create(stream_name, group_name, id="$", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise

class StreamConsumer:
    def __init__(self):
        # Lấy biến môi trường
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        password = os.getenv("REDIS_PASSWORD", None)
        self.preprocess_stream = os.getenv("PREPROCESS_STREAM", "camera:preprocess_stream")
        self.detections_stream = os.getenv("DETECTIONS_STREAM", "camera:detections_stream")
        self.group_name = os.getenv("STREAM_GROUP", "ai_detector_group")
        self.consumer_name = os.getenv("CONSUMER_NAME", "worker_1")
        
        self.yolo_path = os.getenv("YOLO_WEIGHTS", "yolov11s.pt")
        
        # Gắn kết nối Redis (hỗ trợ cả có và không password)
        self.client = redis.Redis(host=host, port=port, password=password, decode_responses=True)
        ensure_group(self.client, self.preprocess_stream, self.group_name)
        
        # Kho lưu trữ các detector ứng với mỗi camera để chống dính ID Tracker
        self.detectors_dict = {}
        logger.info(f"Consumer đã sẵn sàng nghe từ {self.preprocess_stream}...")

    def run(self):
        logger.info("Vòng lặp Consumer bắt đầu (Hỗ trợ Auto-reconnect)...")
        while True:
            try:
                # Tăng count lên 50 để bóc hàng loạt tin nhắn cũ (nếu có tồn đọng)
                response = self.client.xreadgroup(
                    self.group_name, 
                    self.consumer_name, 
                    {self.preprocess_stream: ">"}, 
                    count=50, 
                    block=5000
                )
                
                if not response:
                    # Log định kỳ để biết service vẫn sống (ví dụ mỗi khi timeout 5s)
                    logger.debug("Đang chờ frame mới từ Redis...")
                    continue

                for _, entries in response:
                    logger.info(f"Nhận được batch {len(entries)} tin nhắn. Đang lọc frame mới nhất...")
                    # 1. Xác định tin nhắn cuối cùng (mới nhất) trong batch
                    last_entry_id, last_fields = entries[-1]
                    
                    # 2. Xử lý logic "Skip-to-Latest"
                    # Chúng ta sẽ ACK tất cả các tin nhắn trong batch này để giải phóng Redis
                    for entry_id, fields in entries:
                        is_last = (entry_id == last_entry_id)
                        
                        try:
                            # Chỉ thực hiện inference (YOLO) trên TIN NHẮN CUỐI CÙNG
                            if not is_last:
                                self.client.xack(self.preprocess_stream, self.group_name, entry_id)
                                continue

                            # Bắt đầu xử lý cho tin nhắn mới nhất
                            payload = json.loads(fields["payload"])
                            
                            if payload.get("has_motion") is False:
                                logger.debug(f"Bỏ qua frame {payload.get('frame_id')} vì không có chuyển động.")
                                self.client.xack(self.preprocess_stream, self.group_name, entry_id)
                                continue
                                
                            frame_ref = payload.get("frame_ref")
                            frame = load_frame(frame_ref)
                            
                            cam_id = payload.get("camera_id")
                            if cam_id not in self.detectors_dict:
                                self.detectors_dict[cam_id] = PersonDetector(weights_path=self.yolo_path)
                                
                            t1 = time.time()
                            boxes_results = self.detectors_dict[cam_id].predict(frame)
                            t2 = time.time()
                            
                            latency_ms = (t2 - t1) * 1000.0
                            fps_inference = 1000.0 / latency_ms if latency_ms > 0 else 0.0
                            
                            metadata = {
                                "camera_id": cam_id,
                                "timestamp": time.time(),
                                "frame_id": payload.get("frame_id"),
                                "capture_timestamp": payload.get("capture_timestamp"),
                                "publish_timestamp": payload.get("publish_timestamp"),
                                "frame_info": {
                                    "width": payload.get("frame_size", [0, 0])[0],
                                    "height": payload.get("frame_size", [0, 0])[1]
                                },
                                "detections": {
                                    "yolo11_default": boxes_results
                                },
                                "metadata": {
                                    "total_count": len(boxes_results),
                                    "fps_inference": round(fps_inference, 2), 
                                    "latency_ms": round(latency_ms, 2)
                                }
                            }
                            
                            topic_name = f"camera:metadata:{cam_id}"
                            self.client.set(topic_name, json.dumps(metadata), ex=60)
                            self.client.xadd(self.detections_stream, {"payload": json.dumps(metadata)}, maxlen=1000)
                            self.client.xack(self.preprocess_stream, self.group_name, entry_id)
                            
                            logger.info(f"✅ Xử lý xong frame {payload.get('frame_id')} | Cam: {cam_id} | Detect: {len(boxes_results)} người | Latency: {latency_ms:.1f}ms")

                        except Exception as inner_e:
                            logger.error(f"Lỗi xử lý frame: {inner_e}")
                            self.client.xack(self.preprocess_stream, self.group_name, entry_id)

            except redis.ConnectionError:
                logger.error("Mất kết nối Redis! Đang thử lại sau 5 giây...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Lỗi hệ thống: {e}")
                time.sleep(1)
