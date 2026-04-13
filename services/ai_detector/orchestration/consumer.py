import json
import logging
import os
import time

import redis

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
        while True:
            # Rình nghe Redis. Block 5000 báo hiệu chờ 5 giây nếu mảng rỗng thì bốc lại
            response = self.client.xreadgroup(
                self.group_name, 
                self.consumer_name, 
                {self.preprocess_stream: ">"}, 
                count=1, 
                block=5000
            )
            
            if not response:
                continue

            for _, entries in response:
                for entry_id, fields in entries:
                    try:
                        payload = json.loads(fields["payload"])
                        
                        logger.info(f"Đã bắt được tín hiệu từ Redis: frame={payload.get('frame_id')} | has_motion={payload.get('has_motion')}")
                        
                        # 1. Tối ưu: Bỏ qua khi cảnh yên tĩnh không có gì chuyển động (has_motion = False)
                        if payload.get("has_motion") is False:
                            logger.info("-> Khung hình tĩnh, bỏ qua không chạy YOLO.")
                            continue
                            
                        # 2. Xách dữ liệu báo đi ra ngoài ổ cứng lấy ảnh gốc
                        frame_ref = payload.get("frame_ref")
                        frame = load_frame(frame_ref)
                        
                        # 3. Quăng vào Model tương ứng với Camera đó
                        cam_id = payload.get("camera_id")
                        if cam_id not in self.detectors_dict:
                            logger.info(f"Khởi tạo Tracker Model riêng biệt cho Camera: {cam_id}")
                            self.detectors_dict[cam_id] = PersonDetector(weights_path=self.yolo_path)
                            
                        # ---- BẮT ĐẦU ĐO GIỜ ----
                        t1 = time.time()
                        boxes_results = self.detectors_dict[cam_id].predict(frame)
                        t2 = time.time()
                        
                        # Tính toán tốc độ
                        latency_ms = (t2 - t1) * 1000.0
                        fps_inference = 1000.0 / latency_ms if latency_ms > 0 else 0.0
                        # -------------------------
                        
                        # 4. Gom Metadata kết quả trả về như Cấu trúc giao kèo
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
                                "yolo11_default": boxes_results,
                                "model_license_plate": [],
                                "model_behavior_check": []
                            },
                            "metadata": {
                                "total_count": len(boxes_results),
                                "fps_inference": round(fps_inference, 2), 
                                "latency_ms": round(latency_ms, 2),
                                "model_name": "YOLO_ByteTrack",
                                "model_version": "v1.0"
                            }
                        }
                        
                        # Ghi đè (SET) kết quả (Snapshot)
                        topic_name = f"camera:metadata:{cam_id}"
                        self.client.set(topic_name, json.dumps(metadata), ex=60) # Ép tự xóa sau 60s để dọn rác
                        
                        # Đẩy Log Event (XADD) vào lịch sử
                        self.client.xadd(self.detections_stream, {"payload": json.dumps(metadata)}, maxlen=1000)
                        
                        logger.info(f"Đã xử lý & báo cáo: cam_id={cam_id} | objects={len(boxes_results)} | speed={latency_ms:.1f}ms ({fps_inference:.1f} FPS)")
                        
                    except FileNotFoundError as e:
                        logger.warning(f"Bỏ qua Frame bị trễ quá thời gian bảo quản (xóa mât gốc): {e}")
                    except Exception as e:
                        logger.error(f"Lỗi không mong muốn trong khi chạy model: {e}")
                    finally:
                        # 5. LUÔN LUÔN báo ACK kết thúc nhiệm vụ đọc (Dù thành công hay lỗi)
                        self.client.xack(self.preprocess_stream, self.group_name, entry_id)
