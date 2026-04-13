from __future__ import annotations

import redis

from events.preprocess_event import serialize_stream_entry


import os

class RedisStreamPublisher:
    def __init__(
        self,
        host: str,
        port: int,
        preprocess_stream: str,
        health_stream: str,
        stream_maxlen: int = 1000,
        enable_stream_publish: bool = True,
        enable_health_publish: bool = True,
    ):
        password = os.getenv("REDIS_PASSWORD", None)
        self.r = redis.Redis(host=host, port=port, password=password, decode_responses=True)
        self.preprocess_stream = preprocess_stream
        self.health_stream = health_stream
        self.stream_maxlen = stream_maxlen
        self.enable_stream_publish = enable_stream_publish
        self.enable_health_publish = enable_health_publish

    def publish_preprocess_event(self, event: dict) -> str | None:
        if not self.enable_stream_publish:
            return None
        return self.r.xadd(
            self.preprocess_stream,
            serialize_stream_entry(event),
            maxlen=self.stream_maxlen,
            approximate=True,
        )

    def publish_health_event(self, event: dict) -> str | None:
        if not self.enable_health_publish:
            return None
        return self.r.xadd(
            self.health_stream,
            serialize_stream_entry(event),
            maxlen=max(100, min(self.stream_maxlen, 1000)),
            approximate=True,
        )
