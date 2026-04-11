# services/ai_opencv/main_worker.py
import logging

from config.settings import Settings
from factories.runtime import create_decoder, create_frame_store, create_preprocessor, create_publisher
from metrics.health_monitor import HealthMonitor
from orchestration.pipeline import PreprocessPipeline


logger = logging.getLogger(__name__)


def main():
    settings = Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), format="%(asctime)s - %(levelname)s - %(message)s")

    decoder = create_decoder(settings)
    preprocessor = create_preprocessor(settings)
    frame_store = create_frame_store(settings)
    publisher = create_publisher(settings)
    health_monitor = HealthMonitor(
        camera_id=settings.camera_id,
        backend=settings.pipeline_backend,
        health_publish_interval_sec=settings.health_publish_interval_sec,
    )
    pipeline = PreprocessPipeline(
        decoder=decoder,
        preprocessor=preprocessor,
        frame_store=frame_store,
        publisher=publisher,
        settings=settings,
        health_monitor=health_monitor,
    )

    logger.info(
        "Preprocess pipeline running | camera=%s backend=%s source=%s target_fps=%s store=%s",
        settings.camera_id,
        settings.pipeline_backend,
        settings.input_source,
        settings.target_fps,
        settings.frame_store_dir,
    )

    try:
        pipeline.run()
    except KeyboardInterrupt:
        logger.info("Stopping preprocess pipeline.")
    except Exception as exc:
        logger.error("Fatal preprocess pipeline error: %s", exc)
        raise


if __name__ == "__main__":
    main()
