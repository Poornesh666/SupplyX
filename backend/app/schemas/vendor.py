from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

RiskLevel = Literal["low", "medium", "high"]


class VendorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=2, max_length=200)
    contact: str = Field(default="", max_length=200)
    email: EmailStr
    phone: str = Field(default="", max_length=30)
    reliability_score: float = Field(ge=0, le=100, default=70)
    quality_score: float = Field(ge=0, le=100, default=70)
    payment_score: float = Field(ge=0, le=100, default=70)
    risk_level: RiskLevel = "medium"


class VendorResponse(BaseModel):
    id: str
    vendor_id: str
    name: str
    company: str
    contact: str
    email: str
    phone: str
    reliability_score: float
    quality_score: float
    payment_score: float
    risk_level: RiskLevel
    created_at: datetime


class VendorListResponse(BaseModel):
    items: list[VendorResponse]
    total: int
