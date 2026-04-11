from collections.abc import Iterator
from typing import Protocol

from domain.frame_packet import FramePacket


class FrameDecoder(Protocol):
    def get_frames(self) -> Iterator[FramePacket]:
        """Yield normalized frame packets from a video source."""

    def get_stats_snapshot(self) -> dict[str, int | float | str]:
        """Return decoder-side health metrics for logging and health streams."""
