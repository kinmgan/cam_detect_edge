from dataclasses import dataclass, field
from typing import Any

from .frame_packet import FramePacket


@dataclass(slots=True)
class PreprocessResult:
    frame_packet: FramePacket
    motion_score: float
    has_motion: bool
    blur_score: float
    brightness: float
    contrast: float
    frame_ref: str | None = None
    backend: str = "cpu"
    pipeline_version: str = "v1"
    frame_store_latency_ms: float | None = None
    publish_latency_ms: float | None = None
    event_id: str | None = None
    mask_coverage: float | None = None
    hints: dict[str, Any] = field(default_factory=dict)
