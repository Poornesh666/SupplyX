from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "procurement_decisions"


class RecommendationRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[COLLECTION]

    async def upsert_for_rfq(self, rfq_id: str, document: dict[str, Any]) -> None:
        await self._collection.update_one(
            {"rfq_id": rfq_id}, {"$set": document}, upsert=True
        )

    async def get_by_rfq(self, rfq_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"rfq_id": rfq_id})
