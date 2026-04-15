# services/backend_fastapi/src/redis_worker.py
import redis.asyncio as redis 
import json
import asyncio
import os

class RedisWorker:
    def __init__(self):
        host = os.getenv("REDIS_HOST", "127.0.0.1")
        port = int(os.getenv("REDIS_PORT", 6379))
        password = os.getenv("REDIS_PASSWORD", None)
        # Khởi tạo async client
        self.r = redis.Redis(host=host, port=port, password=password, decode_responses=True)

    async def listen_metadata(self, callback):
        """
        Lắng nghe metadata từ Redis qua luồng Stream (Async hoàn toàn)
        """
        stream_name = os.getenv("DETECTIONS_STREAM", "camera:detections_stream")
        last_id = "$" 
        
        print(f"[*] RedisWorker started listening on stream: {stream_name}")

        while True:
            try:
                # Sử dụng await xread để không chặn Event Loop
                # Đọc batch lớn hơn để "hút" nhanh các tin nhắn cũ nếu có
                response = await self.r.xread({stream_name: last_id}, count=50, block=1000)
                
                if response:
                    for _, entries in response:
                        # Chỉ lấy entry LUÔN LÀ CUỐI CÙNG của batch này để giảm độ trễ (Latency suppression)
                        last_entry_id = None
                        last_fields = None
                        
                        for entry_id, fields in entries:
                            last_entry_id = entry_id
                            last_fields = fields
                        
                        if last_fields and "payload" in last_fields:
                            try:
                                metadata = json.loads(last_fields["payload"])
                                # Chỉ gửi cái mới nhất trong batch này
                                await callback(metadata)
                            except Exception as json_err:
                                print(f"Lỗi parse JSON payload: {json_err}")
                            
                        last_id = last_entry_id 
                else:
                    # Nhường nhịp
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                print(f"Lỗi đọc Redis Stream (Async): {e}")
                await asyncio.sleep(2)