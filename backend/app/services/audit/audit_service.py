import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditEventResponse, AuditEventType
from app.schemas.common import utcnow

logger = logging.getLogger(__name__)


async def record_event(
    db: AsyncIOMotorDatabase,
    rfq_id: str,
    event_type: AuditEventType,
    description: str,
    actor: str | None = None,
) -> None:
    """Fire-and-forget audit log write. Never raises -- a logging failure
    must not break the procurement action that triggered it."""
    try:
        repo = AuditRepository(db)
        await repo.create(
            {
                "rfq_id": rfq_id,
                "event_type": event_type,
                "description": description,
                "actor": actor,
                "created_at": utcnow(),
            }
        )
    except Exception:
        logger.exception("Failed to record audit event '%s' for RFQ %s", event_type, rfq_id)


async def get_audit_trail(db: AsyncIOMotorDatabase, rfq_id: str) -> list[AuditEventResponse]:
    repo = AuditRepository(db)
    docs = await repo.list_by_rfq(rfq_id)
    return [AuditEventResponse.model_validate(doc_to_response_dict(d)) for d in docs]
