from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.audit import AuditEventListResponse
from app.services.audit.audit_service import get_audit_trail

router = APIRouter(prefix="/rfqs", tags=["audit"])


@router.get("/{rfq_id}/audit-trail", response_model=AuditEventListResponse)
async def get_rfq_audit_trail(rfq_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    return AuditEventListResponse(items=await get_audit_trail(db, rfq_id))
