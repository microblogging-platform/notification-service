import logging

from motor.core import AgnosticClientSession

from domain.entities import ResetPasswordMessage
from domain.interfaces.repositories import INotificationRepository
from infrastructure.mongo.database import MongoDatabase

logger = logging.getLogger(__name__)

COLLECTION_NAME = "notifications"


class MongoNotificationRepository(INotificationRepository):

    def __init__(self, db: MongoDatabase) -> None:
        self._collection = db.db[COLLECTION_NAME]

    async def save(
        self,
        message: ResetPasswordMessage,
        session: AgnosticClientSession | None = None,
    ) -> None:
        doc = message.model_dump(mode="json")
        doc["_id"] = doc.pop("id")

        await self._collection.replace_one(
            {"_id": doc["_id"]},
            doc,
            upsert=True,
            session=session,
        )
        logger.debug("Saved notification %s to MongoDB.", doc["_id"])
