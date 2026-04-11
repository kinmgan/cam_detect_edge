from __future__ import annotations

import json
import time
from typing import Any

from domain.preprocess_result import PreprocessResult


def build_preprocess_event(result: PreprocessResult) -> dict[str, Any]:
    return {
        "event_type": "preprocess_frame_ready",
        "camera_id": result.frame_packet.camera_id,
        "frame_id": result.frame_packet.frame_id,
        "capture_timestamp": result.frame_packet.capture_timestamp,
        "publish_timestamp": time.time(),
        "frame_ref": result.frame_ref,
        "frame_size": [result.frame_packet.width, result.frame_packet.height],
        "color_format": result.frame_packet.color_format,
        "frame_dtype": result.frame_packet.frame_dtype,
        "source_fps": result.frame_packet.source_fps,
        "motion_score": result.motion_score,
        "has_motion": result.has_motion,
        "blur_score": result.blur_score,
        "brightness": result.brightness,
        "contrast": result.contrast,
        "backend": result.backend,
        "pipeline_version": result.pipeline_version,
        "source_uri": result.frame_packet.source_uri,
        "hints": result.hints,
    }


def build_health_event(
    camera_id: str,
    backend: str,
    pipeline_version: str,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_type": "preprocess_health",
        "camera_id": camera_id,
        "backend": backend,
        "pipeline_version": pipeline_version,
        "publish_timestamp": time.time(),
        "metrics": snapshot,
    }


def serialize_stream_entry(event: dict[str, Any]) -> dict[str, str]:
    return {
        "event_type": str(event.get("event_type", "unknown")),
        "camera_id": str(event.get("camera_id", "unknown")),
        "payload": json.dumps(event),
    }


def deserialize_stream_payload(payload: str) -> dict[str, Any]:
    return json.loads(payload)
