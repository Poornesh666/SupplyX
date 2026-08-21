from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

RFQStatus = Literal[
    "created",
    "quotes_received",
    "analysis_complete",
    "recommendation_ready",
    "approved",
    "rejected",
    "po_created",
    "po_issued",
]


class RFQCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=2000)
    specifications: str = Field(default="", max_length=2000)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    required_delivery_date: date
    invited_vendor_ids: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("required_delivery_date")
    @classmethod
    def must_be_future(cls, value: date) -> date:
        if value <= date.today():
            raise ValueError("required_delivery_date must be in the future")
        return value


class RFQResponse(BaseModel):
    id: str
    rfq_number: str
    title: str
    description: str
    specifications: str
    quantity: float
    unit: str
    required_delivery_date: date
    allowed_delivery_days: int
    invited_vendor_ids: list[str]
    status: RFQStatus
    created_at: datetime
    updated_at: datetime


class RFQListResponse(BaseModel):
    items: list[RFQResponse]
    total: int
