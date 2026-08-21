from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.rfq import RFQCreate, RFQListResponse, RFQResponse
from app.schemas.recommendation import RecommendationResponse
from app.schemas.scoring import ComparisonResponse
from app.services.ai.factory import AIProviderNotConfiguredError
from app.services.ai.provider import AIProviderError
from app.services.procurement.comparison_service import NoExtractedQuotesError, build_comparison
from app.services.procurement.recommendation_service import (
    NoQuotesAvailableError,
    get_or_generate_recommendation,
)
from app.services.rfq import rfq_service

router = APIRouter(prefix="/rfqs", tags=["rfqs"])


@router.post("", response_model=RFQResponse, status_code=201)
async def create_rfq(payload: RFQCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await rfq_service.create_rfq(db, payload)
    except rfq_service.VendorNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=RFQListResponse)
async def list_rfqs(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await rfq_service.list_rfqs(db)


@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq(rfq_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await rfq_service.get_rfq(db, rfq_id)
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{rfq_id}/comparison", response_model=ComparisonResponse)
async def get_comparison(rfq_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await build_comparison(db, rfq_id)
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NoExtractedQuotesError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{rfq_id}/recommendation", response_model=RecommendationResponse)
async def get_recommendation(rfq_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await get_or_generate_recommendation(db, rfq_id)
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NoQuotesAvailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (AIProviderError, AIProviderNotConfiguredError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
