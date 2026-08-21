from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.extraction import QuoteExtraction
from app.schemas.risk import Risk

QuoteStatus = Literal["extracted", "extraction_failed"]


class NormalizedQuote(BaseModel):
    calculated_subtotal: float
    calculated_total: float
    document_total: float | None
    total_matches_document: bool
    normalized_unit_price: float


class QuoteResponse(BaseModel):
    id: str
    rfq_id: str
    vendor_id: str
    filename: str
    file_type: str
    status: QuoteStatus
    extraction_error: str | None = None
    extraction: QuoteExtraction | None = None
    normalized: NormalizedQuote | None = None
    risks: list[Risk] = []
    created_at: datetime


class QuoteListResponse(BaseModel):
    items: list[QuoteResponse]
    total: int
