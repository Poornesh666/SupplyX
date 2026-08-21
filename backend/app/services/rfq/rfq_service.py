from datetime import date

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.rfq_repository import RFQRepository
from app.database.repositories.vendor_repository import VendorRepository
from app.schemas.common import utcnow
from app.schemas.rfq import RFQCreate, RFQListResponse, RFQResponse

RFQ_STATUS_ORDER = [
    "created",
    "quotes_received",
    "analysis_complete",
    "recommendation_ready",
]


class VendorNotFoundError(ValueError):
    pass


class RFQNotFoundError(ValueError):
    pass


async def _next_rfq_number(repo: RFQRepository) -> str:
    year = date.today().year
    prefix = f"RFQ-{year}-"
    count = await repo.count_with_number_prefix(prefix)
    return f"{prefix}{count + 1:03d}"


async def create_rfq(db: AsyncIOMotorDatabase, payload: RFQCreate) -> RFQResponse:
    rfq_repo = RFQRepository(db)
    vendor_repo = VendorRepository(db)

    if payload.invited_vendor_ids:
        found = await vendor_repo.get_many_by_ids(payload.invited_vendor_ids)
        found_ids = {str(v["_id"]) for v in found}
        missing = set(payload.invited_vendor_ids) - found_ids
        if missing:
            raise VendorNotFoundError(f"Unknown vendor id(s): {', '.join(missing)}")

    now = utcnow()
    allowed_days = (payload.required_delivery_date - date.today()).days

    document = {
        "rfq_number": await _next_rfq_number(rfq_repo),
        "title": payload.title,
        "description": payload.description,
        "specifications": payload.specifications,
        "quantity": payload.quantity,
        "unit": payload.unit,
        "required_delivery_date": payload.required_delivery_date.isoformat(),
        "allowed_delivery_days": allowed_days,
        "invited_vendor_ids": payload.invited_vendor_ids,
        "status": "created",
        "created_at": now,
        "updated_at": now,
    }
    created = await rfq_repo.create(document)
    response = RFQResponse.model_validate(doc_to_response_dict(created))

    from app.services.audit.audit_service import record_event

    await record_event(
        db, response.id, "rfq_created", f"RFQ {response.rfq_number} created: {response.title}"
    )

    return response


async def list_rfqs(db: AsyncIOMotorDatabase) -> RFQListResponse:
    rfq_repo = RFQRepository(db)
    items, total = await rfq_repo.list_all()
    return RFQListResponse(
        items=[RFQResponse.model_validate(doc_to_response_dict(i)) for i in items],
        total=total,
    )


async def get_rfq(db: AsyncIOMotorDatabase, rfq_id: str) -> RFQResponse:
    rfq_repo = RFQRepository(db)
    doc = await rfq_repo.get_by_id(rfq_id)
    if doc is None:
        raise RFQNotFoundError(f"RFQ '{rfq_id}' not found")
    return RFQResponse.model_validate(doc_to_response_dict(doc))


async def advance_status(db: AsyncIOMotorDatabase, rfq_id: str, new_status: str) -> None:
    """Move an RFQ's status forward only — never regress an already-advanced RFQ."""
    rfq_repo = RFQRepository(db)
    doc = await rfq_repo.get_by_id(rfq_id)
    if doc is None:
        return
    if doc["status"] not in RFQ_STATUS_ORDER:
        # Already past this linear pipeline (approved/rejected/po_created/po_issued) --
        # those branching states are owned by approval_service/purchase_order_service,
        # not this forward-only helper. Nothing to do.
        return
    current_index = RFQ_STATUS_ORDER.index(doc["status"])
    new_index = RFQ_STATUS_ORDER.index(new_status)
    if new_index > current_index:
        await rfq_repo.update_status(rfq_id, new_status, utcnow())
