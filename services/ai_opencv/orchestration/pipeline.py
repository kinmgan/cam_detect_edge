import logging
import time

from events.preprocess_event import build_health_event, build_preprocess_event


logger = logging.getLogger(__name__)


class PreprocessPipeline:
    def __init__(self, decoder, preprocessor, frame_store, publisher, settings, health_monitor):
        self.decoder = decoder
        self.preprocessor = preprocessor
        self.frame_store = frame_store
        self.publisher = publisher
        self.settings = settings
        self.health_monitor = health_monitor

    def run(self):
        for frame_packet in self.decoder.get_frames():
            result = self.preprocessor.process(frame_packet)
            result.backend = self.settings.pipeline_backend
            result.pipeline_version = self.settings.pipeline_version

            store_record = self.frame_store.put(frame_packet)
            result.frame_ref = store_record.frame_ref
            result.frame_store_latency_ms = store_record.write_latency_ms

            event = build_preprocess_event(result)
            publish_started = time.perf_counter()
            event_id = self.publisher.publish_preprocess_event(event)
            publish_latency_ms = (time.perf_counter() - publish_started) * 1000.0
            result.publish_latency_ms = publish_latency_ms
            result.event_id = event_id

            self.health_monitor.record_frame(
                store_latency_ms=store_record.write_latency_ms,
                publish_latency_ms=publish_latency_ms,
                decoder_stats=self.decoder.get_stats_snapshot(),
                event_id=event_id,
            )

            now = time.time()
            if self.health_monitor.should_publish_health(now):
                self.publisher.publish_health_event(
                    build_health_event(
                        camera_id=result.frame_packet.camera_id,
                        backend=result.backend,
                        pipeline_version=result.pipeline_version,
                        snapshot=self.health_monitor.build_snapshot(),
                    )
                )
                self.health_monitor.mark_health_published(now)

            logger.debug(
                "Published preprocess event | camera=%s frame=%s motion=%.4f frame_ref=%s",
                result.frame_packet.camera_id,
                result.frame_packet.frame_id,
                result.motion_score,
                result.frame_ref,
            )
