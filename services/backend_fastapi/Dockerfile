# Sử dụng Python 3.11 bản slim cho nhẹ
FROM python:3.11-slim

WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (nếu có)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Mở cổng 8000 cho FastAPI
EXPOSE 8000

# Chạy server Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]