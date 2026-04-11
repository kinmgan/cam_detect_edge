from typing import Protocol


class ResultPublisher(Protocol):
    def publish_preprocess_event(self, event: dict) -> str | None:
        """Publish a preprocess event to the configured event bus."""

    def publish_health_event(self, event: dict) -> str | None:
        """Publish a health event to the configured event bus."""
