from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.insights import ProcurementInsightListResponse
from app.services.procurement.insights_service import build_insights

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=ProcurementInsightListResponse)
async def get_insights(
    rfq_id: str | None = None, db: AsyncIOMotorDatabase = Depends(get_db)
):
    return ProcurementInsightListResponse(items=await build_insights(db, rfq_id))
