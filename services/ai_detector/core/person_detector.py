import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class PersonDetector:
    def __init__(self, weights_path="yolov11n.pt"):
        """
        Khởi tạo Model YOLO. Nếu weights_path rỗng hoặc dùng tên model rỗng, ultralytics sẽ tự động tải pre-train.
        """
        logger.info(f"Đang tải Model YOLO từ: {weights_path}")
        self.model = YOLO(weights_path)
    
    def predict(self, frame_array):
        """
        Nhận diện và tracking người trên ảnh.
        :param frame_array: mảng ảnh Numpy BGR
        :return: Danh sách các bounding box [{object_id, label, bbox, score}, ...]
        """
        # Sử dụng hàm track() của ultralytics để vừa lấy tọa độ vừa lấy ID
        # Thiết lập chạy mặc định với bytetrack để tối ưu tốc độ và tránh ngốn CPU
        # Chỉ focus class 0 là 'person'
        results = self.model.track(frame_array, persist=True, classes=[0], verbose=False, tracker="bytetrack.yaml")
        
        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                # Trích xuất tọa độ [x1, y1, x2, y2]
                xyxy = box.xyxy[0].tolist()
                score = float(box.conf[0])
                
                # Tracking ID, nếu chưa có thì gán mặc định là None hoặc -1
                obj_id = -1
                if box.id is not None:
                    obj_id = int(box.id[0])
                
                detections.append({
                    "object_id": obj_id,
                    "label": "person",
                    "bbox": xyxy,
                    "score": round(score, 2)
                })
                
        return detections
