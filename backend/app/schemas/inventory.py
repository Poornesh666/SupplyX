from datetime import datetime

from pydantic import BaseModel


class InventoryItem(BaseModel):
    id: str
    sku: str
    description: str
    quantity: float
    reserved_quantity: float
    available_quantity: float
    reorder_level: float
    unit: str
    warehouse: str
    updated_at: datetime


class InventoryListResponse(BaseModel):
    items: list[InventoryItem]


class ReceiveInventoryInput(BaseModel):
    po_id: str
