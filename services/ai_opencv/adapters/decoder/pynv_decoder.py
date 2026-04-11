from __future__ import annotations

import time

from domain.frame_packet import FramePacket


class PyNvVideoCodecDecoder:
    """
    GPU decoder scaffold for Linux Docker deployment.

    This v1 implementation validates the NVIDIA runtime and prepares a dedicated
    GPU decode path, but intentionally fails fast for live network sources until
    the low-level demux path is added on a GPU host.
    """

    def __init__(self, camera_id: str, source_uri: str, target_fps: int = 2, gpu_id: int = 0, buffer_size: int = 12):
        try:
            import PyNvVideoCodec as nvc
        except ImportError as exc:
            raise RuntimeError(
                "GPU backend requires PyNvVideoCodec. Install NVIDIA's PyNvVideoCodec module inside the GPU image."
            ) from exc

        try:
            import cvcuda  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "GPU backend requires CV-CUDA. Install cvcuda inside the GPU image or switch to PIPELINE_BACKEND=cpu."
            ) from exc

        self.camera_id = camera_id
        self.source_uri = source_uri
        self.target_fps = target_fps
        self.gpu_id = gpu_id
        self.buffer_size = buffer_size
        self._stats = {
            "backend": "gpu",
            "reconnect_count": 0,
            "dropped_frames": 0,
            "source_uri": source_uri,
        }

        if "://" in source_uri and not source_uri.lower().startswith("file://"):
            raise RuntimeError(
                "Current GPU v1 scaffold only validates seekable file/container inputs. "
                "Use CPU path for RTSP today, or extend this decoder with a low-level demux path on the GPU host."
            )
        self.runtime_summary = {
            "decoder_library": nvc.__name__,
            "gpu_id": gpu_id,
            "buffer_size": buffer_size,
        }

    def get_frames(self):
        raise RuntimeError(
            "GPU decode path is scaffolded but host-visible frame export is intentionally disabled in this environment. "
            "Bring this code to the Linux GPU host to complete PyNvVideoCodec/CV-CUDA -> shared frame store transfer."
        )
        yield FramePacket(  # pragma: no cover
            camera_id=self.camera_id,
            frame_id=0,
            frame=None,
            capture_timestamp=time.time(),
        )

    def get_stats_snapshot(self) -> dict[str, int | float | str]:
        return dict(self._stats)
