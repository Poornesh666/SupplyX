from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.inventory import InventoryListResponse, ReceiveInventoryInput
from app.services.inventory import inventory_service
from app.services.purchase_order import purchase_order_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=InventoryListResponse)
async def list_inventory(db: AsyncIOMotorDatabase = Depends(get_db)):
    items = await inventory_service.list_inventory(db)
    return InventoryListResponse(items=items)


@router.post("/receive", response_model=InventoryListResponse)
async def receive_inventory(
    payload: ReceiveInventoryInput, db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        items = await inventory_service.receive_inventory(db, payload.po_id)
    except purchase_order_service.PurchaseOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except inventory_service.PONotReceivableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return InventoryListResponse(items=items)
