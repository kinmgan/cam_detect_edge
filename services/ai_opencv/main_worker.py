# services/ai_opencv/main_worker.py
import os
import logging
from ingestion.stream_reader import StreamLoader
from ai_engine.wrapper import AIModelWrapper
from output_handler.redis_publisher import RedisPublisher
from command_listener import CommandListener

# Cấu hình Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 1. Khởi tạo cấu hình từ biến môi trường
    RTSP_URL = os.getenv("RTSP_URL", "rtsp://localhost:8554/cam1")
    CAMERA_ID = os.getenv("CAMERA_ID", "cam_001")
    TARGET_FPS = int(os.getenv("TARGET_FPS", 2))
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    # 2. Khởi tạo AI Engine
    ai_engine = AIModelWrapper(model_path="ai_engine/weights/yolo11n.pt")

    # 3. Kích hoạt Command Listener để FE có thể đổi model "nóng"
    # CommandListener kế thừa threading.Thread, gọi .start() trực tiếp là đủ
    cmd_listener = CommandListener(ai_engine, host=REDIS_HOST, port=REDIS_PORT)
    cmd_listener.start()
    logger.info("Command Listener đã sẵn sàng nhận lệnh đổi model từ Dashboard.")

    # 4. Khởi tạo Stream & Output
    stream_loader = StreamLoader(rtsp_url=RTSP_URL, target_fps=TARGET_FPS)
    publisher = RedisPublisher(host=REDIS_HOST, port=REDIS_PORT)

    logger.info(f"Hệ thống vận hành: {CAMERA_ID} | Target: {TARGET_FPS} FPS")

    try:
        # Loop xử lý chính
        for frame in stream_loader.get_frames():
            # Bước A: Inference - Chạy AI nhận diện
            detections = ai_engine.predict(frame)

            # Bước B: Đẩy Metadata chuẩn JSON lên Redis
            publisher.publish_metadata(
                camera_id=CAMERA_ID,
                detections=detections
            )

            # Log kết quả để theo dõi hiệu năng
            if len(detections) > 0:
                logger.info(f"[{CAMERA_ID}] Phát hiện {len(detections)} đối tượng.")

    except KeyboardInterrupt:
        logger.info("Đang dừng hệ thống theo yêu cầu người dùng...")
    except Exception as e:
        logger.error(f"Lỗi hệ thống nghiêm trọng: {e}")

if __name__ == "__main__":
    main()