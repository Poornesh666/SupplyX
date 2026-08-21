from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import to_object_id

COLLECTION = "quotes"


class QuoteRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[COLLECTION]

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self._collection.insert_one(document)
        return await self.get_by_id(str(result.inserted_id))

    async def get_by_id(self, quote_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"_id": to_object_id(quote_id)})

    async def list_by_rfq(self, rfq_id: str) -> list[dict[str, Any]]:
        cursor = self._collection.find({"rfq_id": rfq_id}).sort("created_at", 1)
        return await cursor.to_list(length=None)

    async def list_extracted_by_rfq(self, rfq_id: str) -> list[dict[str, Any]]:
        cursor = self._collection.find(
            {"rfq_id": rfq_id, "status": "extracted"}
        ).sort("created_at", 1)
        return await cursor.to_list(length=None)
