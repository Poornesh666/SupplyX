from typing import Literal

from pydantic import BaseModel

InsightCategory = Literal["risk", "savings", "quality", "general"]


class ProcurementInsight(BaseModel):
    id: str
    rfq_id: str | None
    summary: str
    category: InsightCategory


class ProcurementInsightListResponse(BaseModel):
    items: list[ProcurementInsight]
