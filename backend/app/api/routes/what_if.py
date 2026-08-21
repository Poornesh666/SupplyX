from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.api.dependencies.database import get_db
from app.schemas.scoring import ComparisonResponse, ScoringWeights
from app.services.procurement.comparison_service import (
    NoExtractedQuotesError,
    build_comparison,
)
from app.services.rfq import rfq_service

router = APIRouter(prefix="/rfqs", tags=["what-if"])


class WhatIfRequest(BaseModel):
    weights: ScoringWeights


@router.post("/{rfq_id}/what-if", response_model=ComparisonResponse)
async def simulate_what_if(
    rfq_id: str, payload: WhatIfRequest, db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Pure recompute of the vendor comparison under custom scoring weights.

    Does not persist anything or advance RFQ status side effects beyond what
    build_comparison already does for the default comparison endpoint.
    """
    try:
        return await build_comparison(db, rfq_id, weights=payload.weights)
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NoExtractedQuotesError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
