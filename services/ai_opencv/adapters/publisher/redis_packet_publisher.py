from output_handler.redis_publisher import RedisPublisher


class RedisPacketPublisher:
    def __init__(self, host: str = "redis", port: int = 6379, db: int = 0):
        self.publisher = RedisPublisher(host=host, port=port, db=db)

    def publish(self, result):
        self.publisher.publish_preprocess_result(result)
