from app.schemas.risk import Risk
from app.schemas.scoring import ScoreBreakdown, ScoringWeights
from app.schemas.vendor import VendorResponse

SEVERITY_PENALTY = {"high": 4, "medium": 2, "low": 1}
PAYMENT_TERMS_MISSING_PENALTY_RATIO = 0.3


def score_price(calculated_total: float, min_total_across_quotes: float, weight: float) -> float:
    if calculated_total <= 0:
        return 0.0
    return round(weight * min(min_total_across_quotes / calculated_total, 1.0), 2)


def score_delivery(delivery_days: int | None, allowed_delivery_days: int, weight: float) -> float:
    if not delivery_days or delivery_days <= 0 or allowed_delivery_days <= 0:
        return 0.0
    return round(weight * min(allowed_delivery_days / delivery_days, 1.0), 2)


def score_quality(vendor_quality_score: float, weight: float) -> float:
    return round(weight * (vendor_quality_score / 100), 2)


def score_reliability(vendor_reliability_score: float, weight: float) -> float:
    return round(weight * (vendor_reliability_score / 100), 2)


def score_payment(
    vendor_payment_score: float, payment_terms_present: bool, weight: float
) -> float:
    base = weight * (vendor_payment_score / 100)
    if not payment_terms_present:
        base *= 1 - PAYMENT_TERMS_MISSING_PENALTY_RATIO
    return round(base, 2)


def score_risk(risks: list[Risk], weight: float) -> float:
    penalty = sum(SEVERITY_PENALTY.get(r.severity, 0) for r in risks)
    return round(max(weight - penalty, 0.0), 2)


def compute_score(
    *,
    calculated_total: float,
    min_total_across_quotes: float,
    delivery_days: int | None,
    allowed_delivery_days: int,
    payment_terms_present: bool,
    vendor: VendorResponse,
    risks: list[Risk],
    weights: ScoringWeights,
) -> ScoreBreakdown:
    """The SupplyX Decision Engine core: every component is a pure function
    of facts already extracted/normalized/detected — no AI call in this
    path, no randomness, same inputs always produce the same score."""
    return ScoreBreakdown(
        price=score_price(calculated_total, min_total_across_quotes, weights.price),
        delivery=score_delivery(delivery_days, allowed_delivery_days, weights.delivery),
        quality=score_quality(vendor.quality_score, weights.quality),
        reliability=score_reliability(vendor.reliability_score, weights.reliability),
        payment=score_payment(vendor.payment_score, payment_terms_present, weights.payment),
        risk=score_risk(risks, weights.risk),
    )
