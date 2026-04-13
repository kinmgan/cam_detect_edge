import os
import numpy as np

def load_frame(frame_ref: str) -> np.ndarray:
    # Xử lý đường dẫn tương đối do 2 service chạy ở 2 thư mục khác nhau
    # frame_ref thường có dạng: data/frame_store/xxx.npy
    # Cần trỏ về thư mục: ../ai_opencv/data/frame_store/xxx.npy
    
    # Nếu đường dẫn không tuyệt đối, hãy lùi lại một cấp thư mục
    if not os.path.isabs(frame_ref):
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ai_opencv")
        real_path = os.path.normpath(os.path.join(base_dir, frame_ref))
    else:
        real_path = frame_ref

    if not os.path.exists(real_path):
        raise FileNotFoundError(f"Không tìm thấy file ảnh: {real_path}")
    
    frame = np.load(real_path)
    return frame
