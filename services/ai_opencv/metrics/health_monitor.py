from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class HealthMonitor:
    camera_id: str
    backend: str
    health_publish_interval_sec: int = 10
    started_at: float = field(default_factory=time.time)
    last_health_publish_at: float = field(default_factory=lambda: 0.0)
    ingested_frames: int = 0
    published_frames: int = 0
    total_store_latency_ms: float = 0.0
    total_publish_latency_ms: float = 0.0
    last_decoder_stats: dict[str, Any] = field(default_factory=dict)
    last_event_id: str | None = None

    def record_frame(
        self,
        *,
        store_latency_ms: float,
        publish_latency_ms: float,
        decoder_stats: dict[str, Any],
        event_id: str | None,
    ) -> None:
        self.ingested_frames += 1
        self.published_frames += 1
        self.total_store_latency_ms += store_latency_ms
        self.total_publish_latency_ms += publish_latency_ms
        self.last_decoder_stats = decoder_stats
        self.last_event_id = event_id

    def should_publish_health(self, now: float) -> bool:
        return now - self.last_health_publish_at >= self.health_publish_interval_sec

    def mark_health_published(self, now: float) -> None:
        self.last_health_publish_at = now

    def build_snapshot(self) -> dict[str, Any]:
        uptime_sec = max(time.time() - self.started_at, 1e-6)
        return {
            "camera_id": self.camera_id,
            "backend": self.backend,
            "uptime_sec": round(uptime_sec, 3),
            "ingest_fps": round(self.ingested_frames / uptime_sec, 3),
            "published_fps": round(self.published_frames / uptime_sec, 3),
            "published_frames": self.published_frames,
            "avg_frame_store_latency_ms": round(self.total_store_latency_ms / max(self.published_frames, 1), 3),
            "avg_publish_latency_ms": round(self.total_publish_latency_ms / max(self.published_frames, 1), 3),
            "decoder_stats": self.last_decoder_stats,
            "last_event_id": self.last_event_id,
        }
