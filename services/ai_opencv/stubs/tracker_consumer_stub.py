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
    stream_name = settings.detections_stream
    out_stream = settings.tracks_stream
    group_name = os.getenv("STREAM_GROUP", "tracker_stub")
    consumer_name = os.getenv("CONSUMER_NAME", "tracker_stub_consumer")

    client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    ensure_group(client, stream_name, group_name)

    logger.info("Tracker stub consuming stream=%s -> %s", stream_name, out_stream)
    while True:
        response = client.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=1, block=5000)
        if not response:
            continue

        for _, entries in response:
            for entry_id, fields in entries:
                payload = json.loads(fields["payload"])
                track_event = {
                    "event_type": "tracks_ready",
                    "camera_id": payload.get("camera_id"),
                    "frame_id": payload.get("frame_id"),
                    "capture_timestamp": payload.get("capture_timestamp"),
                    "publish_timestamp": time.time(),
                    "tracks": payload.get("detections", []),
                }
                client.xadd(out_stream, {"event_type": "tracks_ready", "camera_id": payload.get("camera_id", "unknown"), "payload": json.dumps(track_event)})
                client.xack(stream_name, group_name, entry_id)


if __name__ == "__main__":
    main()
