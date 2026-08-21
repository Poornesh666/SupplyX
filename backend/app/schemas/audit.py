from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AuditEventType = Literal[
    "rfq_created",
    "quote_uploaded",
    "quote_analyzed",
    "quote_extraction_failed",
    "risk_detected",
    "recommendation_generated",
    "rfq_approved",
    "rfq_rejected",
    "po_created",
    "po_issued",
    "po_acknowledged",
    "po_received",
    "po_cancelled",
    "inventory_received",
    "finance_transaction_created",
]


class AuditEventResponse(BaseModel):
    id: str
    rfq_id: str
    event_type: AuditEventType
    description: str
    actor: str | None
    created_at: datetime


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
