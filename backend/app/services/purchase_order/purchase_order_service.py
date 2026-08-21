from datetime import date, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.approval_repository import ApprovalRepository
from app.database.repositories.purchase_order_repository import PurchaseOrderRepository
from app.database.repositories.quote_repository import QuoteRepository
from app.database.repositories.rfq_repository import RFQRepository
from app.database.repositories.vendor_repository import VendorRepository
from app.schemas.common import utcnow
from app.schemas.purchase_order import (
    PurchaseOrderItem,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
)
from app.schemas.quote import QuoteResponse
from app.services.rfq import rfq_service

# draft -> issued -> acknowledged -> received; cancellation only from draft/issued.
LEGAL_PO_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"issued", "cancelled"},
    "issued": {"acknowledged", "cancelled"},
    "acknowledged": {"received"},
    "received": set(),
    "cancelled": set(),
}


class RFQNotApprovedError(ValueError):
    pass


class NoApprovedQuoteError(ValueError):
    pass


class PurchaseOrderNotFoundError(ValueError):
    pass


class InvalidPOStatusTransitionError(ValueError):
    pass


async def _next_po_number(repo: PurchaseOrderRepository) -> str:
    year = date.today().year
    prefix = f"PO-{year}-"
    count = await repo.count_with_number_prefix(prefix)
    return f"{prefix}{count + 1:03d}"


async def create_purchase_order(db: AsyncIOMotorDatabase, rfq_id: str) -> PurchaseOrderResponse:
    rfq = await rfq_service.get_rfq(db, rfq_id)  # raises RFQNotFoundError if missing

    if rfq.status != "approved":
        raise RFQNotApprovedError(
            f"RFQ '{rfq_id}' must be approved before a purchase order can be created "
            f"(current status='{rfq.status}')"
        )

    approval_repo = ApprovalRepository(db)
    approval = await approval_repo.get_by_rfq(rfq_id)
    if approval is None:
        # Shouldn't happen if status is "approved", but guard against
        # inconsistent state rather than crashing.
        raise NoApprovedQuoteError(f"No approval record found for RFQ '{rfq_id}'")

    vendor_id = approval["recommended_vendor_id"]

    quote_repo = QuoteRepository(db)
    extracted_docs = await quote_repo.list_extracted_by_rfq(rfq_id)
    quote_doc = next((d for d in extracted_docs if d["vendor_id"] == vendor_id), None)
    if quote_doc is None:
        raise NoApprovedQuoteError(
            f"No extracted quote found for approved vendor '{vendor_id}' on RFQ '{rfq_id}'"
        )
    quote = QuoteResponse.model_validate(doc_to_response_dict(quote_doc))
    if quote.extraction is None or quote.normalized is None:
        raise NoApprovedQuoteError(
            f"Approved vendor's quote on RFQ '{rfq_id}' has no usable extraction"
        )

    vendor_repo = VendorRepository(db)
    vendor_doc = await vendor_repo.get_by_id(vendor_id)
    vendor_name = vendor_doc["company"] if vendor_doc else approval["recommended_vendor_name"]

    items = [
        PurchaseOrderItem(
            sku=item.sku,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            line_total=round(item.quantity * item.unit_price, 2),
        )
        for item in quote.extraction.items
    ]

    delivery_days = quote.extraction.delivery_days
    delivery_terms = (
        f"{delivery_days} days from order confirmation" if delivery_days is not None else None
    )
    expected_delivery_date = (
        (date.today() + timedelta(days=delivery_days)).isoformat()
        if delivery_days is not None
        else rfq.required_delivery_date.isoformat()
    )

    po_repo = PurchaseOrderRepository(db)
    now = utcnow()
    document = {
        "po_number": await _next_po_number(po_repo),
        "rfq_id": rfq_id,
        "rfq_number": rfq.rfq_number,
        "vendor_id": vendor_id,
        "vendor_name": vendor_name,
        "items": [i.model_dump() for i in items],
        "subtotal": quote.normalized.calculated_subtotal,
        "discount": quote.extraction.discount or 0,
        "tax": quote.extraction.tax or 0,
        "shipping": quote.extraction.shipping or 0,
        "total": quote.normalized.calculated_total,
        "delivery_terms": delivery_terms,
        "payment_terms": quote.extraction.payment_terms,
        "warranty": quote.extraction.warranty,
        "expected_delivery_date": expected_delivery_date,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
    }
    created = await po_repo.create(document)

    # po_created is outside the linear RFQ_STATUS_ORDER, so update directly.
    rfq_repo = RFQRepository(db)
    await rfq_repo.update_status(rfq_id, "po_created", now)

    response = PurchaseOrderResponse.model_validate(doc_to_response_dict(created))

    from app.services.audit.audit_service import record_event

    await record_event(
        db,
        rfq_id,
        "po_created",
        f"Purchase order {response.po_number} created for {vendor_name} (total {response.total:,.2f})",
    )

    return response


async def list_purchase_orders(db: AsyncIOMotorDatabase) -> PurchaseOrderListResponse:
    repo = PurchaseOrderRepository(db)
    items, total = await repo.list_all()
    return PurchaseOrderListResponse(
        items=[PurchaseOrderResponse.model_validate(doc_to_response_dict(i)) for i in items],
        total=total,
    )


async def get_purchase_order(db: AsyncIOMotorDatabase, po_id: str) -> PurchaseOrderResponse:
    repo = PurchaseOrderRepository(db)
    doc = await repo.get_by_id(po_id)
    if doc is None:
        raise PurchaseOrderNotFoundError(f"Purchase order '{po_id}' not found")
    return PurchaseOrderResponse.model_validate(doc_to_response_dict(doc))


async def update_purchase_order_status(
    db: AsyncIOMotorDatabase, po_id: str, new_status: str
) -> PurchaseOrderResponse:
    repo = PurchaseOrderRepository(db)
    doc = await repo.get_by_id(po_id)
    if doc is None:
        raise PurchaseOrderNotFoundError(f"Purchase order '{po_id}' not found")

    current_status = doc["status"]
    allowed = LEGAL_PO_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise InvalidPOStatusTransitionError(
            f"Cannot move purchase order '{po_id}' from '{current_status}' to '{new_status}'"
        )

    now = utcnow()
    await repo.update_status(po_id, new_status, now)

    if new_status == "issued":
        rfq_repo = RFQRepository(db)
        await rfq_repo.update_status(doc["rfq_id"], "po_issued", now)

    from app.services.audit.audit_service import record_event

    PO_EVENT_TYPES = {
        "issued": "po_issued",
        "acknowledged": "po_acknowledged",
        "received": "po_received",
        "cancelled": "po_cancelled",
    }
    event_type = PO_EVENT_TYPES.get(new_status)
    if event_type:
        await record_event(
            db,
            doc["rfq_id"],
            event_type,
            f"Purchase order {doc['po_number']} {new_status}",
        )

    updated = await repo.get_by_id(po_id)
    return PurchaseOrderResponse.model_validate(doc_to_response_dict(updated))
