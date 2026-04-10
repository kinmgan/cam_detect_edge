# Sử dụng base image DeepStream của NVIDIA
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

WORKDIR /app

# Copy requirement và cài đặt thư viện Python (như redis)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy toàn bộ code AI vào container
COPY . /app

# Lệnh chạy pipeline khi start container
CMD ["python3", "src/main_pipeline.py"]