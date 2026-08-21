from pydantic import BaseModel, model_validator

from app.schemas.risk import Risk


class ScoringWeights(BaseModel):
    price: float = 30
    delivery: float = 20
    quality: float = 15
    reliability: float = 15
    payment: float = 10
    risk: float = 10

    @model_validator(mode="after")
    def weights_sum_to_100(self) -> "ScoringWeights":
        total = (
            self.price
            + self.delivery
            + self.quality
            + self.reliability
            + self.payment
            + self.risk
        )
        if abs(total - 100) > 0.01:
            raise ValueError(f"Scoring weights must sum to 100, got {total}")
        return self


class ScoreBreakdown(BaseModel):
    price: float
    delivery: float
    quality: float
    reliability: float
    payment: float
    risk: float

    @property
    def total(self) -> float:
        return round(
            self.price
            + self.delivery
            + self.quality
            + self.reliability
            + self.payment
            + self.risk,
            2,
        )


class VendorComparisonEntry(BaseModel):
    vendor_id: str
    vendor_name: str
    quote_id: str
    calculated_total: float
    delivery_days: int | None
    score: ScoreBreakdown
    total_score: float
    rank: int
    risks: list[Risk]


class ComparisonResponse(BaseModel):
    rfq_id: str
    weights: ScoringWeights
    entries: list[VendorComparisonEntry]
    lowest_price_vendor_id: str | None
    recommended_vendor_id: str | None
