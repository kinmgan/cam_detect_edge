from ingestion.stream_reader import StreamLoader


class OpenCVFrameDecoder:
    def __init__(self, camera_id: str, rtsp_url: str, target_fps: int = 2, retry_interval: int = 5):
        self.stream_loader = StreamLoader(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            target_fps=target_fps,
            retry_interval=retry_interval,
        )

    def get_frames(self):
        yield from self.stream_loader.get_frames()

    def get_stats_snapshot(self):
        return self.stream_loader.get_stats_snapshot()
