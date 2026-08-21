from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "audit_logs"


class AuditRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[COLLECTION]

    async def create(self, document: dict[str, Any]) -> None:
        await self._collection.insert_one(document)

    async def list_by_rfq(self, rfq_id: str) -> list[dict[str, Any]]:
        cursor = self._collection.find({"rfq_id": rfq_id}).sort("created_at", 1)
        return await cursor.to_list(length=None)
