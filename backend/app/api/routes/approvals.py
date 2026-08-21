from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.approval import ApprovalCreate, ApprovalResponse
from app.services.ai.factory import AIProviderNotConfiguredError
from app.services.ai.provider import AIProviderError
from app.services.procurement import approval_service
from app.services.rfq import rfq_service

router = APIRouter(prefix="/rfqs", tags=["approvals"])


@router.post("/{rfq_id}/approval", response_model=ApprovalResponse, status_code=201)
async def create_approval(
    rfq_id: str, payload: ApprovalCreate, db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        return await approval_service.create_approval(db, rfq_id, payload)
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except approval_service.InvalidApprovalStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (AIProviderError, AIProviderNotConfiguredError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{rfq_id}/approval", response_model=ApprovalResponse)
async def get_approval(rfq_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await approval_service.get_approval(db, rfq_id)
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except approval_service.ApprovalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
