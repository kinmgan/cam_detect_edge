# services/ai_opencv/main_worker.py
import os
import logging
from ingestion.stream_reader import StreamLoader
from ai_engine.wrapper import AIModelWrapper
from output_handler.redis_publisher import RedisPublisher
from command_listener import CommandListener

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 1. Cấu hình từ biến môi trường
    RTSP_URL  = os.getenv("RTSP_URL",  "rtsp://localhost:8554/cam1")
    CAMERA_ID = os.getenv("CAMERA_ID", "cam_001")
    TARGET_FPS = int(os.getenv("TARGET_FPS", 2))
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    # 2. Khởi tạo AI Engine
    ai_engine = AIModelWrapper(model_path="ai_engine/weights/yolo11n.pt")

    # 3. Command Listener (đổi model nóng từ Dashboard)
    cmd_listener = CommandListener(ai_engine, host=REDIS_HOST, port=REDIS_PORT)
    cmd_listener.start()
    logger.info("Command Listener đã sẵn sàng.")

    # 4. Stream & Output
    stream_loader = StreamLoader(rtsp_url=RTSP_URL, target_fps=TARGET_FPS)
    publisher     = RedisPublisher(host=REDIS_HOST, port=REDIS_PORT)

    logger.info(f"Hệ thống vận hành: {CAMERA_ID} | Target: {TARGET_FPS} FPS")

    try:
        for frame in stream_loader.get_frames():  # retry vô hạn khi stream đứt
            detections = ai_engine.predict(frame)
            publisher.publish_metadata(camera_id=CAMERA_ID, detections=detections)

            if detections:
                logger.info(f"[{CAMERA_ID}] Phát hiện {len(detections)} đối tượng.")

    except KeyboardInterrupt:
        logger.info("Dừng hệ thống.")
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng: {e}")

if __name__ == "__main__":
    main()