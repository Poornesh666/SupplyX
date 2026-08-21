from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies.database import get_db
from app.core.config import get_settings
from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.quote_repository import QuoteRepository
from app.schemas.quote import QuoteListResponse, QuoteResponse
from app.services.document.factory import SUPPORTED_EXTENSIONS
from app.services.procurement.quote_pipeline import VendorNotInvitedError, process_quote_upload
from app.services.rfq import rfq_service

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/upload", response_model=QuoteResponse, status_code=201)
async def upload_quote(
    rfq_id: str = Form(...),
    vendor_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    settings = get_settings()

    extension = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{extension}' — allowed: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_size_mb}MB upload limit",
        )

    try:
        return await process_quote_upload(
            db,
            rfq_id=rfq_id,
            vendor_id=vendor_id,
            filename=file.filename,
            file_bytes=file_bytes,
        )
    except rfq_service.RFQNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VendorNotInvitedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=QuoteListResponse)
async def list_quotes(rfq_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    repo = QuoteRepository(db)
    docs = await repo.list_by_rfq(rfq_id)
    items = [QuoteResponse.model_validate(doc_to_response_dict(d)) for d in docs]
    return QuoteListResponse(items=items, total=len(items))
