from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import to_object_id

COLLECTION = "purchase_orders"


class PurchaseOrderRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[COLLECTION]

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self._collection.insert_one(document)
        return await self.get_by_id(str(result.inserted_id))

    async def get_by_id(self, po_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"_id": to_object_id(po_id)})

    async def get_by_rfq(self, rfq_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"rfq_id": rfq_id})

    async def list_all(self, limit: int = 200) -> tuple[list[dict[str, Any]], int]:
        total = await self._collection.count_documents({})
        cursor = self._collection.find().sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return items, total

    async def update_status(self, po_id: str, status: str, updated_at) -> None:
        await self._collection.update_one(
            {"_id": to_object_id(po_id)},
            {"$set": {"status": status, "updated_at": updated_at}},
        )

    async def count_with_number_prefix(self, prefix: str) -> int:
        return await self._collection.count_documents(
            {"po_number": {"$regex": f"^{prefix}"}}
        )
