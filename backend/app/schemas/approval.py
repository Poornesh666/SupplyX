from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ApprovalDecision = Literal["approved", "rejected"]


class ApprovalCreate(BaseModel):
    decision: ApprovalDecision
    approver_name: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=1000)


class ApprovalResponse(BaseModel):
    id: str
    rfq_id: str
    decision: ApprovalDecision
    approver_name: str
    note: str | None
    recommended_vendor_id: str
    recommended_vendor_name: str
    recommended_score: float
    decided_at: datetime
