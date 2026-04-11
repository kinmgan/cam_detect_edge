import json
import logging
import os
import sys
import time
from pathlib import Path

import redis

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from adapters.frame_store.npy_frame_store import NpyFrameStore
from config.settings import Settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def ensure_group(client, stream_name: str, group_name: str):
    try:
        client.xgroup_create(stream_name, group_name, id="$", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def main():
    settings = Settings.from_env()
    stream_name = settings.preprocess_stream
    group_name = os.getenv("STREAM_GROUP", "model_stub")
    consumer_name = os.getenv("CONSUMER_NAME", "model_stub_consumer")

    client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    store = NpyFrameStore(settings.frame_store_dir, ttl_sec=settings.frame_ttl_sec)
    ensure_group(client, stream_name, group_name)

    logger.info("Model stub consuming stream=%s group=%s", stream_name, group_name)
    while True:
        response = client.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=1, block=5000)
        if not response:
            continue

        for _, entries in response:
            for entry_id, fields in entries:
                payload = json.loads(fields["payload"])
                try:
                    frame = store.load(payload["frame_ref"])
                    logger.info(
                        "Model stub received frame | camera=%s frame=%s shape=%s",
                        payload["camera_id"],
                        payload["frame_id"],
                        tuple(frame.shape),
                    )
                except FileNotFoundError:
                    logger.warning(
                        "Frame ref expired or missing | camera=%s frame=%s frame_ref=%s",
                        payload.get("camera_id"),
                        payload.get("frame_id"),
                        payload.get("frame_ref"),
                    )
                client.xack(stream_name, group_name, entry_id)
        time.sleep(0.01)


if __name__ == "__main__":
    main()
