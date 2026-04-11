from __future__ import annotations

from preprocess.frame_preprocessor import FrameQualityPreprocessor


class GPUFramePreprocessor:
    def __init__(self, motion_threshold: float = 0.5):
        try:
            import cvcuda  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "GPU preprocess requires CV-CUDA. Install cvcuda inside the GPU image or switch to PIPELINE_BACKEND=cpu."
            ) from exc

        self.cpu_fallback = FrameQualityPreprocessor(motion_threshold=motion_threshold)

    def process(self, frame_packet):
        result = self.cpu_fallback.process(frame_packet)
        result.hints["gpu_preprocess"] = "runtime_ready_cpu_metric_fallback"
        return result
