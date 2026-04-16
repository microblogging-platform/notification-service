import logging

import aio_pika
import orjson
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustChannel
from pydantic import ValidationError
from tenacity import RetryError

from application.usecases.send_reset_password_email import SendResetPasswordEmailUseCase
from infrastructure.rabbitmq.client import RabbitMQClient
from infrastructure.rabbitmq.models import IncomingEvent

logger = logging.getLogger(__name__)


class PasswordResetConsumer:

    DLX_NAME = "dlx"
    DLQ_ROUTING_KEY = "dead_letters"

    def __init__(
        self,
        client: RabbitMQClient,
        use_case: SendResetPasswordEmailUseCase,
        queue_name: str = "reset-password-stream",
        dlq_name: str = "reset-password-dlq",
        prefetch_count: int = 10,
    ) -> None:
        self._client = client
        self._use_case = use_case
        self._queue_name = queue_name
        self._dlq_name = dlq_name
        self._prefetch_count = prefetch_count

    async def start(self) -> None:
        channel: AbstractRobustChannel = await self._client.get_channel()
        await channel.set_qos(prefetch_count=self._prefetch_count)

        dlx = await channel.declare_exchange(
            self.DLX_NAME,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )
        dlq = await channel.declare_queue(self._dlq_name, durable=True)
        await dlq.bind(dlx, routing_key=self.DLQ_ROUTING_KEY)

        queue = await channel.declare_queue(
            self._queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.DLX_NAME,
                "x-dead-letter-routing-key": self.DLQ_ROUTING_KEY,
            },
        )

        await queue.consume(self._process_message)
        logger.info(
            "PasswordResetConsumer started. Queue=%s, DLQ=%s",
            self._queue_name,
            self._dlq_name,
        )

    async def _process_message(self, message: AbstractIncomingMessage) -> None:
        try:
            raw = orjson.loads(message.body)
        except orjson.JSONDecodeError:
            logger.exception("Invalid JSON; sending to DLQ.")
            await message.reject(requeue=False)
            return

        try:
            event = IncomingEvent(**raw)
        except ValidationError:
            logger.exception("Payload validation failed; sending to DLQ.")
            await message.reject(requeue=False)
            return

        try:
            await self._use_case.execute(event)
            await message.ack()
            logger.info("Message processed successfully.")
        except RetryError as exc:
            logger.exception(
                "Use case failed after all retry attempts; sending to DLQ. "
                "Last error: %s",
                exc.last_attempt.exception(),
            )
            await message.reject(requeue=False)
