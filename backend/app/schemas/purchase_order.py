from datetime import datetime
from typing import Literal

from pydantic import BaseModel

PurchaseOrderStatus = Literal["draft", "issued", "acknowledged", "received", "cancelled"]


class PurchaseOrderCreate(BaseModel):
    rfq_id: str


class PurchaseOrderStatusUpdate(BaseModel):
    status: PurchaseOrderStatus


class PurchaseOrderItem(BaseModel):
    sku: str | None = None
    description: str
    quantity: float
    unit: str | None = None
    unit_price: float
    line_total: float


class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str
    rfq_id: str
    rfq_number: str
    vendor_id: str
    vendor_name: str
    items: list[PurchaseOrderItem]
    subtotal: float
    discount: float
    tax: float
    shipping: float
    total: float
    delivery_terms: str | None
    payment_terms: str | None
    warranty: str | None
    expected_delivery_date: str | None
    status: PurchaseOrderStatus
    created_at: datetime


class PurchaseOrderListResponse(BaseModel):
    items: list[PurchaseOrderResponse]
    total: int
