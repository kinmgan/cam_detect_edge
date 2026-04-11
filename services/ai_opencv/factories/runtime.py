from __future__ import annotations

from adapters.decoder.opencv_decoder import OpenCVFrameDecoder
from adapters.decoder.pynv_decoder import PyNvVideoCodecDecoder
from adapters.frame_store.npy_frame_store import NpyFrameStore
from adapters.publisher.redis_stream_publisher import RedisStreamPublisher
from config.settings import Settings
from preprocess.frame_preprocessor import FrameQualityPreprocessor
from preprocess.gpu_frame_preprocessor import GPUFramePreprocessor


def create_decoder(settings: Settings):
    if settings.pipeline_backend == "gpu":
        return PyNvVideoCodecDecoder(
            camera_id=settings.camera_id,
            source_uri=settings.input_source,
            target_fps=settings.target_fps,
            gpu_id=settings.gpu_id,
            buffer_size=settings.gpu_decoder_buffer_size,
        )

    return OpenCVFrameDecoder(
        camera_id=settings.camera_id,
        rtsp_url=settings.input_source,
        target_fps=settings.target_fps,
        retry_interval=settings.retry_interval,
    )


def create_preprocessor(settings: Settings):
    if settings.pipeline_backend == "gpu":
        return GPUFramePreprocessor(motion_threshold=settings.motion_threshold)
    return FrameQualityPreprocessor(motion_threshold=settings.motion_threshold)


def create_frame_store(settings: Settings):
    return NpyFrameStore(store_dir=settings.frame_store_dir, ttl_sec=settings.frame_ttl_sec)


def create_publisher(settings: Settings):
    return RedisStreamPublisher(
        host=settings.redis_host,
        port=settings.redis_port,
        preprocess_stream=settings.preprocess_stream,
        health_stream=settings.health_stream,
        stream_maxlen=settings.stream_maxlen,
        enable_stream_publish=settings.enable_stream_publish,
        enable_health_publish=settings.enable_health_publish,
    )
