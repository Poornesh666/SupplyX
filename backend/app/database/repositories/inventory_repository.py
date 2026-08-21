from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import to_object_id

COLLECTION = "inventory"


class InventoryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db[COLLECTION]

    async def list_all(self) -> list[dict[str, Any]]:
        cursor = self._collection.find().sort("sku", 1)
        return await cursor.to_list(length=None)

    async def get_by_id(self, item_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"_id": to_object_id(item_id)})

    async def find_by_sku(self, sku: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"sku": sku})

    async def find_by_description(self, description: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"description": description})

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self._collection.insert_one(document)
        return await self.get_by_id(str(result.inserted_id))

    async def update_quantities(
        self,
        item_id: str,
        quantity: float,
        available_quantity: float,
        updated_at,
    ) -> dict[str, Any] | None:
        await self._collection.update_one(
            {"_id": to_object_id(item_id)},
            {
                "$set": {
                    "quantity": quantity,
                    "available_quantity": available_quantity,
                    "updated_at": updated_at,
                }
            },
        )
        return await self.get_by_id(item_id)
