from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.dashboard import DashboardMetrics
from app.services.procurement.dashboard_service import build_dashboard_metrics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardMetrics)
async def get_dashboard_summary(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await build_dashboard_metrics(db)
