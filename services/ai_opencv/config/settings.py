from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path.cwd() / ".env")


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    pipeline_backend: str = "cpu"
    pipeline_version: str = "v1"
    input_source: str = "rtsp://127.0.0.1:8554/cam1"
    camera_id: str = "cam1"
    target_fps: int = 2
    retry_interval: int = 5
    motion_threshold: float = 0.5
    frame_store_dir: str = "./data/frame_store"
    frame_ttl_sec: int = 30
    redis_host: str = "localhost"
    redis_port: int = 6379
    enable_stream_publish: bool = True
    enable_health_publish: bool = True
    preprocess_stream: str = "camera:preprocess_stream"
    detections_stream: str = "camera:detections_stream"
    tracks_stream: str = "camera:tracks_stream"
    health_stream: str = "camera:health_stream"
    stream_maxlen: int = 1000
    health_publish_interval_sec: int = 10
    log_level: str = "INFO"
    gpu_id: int = 0
    gpu_decoder_buffer_size: int = 12
    source_kind: str = "auto"
    metadata_key_prefix: str = "camera:metadata"

    @classmethod
    def from_env(cls) -> "Settings":
        input_source = os.getenv("INPUT_SOURCE") or os.getenv("RTSP_URL") or "rtsp://127.0.0.1:8554/cam1"
        frame_store_dir = os.getenv("FRAME_STORE_DIR")
        if not frame_store_dir:
            frame_store_dir = str((Path.cwd() / "data" / "frame_store").resolve())

        return cls(
            pipeline_backend=os.getenv("PIPELINE_BACKEND", "cpu").strip().lower(),
            pipeline_version=os.getenv("PIPELINE_VERSION", "v1"),
            input_source=input_source,
            camera_id=os.getenv("CAMERA_ID", "cam1"),
            target_fps=int(os.getenv("TARGET_FPS", 2)),
            retry_interval=int(os.getenv("RETRY_INTERVAL", 5)),
            motion_threshold=float(os.getenv("MOTION_THRESHOLD", 0.5)),
            frame_store_dir=frame_store_dir,
            frame_ttl_sec=int(os.getenv("FRAME_TTL_SEC", 30)),
            redis_host=os.getenv("REDIS_HOST", "127.0.0.1"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            enable_stream_publish=_as_bool(os.getenv("ENABLE_STREAM_PUBLISH"), True),
            enable_health_publish=_as_bool(os.getenv("ENABLE_HEALTH_PUBLISH"), True),
            preprocess_stream=os.getenv("PREPROCESS_STREAM", "camera:preprocess_stream"),
            detections_stream=os.getenv("DETECTIONS_STREAM", "camera:detections_stream"),
            tracks_stream=os.getenv("TRACKS_STREAM", "camera:tracks_stream"),
            health_stream=os.getenv("HEALTH_STREAM", "camera:health_stream"),
            stream_maxlen=int(os.getenv("STREAM_MAXLEN", 1000)),
            health_publish_interval_sec=int(os.getenv("HEALTH_PUBLISH_INTERVAL_SEC", 10)),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            gpu_id=int(os.getenv("GPU_ID", 0)),
            gpu_decoder_buffer_size=int(os.getenv("GPU_DECODER_BUFFER_SIZE", 12)),
            source_kind=os.getenv("SOURCE_KIND", "auto").strip().lower(),
            metadata_key_prefix=os.getenv("METADATA_KEY_PREFIX", "camera:metadata"),
        )
