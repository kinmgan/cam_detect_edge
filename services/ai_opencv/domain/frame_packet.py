from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FramePacket:
    camera_id: str
    frame_id: int
    frame: Any
    capture_timestamp: float
    source_uri: str | None = None
    source_fps: float | None = None
    width: int | None = None
    height: int | None = None
    color_format: str = "bgr"
    frame_dtype: str = "uint8"
    extra: dict[str, Any] = field(default_factory=dict)
