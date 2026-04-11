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

from config.settings import Settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def ensure_group(client, stream_name: str, group_name: str):
    try:
        client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def main():
    settings = Settings.from_env()
    stream_name = settings.tracks_stream
    group_name = os.getenv("STREAM_GROUP", "metadata_bridge")
    consumer_name = os.getenv("CONSUMER_NAME", "metadata_bridge_consumer")

    client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    ensure_group(client, stream_name, group_name)

    logger.info("Metadata bridge consuming stream=%s", stream_name)
    while True:
        response = client.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=1, block=5000)
        if not response:
            continue

        for _, entries in response:
            for entry_id, fields in entries:
                payload = json.loads(fields["payload"])
                metadata_key = f"{settings.metadata_key_prefix}:{payload['camera_id']}"
                metadata = {
                    "camera_id": payload["camera_id"],
                    "capture_timestamp": payload.get("capture_timestamp"),
                    "publish_timestamp": time.time(),
                    "detections": {
                        "yolo11_default": payload.get("tracks", []),
                    },
                    "tracks": payload.get("tracks", []),
                }
                client.set(metadata_key, json.dumps(metadata))
                client.xack(stream_name, group_name, entry_id)


if __name__ == "__main__":
    main()
