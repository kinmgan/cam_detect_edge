# services/backend_fastapi/src/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .redis_worker import RedisWorker
import asyncio
import json
import os
from dotenv import load_dotenv
from .routers import camera

load_dotenv()

app = FastAPI(title="Camera AI Backend")

# Cho phép Dashboard truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(camera.router)
# Quản lý các kết nối WebSocket đang hoạt động
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()
redis_worker = RedisWorker()

@app.on_event("startup")
async def startup_event():
    # Chạy loop lắng nghe Redis ngay khi backend khởi động
    asyncio.create_task(redis_worker.listen_metadata(manager.broadcast))

@app.get("/")
def read_root():
    return {"status": "Backend is running", "target": "RTX 4070 Edge Server"}

@app.websocket("/ws/metadata")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Giữ kết nối mở
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)