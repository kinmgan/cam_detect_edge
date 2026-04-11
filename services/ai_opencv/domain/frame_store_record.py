from dataclasses import dataclass


@dataclass(slots=True)
class FrameStoreRecord:
    frame_ref: str
    created_timestamp: float
    expires_timestamp: float
    write_latency_ms: float
