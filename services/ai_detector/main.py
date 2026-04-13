import logging
from dotenv import load_dotenv
from orchestration.consumer import StreamConsumer

def main():
    # Load environment variables từ file .env
    load_dotenv()
    
    # Thiết lập cơ bản cho log hệ thống
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("AI_Detector_Main")
    
    logger.info("Đang khởi động AI Detector Service...")
    
    # Khởi tạo tiến trình vòng lặp Model
    app = StreamConsumer()
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Đã nhận lệnh thoát (Ctrl+C). Đang tắt dịch vụ...")

if __name__ == "__main__":
    main()
