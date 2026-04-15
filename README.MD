# Cam Detect Edge - Runbook


### 1) Docker (FE/BE/Redis/Postgres/MediaMTX)

```bash
docker compose up -d --build
```

Nếu bị dính cache (CSS/JS cũ):

```bash
docker compose build --no-cache frontend backend
docker compose up -d
```

### 2) Bơm luồng RTSP vào `cam1` (host)

```bash
ffmpeg -re -stream_loop -1 -i "C:\Users\ngant\test\video_test_1.mp4" -c:v libx264 -preset ultrafast -tune zerolatency -profile:v baseline -level 3.0 -bf 0 -an -rtsp_transport tcp -f rtsp rtsp://localhost:8554/cam1
```
thay bằng đường dẫn của bạn

### 3) Chạy tay `ai_opencv` (host)

```bash
cd services/ai_opencv
pip install -r requirements.txt
```

**Cấu hình (chọn 1):**

- **A. Dùng file `.env`**: tạo `services/ai_opencv/.env` (hoặc đảm bảo `.env` đang được load đúng thư mục).
- **B. Override nhanh bằng biến môi trường** (PowerShell) như bên dưới.

```powershell
$env:RTSP_URL="rtsp://127.0.0.1:8554/cam1"
$env:REDIS_HOST="127.0.0.1"
$env:REDIS_PORT="6379"
$env:CAMERA_ID="cam1"
$env:TARGET_FPS="2"
python main_worker.py
```

### 4) Chạy tay `ai_detector` (host)

```bash
cd services/ai_detector
pip install -r requirements.txt
```

**Cấu hình (chọn 1):**

- **A. Dùng file `.env`**: tạo `services/ai_detector/.env` (được `load_dotenv()` tự load khi chạy `python main.py`).
- **B. Override nhanh bằng biến môi trường** (PowerShell) như bên dưới.

```powershell
$env:REDIS_HOST="127.0.0.1"
$env:REDIS_PORT="6379"
$env:YOLO_WEIGHTS="models/person_detector/weights/yolo11s.pt"
python main.py
```

### 5) Mở dashboard

- `http://localhost:3000`

---

