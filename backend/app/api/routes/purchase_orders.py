from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
)
from app.services.purchase_order import purchase_order_service
from app.services.rfq import rfq_service

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.post("", response_model=PurchaseOrderResponse, status_code=201)
async def create_purchase_order(
    payload: PurchaseOrderCreate, db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        return await purchase_order_service.create_purchase_order(db, payload.rfq_id)
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except purchase_order_service.RFQNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except purchase_order_service.NoApprovedQuoteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await purchase_order_service.list_purchase_orders(db)


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(po_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await purchase_order_service.get_purchase_order(db, po_id)
    except purchase_order_service.PurchaseOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{po_id}/status", response_model=PurchaseOrderResponse)
async def update_purchase_order_status(
    po_id: str, payload: PurchaseOrderStatusUpdate, db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        return await purchase_order_service.update_purchase_order_status(
            db, po_id, payload.status
        )
    except purchase_order_service.PurchaseOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except purchase_order_service.InvalidPOStatusTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
