from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import to_object_id

COLLECTION = "vendors"


class VendorRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[COLLECTION]

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self._collection.insert_one(document)
        return await self.get_by_id(str(result.inserted_id))

    async def get_by_id(self, vendor_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"_id": to_object_id(vendor_id)})

    async def get_many_by_ids(self, vendor_ids: list[str]) -> list[dict[str, Any]]:
        object_ids = [to_object_id(v) for v in vendor_ids]
        cursor = self._collection.find({"_id": {"$in": object_ids}})
        return await cursor.to_list(length=len(object_ids) or None)

    async def list_all(self, limit: int = 200) -> tuple[list[dict[str, Any]], int]:
        total = await self._collection.count_documents({})
        cursor = self._collection.find().sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return items, total

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"email": email})

    async def count(self) -> int:
        return await self._collection.count_documents({})
