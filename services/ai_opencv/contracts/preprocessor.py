from typing import Protocol

from domain.frame_packet import FramePacket
from domain.preprocess_result import PreprocessResult


class FramePreprocessor(Protocol):
    def process(self, frame_packet: FramePacket) -> PreprocessResult:
        """Return frame quality and motion metadata for downstream services."""
