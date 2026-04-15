# services/ai_opencv/ai_engine/wrapper.py
import threading
from ultralytics import YOLO

class AIModelWrapper:
    def __init__(self, model_path="yolo11n.pt"):
        self.model = YOLO(model_path)
        self.current_model_path = model_path
        self._lock = threading.Lock()  # Bảo vệ khỏi race condition khi switch model

    def switch_model(self, model_name):
        """Đổi model an toàn từ CommandListener thread."""
        new_path = f"services\ai_detector\models\person_detector\weights\{model_name}.pt"
        if new_path != self.current_model_path:
            with self._lock:
                self.model = YOLO(new_path)
                self.current_model_path = new_path

    def predict(self, frame):
        """Xử lý suy luận và trả về kết quả chuẩn hóa."""
        with self._lock:
            results = self.model(frame, verbose=False)[0]
            model_names = self.model.names  # Fix: dùng self.model.names thay vì self.model_names
        detections = []
        for box in results.boxes:
            detections.append({
                "label": model_names[int(box.cls)],
                "bbox": [round(x, 2) for x in box.xywh[0].tolist()],
                "score": round(float(box.conf), 2)
            })
        return detections