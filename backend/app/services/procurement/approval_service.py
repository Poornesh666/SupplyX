from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.approval_repository import ApprovalRepository
from app.database.repositories.rfq_repository import RFQRepository
from app.schemas.approval import ApprovalCreate, ApprovalResponse
from app.schemas.common import utcnow
from app.services.procurement.recommendation_service import get_or_generate_recommendation
from app.services.rfq import rfq_service

ALREADY_DECIDED_STATUSES = {"approved", "rejected", "po_created", "po_issued"}


class ApprovalNotFoundError(ValueError):
    pass


class InvalidApprovalStateError(ValueError):
    pass


async def create_approval(
    db: AsyncIOMotorDatabase, rfq_id: str, payload: ApprovalCreate
) -> ApprovalResponse:
    """Approve or reject the RFQ's current system recommendation.

    The approval always applies to whatever vendor `get_or_generate_recommendation`
    currently identifies as the winner — callers cannot substitute a different
    vendor, keeping the decision trail auditable and unambiguous.
    """
    rfq = await rfq_service.get_rfq(db, rfq_id)  # raises RFQNotFoundError if missing

    if rfq.status in ALREADY_DECIDED_STATUSES:
        raise InvalidApprovalStateError(
            f"RFQ '{rfq_id}' has already been decided (status='{rfq.status}')"
        )
    if rfq.status != "recommendation_ready":
        raise InvalidApprovalStateError(
            f"RFQ '{rfq_id}' has no recommendation to approve yet (status='{rfq.status}')"
        )

    recommendation = await get_or_generate_recommendation(db, rfq_id)

    now = utcnow()
    document = {
        "rfq_id": rfq_id,
        "decision": payload.decision,
        "approver_name": payload.approver_name,
        "note": payload.note,
        "recommended_vendor_id": recommendation.recommended_vendor_id,
        "recommended_vendor_name": recommendation.recommended_vendor_name,
        "recommended_score": recommendation.recommended_score,
        "decided_at": now,
    }
    repo = ApprovalRepository(db)
    created = await repo.create(document)

    # approved/rejected are terminal-ish branches outside the linear
    # RFQ_STATUS_ORDER, so update the RFQ directly rather than through the
    # forward-only advance_status helper.
    rfq_repo = RFQRepository(db)
    await rfq_repo.update_status(rfq_id, payload.decision, now)

    from app.services.audit.audit_service import record_event

    event_type = "rfq_approved" if payload.decision == "approved" else "rfq_rejected"
    note_suffix = f" — {payload.note}" if payload.note else ""
    await record_event(
        db,
        rfq_id,
        event_type,
        f"{recommendation.recommended_vendor_name} {payload.decision} by {payload.approver_name}{note_suffix}",
        actor=payload.approver_name,
    )

    return ApprovalResponse.model_validate(doc_to_response_dict(created))


async def get_approval(db: AsyncIOMotorDatabase, rfq_id: str) -> ApprovalResponse:
    await rfq_service.get_rfq(db, rfq_id)  # raises RFQNotFoundError if missing

    repo = ApprovalRepository(db)
    doc = await repo.get_by_rfq(rfq_id)
    if doc is None:
        raise ApprovalNotFoundError(f"No approval decision recorded for RFQ '{rfq_id}'")
    return ApprovalResponse.model_validate(doc_to_response_dict(doc))
