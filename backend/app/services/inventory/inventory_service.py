from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.inventory_repository import InventoryRepository
from app.schemas.common import utcnow
from app.schemas.inventory import InventoryItem
from app.services.purchase_order import purchase_order_service

DEFAULT_WAREHOUSE = "Main Warehouse"

# PO statuses that can be received against, and the transition steps needed
# to get from that status to "received".
_RECEIVE_PATH: dict[str, list[str]] = {
    "issued": ["acknowledged", "received"],
    "acknowledged": ["received"],
}


class PONotReceivableError(ValueError):
    pass


async def list_inventory(db: AsyncIOMotorDatabase) -> list[InventoryItem]:
    repo = InventoryRepository(db)
    docs = await repo.list_all()
    return [InventoryItem.model_validate(doc_to_response_dict(d)) for d in docs]


async def receive_inventory(db: AsyncIOMotorDatabase, po_id: str) -> list[InventoryItem]:
    po = await purchase_order_service.get_purchase_order(db, po_id)  # raises PurchaseOrderNotFoundError

    steps = _RECEIVE_PATH.get(po.status)
    if steps is None:
        raise PONotReceivableError(
            f"Purchase order '{po_id}' cannot be received from status '{po.status}'"
        )

    for status in steps:
        await purchase_order_service.update_purchase_order_status(db, po_id, status)

    repo = InventoryRepository(db)
    now = utcnow()
    touched: list[InventoryItem] = []

    for item in po.items:
        existing = None
        if item.sku:
            existing = await repo.find_by_sku(item.sku)
        if existing is None:
            existing = await repo.find_by_description(item.description)

        if existing is None:
            quantity = item.quantity
            reorder_level = round(quantity * 0.2, 2) or 1
            document = {
                "sku": item.sku or item.description,
                "description": item.description,
                "quantity": quantity,
                "reserved_quantity": 0,
                "available_quantity": quantity,
                "reorder_level": reorder_level,
                "unit": item.unit or "unit",
                "warehouse": DEFAULT_WAREHOUSE,
                "updated_at": now,
            }
            created = await repo.create(document)
            touched.append(InventoryItem.model_validate(doc_to_response_dict(created)))
        else:
            new_quantity = existing["quantity"] + item.quantity
            reserved = existing.get("reserved_quantity", 0)
            new_available = new_quantity - reserved
            updated = await repo.update_quantities(
                str(existing["_id"]), new_quantity, new_available, now
            )
            touched.append(InventoryItem.model_validate(doc_to_response_dict(updated)))

    from app.services.audit.audit_service import record_event

    summary = ", ".join(f"{i.quantity} {i.unit or 'unit'} of {i.description}" for i in po.items)
    await record_event(
        db,
        po.rfq_id,
        "inventory_received",
        f"Received {summary} against PO {po.po_number}",
    )

    return touched
