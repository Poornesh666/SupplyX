from typing import Literal

from pydantic import BaseModel

RiskSeverity = Literal["low", "medium", "high"]
RiskSource = Literal["deterministic", "ai"]


class Risk(BaseModel):
    type: str
    severity: RiskSeverity
    description: str
    source: RiskSource
    affected_field: str | None = None
