import logging

from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClientSession

logger = logging.getLogger(__name__)


class MongoDatabase:
    def __init__(self, uri: str, db_name: str) -> None:
        self._client: AsyncIOMotorClient = AsyncIOMotorClient(uri)
        self._db_name = db_name
        logger.info("MongoDatabase initialised. db=%s", db_name)

    @property
    def db(self):
        return self._client[self._db_name]

    async def start_session(self) -> AgnosticClientSession:
        return await self._client.start_session()

    def close(self) -> None:
        self._client.close()
        logger.info("MongoDB connection closed.")
