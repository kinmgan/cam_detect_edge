from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from domain.frame_packet import FramePacket
from domain.frame_store_record import FrameStoreRecord


class NpyFrameStore:
    def __init__(self, store_dir: str, ttl_sec: int = 30):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_sec = ttl_sec
        self._last_cleanup_at = 0.0

    def put(self, frame_packet: FramePacket) -> FrameStoreRecord:
        started = time.perf_counter()
        filename = (
            f"{frame_packet.camera_id}_"
            f"{frame_packet.frame_id}_"
            f"{int(frame_packet.capture_timestamp * 1000)}.npy"
        )
        final_path = self.store_dir / filename
        np.save(final_path, frame_packet.frame, allow_pickle=False)

        write_latency_ms = (time.perf_counter() - started) * 1000.0
        created_timestamp = time.time()
        expires_timestamp = created_timestamp + self.ttl_sec
        self._maybe_cleanup(created_timestamp)

        return FrameStoreRecord(
            frame_ref=str(final_path),
            created_timestamp=created_timestamp,
            expires_timestamp=expires_timestamp,
            write_latency_ms=write_latency_ms,
        )

    def load(self, frame_ref: str) -> np.ndarray:
        return np.load(frame_ref, mmap_mode="r", allow_pickle=False)

    def cleanup_expired(self) -> int:
        cutoff = time.time() - self.ttl_sec
        removed = 0
        for path in self.store_dir.glob("*.npy"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
                    removed += 1
            except FileNotFoundError:
                continue
        return removed

    def _maybe_cleanup(self, now: float) -> None:
        if now - self._last_cleanup_at >= max(self.ttl_sec / 2, 1):
            self.cleanup_expired()
            self._last_cleanup_at = now
