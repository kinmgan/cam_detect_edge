# services/backend_fastapi/src/redis_worker.py
import redis
import json
import asyncio
import os

class RedisWorker:
    def __init__(self):
        host = os.getenv("REDIS_HOST", "redis_broker")
        port = int(os.getenv("REDIS_PORT", 6379))
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        self.channel = "camera_metadata_stream"

    async def listen_metadata(self, callback):
        """
        Lắng nghe metadata từ Redis và thực hiện callback (gửi tới WebSocket)
        """
        while True:
            # Ở bản đơn giản này chúng ta scan các key metadata của camera
            # Trong thực tế với 25 cam, nên dùng Redis Pub/Sub để tối ưu
            keys = self.r.keys("camera:metadata:*")
            for key in keys:
                data = self.r.get(key)
                if data:
                    metadata = json.loads(data)
                    await callback(metadata)
            
            await asyncio.sleep(0.1) # Tương đương ~10Hz, đủ cho AI 2 FPS