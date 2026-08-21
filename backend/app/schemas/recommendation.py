from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Confidence = Literal["low", "medium", "high"]


class RecommendationExplanation(BaseModel):
    """AI-generated explanation of a decision Python already made.

    The AI receives the deterministic winner, score, and runner-up as
    fixed facts — it explains them, it does not decide them.
    """

    recommendation_summary: str
    why_recommended: list[str]
    key_strengths: list[str]
    key_risks: list[str]
    tradeoffs: list[str]
    alternative_vendor: str | None
    confidence: Confidence
    explanation: str


class RecommendationResponse(BaseModel):
    rfq_id: str
    recommended_vendor_id: str
    recommended_vendor_name: str
    recommended_score: float
    alternative_vendor_id: str | None
    alternative_vendor_name: str | None
    alternative_score: float | None
    potential_savings: float | None
    explanation: RecommendationExplanation
    generated_at: datetime
