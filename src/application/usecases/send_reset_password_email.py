import logging
from datetime import datetime, timezone

from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from application.usecases.base import UseCase
from domain.entities import ResetPasswordMessage
from domain.interfaces.repositories import INotificationRepository
from domain.interfaces.services.email_sender import IEmailSender
from infrastructure.mongo.database import MongoDatabase
from infrastructure.rabbitmq.models import IncomingEvent

logger = logging.getLogger(__name__)


class SendResetPasswordEmailUseCase(UseCase):

    def __init__(
        self,
        repository: INotificationRepository,
        email_sender: IEmailSender,
        db: MongoDatabase,
    ) -> None:
        self._repository = repository
        self._email_sender = email_sender
        self._db = db

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False,
    )
    async def execute(self, event: IncomingEvent) -> None:
        message = ResetPasswordMessage(
            user_id=event.payload.user_id,
            email=event.payload.recipient_email,
            subject="Password Reset Request",
            body=event.payload.reset_link,
            published_at=event.occurred_at,
        )

        async with await self._db.start_session() as session:
            async with session.start_transaction():
                await self._repository.save(message, session=session)
                logger.info("Message %s saved to MongoDB.", message.id)

                await self._email_sender.send_email(
                    to=message.email,
                    subject=message.subject,
                    body=message.body,
                )
                logger.info("Email sent to %s for message %s.", message.email, message.id)

                message.sent_at = datetime.now(timezone.utc)
                await self._repository.save(message, session=session)
