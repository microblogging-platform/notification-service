import logging
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection


logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self, url: str) -> None:
        self._url = url
        self._connection: Optional[AbstractRobustConnection] = None

    @property
    def is_connected(self) -> bool:
        return bool(self._connection and not self._connection.is_closed)

    async def connect(self) -> None:
        if self.is_connected:
            return

        logger.info("Connecting to RabbitMQ...")
        self._connection = await aio_pika.connect_robust(
            self._url,
            client_properties={"connection_name": "notification-service"},
        )
        logger.info("Connected to RabbitMQ.")

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ connection closed.")

    async def get_channel(self) -> AbstractRobustChannel:
        if not self.is_connected:
            await self.connect()

        assert self._connection is not None
        return await self._connection.channel()