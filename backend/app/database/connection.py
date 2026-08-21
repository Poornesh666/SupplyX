import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Database:
    """Holds the single Motor client/database instance for the app lifespan."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


database = Database()


async def connect_to_mongo() -> None:
    settings = get_settings()
    database.client = AsyncIOMotorClient(settings.mongodb_uri)
    database.db = database.client[settings.mongodb_database]
    try:
        await database.client.admin.command("ping")
        logger.info("Connected to MongoDB database '%s'", settings.mongodb_database)
    except Exception:
        logger.exception("Could not reach MongoDB at startup — check MONGODB_URI")


async def close_mongo_connection() -> None:
    if database.client is not None:
        database.client.close()
        logger.info("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    if database.db is None:
        raise RuntimeError("Database not initialized — connect_to_mongo() must run first")
    return database.db
