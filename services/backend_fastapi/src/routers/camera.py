from fastapi import APIRouter, HTTPException
import redis
import json
import os

router = APIRouter(prefix="/api/camera", tags=["Camera Control"])

# Kết nối Redis từ biến môi trường
R_HOST = os.getenv("REDIS_HOST", "redis")
R_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=R_HOST, port=R_PORT, decode_responses=True)

@router.post("/control")
async def control_camera(command: dict):
    """
    Endpoint nhận lệnh từ FE và publish vào Redis Pub/Sub.
    Payload mẫu: {"action": "switch_model", "model_name": "yolo11s"}
    """
    try:
        r.publish("ai_commands", json.dumps(command))
        return {"status": "success", "message": f"Command {command['action']} sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))