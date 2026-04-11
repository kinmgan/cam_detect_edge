from typing import Protocol

import numpy as np

from domain.frame_packet import FramePacket
from domain.frame_store_record import FrameStoreRecord


class FrameStore(Protocol):
    def put(self, frame_packet: FramePacket) -> FrameStoreRecord:
        """Persist a frame and return a reference for downstream consumers."""

    def load(self, frame_ref: str) -> np.ndarray:
        """Load a frame from its reference."""

    def cleanup_expired(self) -> int:
        """Delete expired frames and return the number of removed entries."""
