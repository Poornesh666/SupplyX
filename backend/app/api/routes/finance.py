from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.finance import FinanceSummary, FinanceTransactionListResponse
from app.services.finance import finance_service

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/transactions", response_model=FinanceTransactionListResponse)
async def list_finance_transactions(db: AsyncIOMotorDatabase = Depends(get_db)):
    items = await finance_service.list_finance_transactions(db)
    return FinanceTransactionListResponse(items=items)


@router.get("/summary", response_model=FinanceSummary)
async def get_finance_summary(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await finance_service.get_finance_summary(db)
