import asyncio
import logging
import signal

from application.usecases.send_reset_password_email import SendResetPasswordEmailUseCase
from infrastructure.aws.ses_service import SesEmailSender
from infrastructure.config import settings
from infrastructure.mongo.database import MongoDatabase
from infrastructure.mongo.repository.notification_repository import MongoNotificationRepository
from infrastructure.rabbitmq.client import RabbitMQClient
from infrastructure.rabbitmq.consumers.password_reset_consumer import PasswordResetConsumer

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # --- Infrastructure ---
    mongo_db = MongoDatabase(uri=settings.mongo_uri, db_name=settings.mongo_db)
    repository = MongoNotificationRepository(db=mongo_db)

    email_sender = SesEmailSender(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        aws_region=settings.aws_region,
        sender=settings.aws_ses_sender,
    )

    rabbitmq_client = RabbitMQClient(url=settings.rabbitmq_url)
    await rabbitmq_client.connect()

    # --- Use cases ---
    use_case = SendResetPasswordEmailUseCase(
        repository=repository,
        email_sender=email_sender,
        db=mongo_db,
    )

    # --- Consumer ---
    consumer = PasswordResetConsumer(client=rabbitmq_client, use_case=use_case)
    await consumer.start()

    # --- Graceful Shutdown ---
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_signal() -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    logger.info("Notification service is running. Waiting for messages...")

    try:
        await stop_event.wait()
    finally:
        logger.info("Shutting down service...")
        await rabbitmq_client.close()
        mongo_db.close()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
