from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.schemas.vendor import VendorCreate, VendorListResponse, VendorResponse
from app.services.vendor import vendor_service

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(payload: VendorCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await vendor_service.create_vendor(db, payload)
    except vendor_service.DuplicateVendorEmailError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=VendorListResponse)
async def list_vendors(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await vendor_service.list_vendors(db)


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        return await vendor_service.get_vendor(db, vendor_id)
    except vendor_service.VendorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
