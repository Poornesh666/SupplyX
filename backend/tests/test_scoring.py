import pytest
from pydantic import ValidationError

from app.schemas.risk import Risk
from app.schemas.scoring import ScoringWeights
from app.schemas.vendor import VendorResponse
from app.services.procurement import scoring


def _vendor(**overrides) -> VendorResponse:
    base = dict(
        id="v1",
        vendor_id="VND-0001",
        name="Contact",
        company="Test Vendor",
        contact="",
        email="v@example.com",
        phone="",
        reliability_score=70,
        quality_score=70,
        payment_score=70,
        risk_level="medium",
        created_at="2026-01-01T00:00:00Z",
    )
    base.update(overrides)
    return VendorResponse(**base)


def _risk(severity: str, type_="test_risk") -> Risk:
    return Risk(type=type_, severity=severity, description="x", source="deterministic")


def test_weights_must_sum_to_100():
    ScoringWeights()  # default is valid
    with pytest.raises(ValidationError):
        ScoringWeights(price=50, delivery=20, quality=15, reliability=15, payment=10, risk=10)


def test_price_score_full_marks_for_cheapest():
    assert scoring.score_price(82500, 82500, weight=30) == 30

def test_price_score_scales_down_for_more_expensive():
    score = scoring.score_price(102500, 82500, weight=30)
    assert 0 < score < 30


def test_delivery_score_full_marks_when_within_deadline():
    score = scoring.score_delivery(10, allowed_delivery_days=15, weight=20)
    assert score == 20  # capped, not rewarded beyond full marks for being early


def test_delivery_score_penalised_past_deadline():
    score = scoring.score_delivery(30, allowed_delivery_days=15, weight=20)
    assert 0 < score < 20


def test_delivery_score_zero_when_missing():
    assert scoring.score_delivery(None, allowed_delivery_days=15, weight=20) == 0


def test_payment_score_penalised_when_terms_missing():
    with_terms = scoring.score_payment(80, payment_terms_present=True, weight=10)
    without_terms = scoring.score_payment(80, payment_terms_present=False, weight=10)
    assert without_terms < with_terms


def test_risk_score_floors_at_zero():
    heavy_risks = [_risk("high"), _risk("high"), _risk("high")]
    assert scoring.score_risk(heavy_risks, weight=10) == 0


def test_risk_score_full_marks_with_no_risks():
    assert scoring.score_risk([], weight=10) == 10


def test_delivery_deadline_violation_lowers_total_score():
    weights = ScoringWeights()
    vendor = _vendor()
    on_time = scoring.compute_score(
        calculated_total=90000,
        min_total_across_quotes=82500,
        delivery_days=10,
        allowed_delivery_days=15,
        payment_terms_present=True,
        vendor=vendor,
        risks=[],
        weights=weights,
    )
    late = scoring.compute_score(
        calculated_total=90000,
        min_total_across_quotes=82500,
        delivery_days=25,
        allowed_delivery_days=15,
        payment_terms_present=True,
        vendor=vendor,
        risks=[_risk("high", "delivery_exceeds_deadline")],
        weights=weights,
    )
    assert late.total < on_time.total


def test_risks_lower_total_score():
    weights = ScoringWeights()
    vendor = _vendor()
    clean = scoring.compute_score(
        calculated_total=90000,
        min_total_across_quotes=82500,
        delivery_days=10,
        allowed_delivery_days=15,
        payment_terms_present=True,
        vendor=vendor,
        risks=[],
        weights=weights,
    )
    risky = scoring.compute_score(
        calculated_total=90000,
        min_total_across_quotes=82500,
        delivery_days=10,
        allowed_delivery_days=15,
        payment_terms_present=True,
        vendor=vendor,
        risks=[_risk("high"), _risk("medium")],
        weights=weights,
    )
    assert risky.total < clean.total


def test_cheapest_vendor_does_not_automatically_win():
    """The core SupplyX claim: a cheap, risky, late vendor must lose to a
    moderately-priced, reliable, on-time vendor. Mirrors the Apex/Bharat/
    Nova demo scenario end to end through the real scoring function."""
    weights = ScoringWeights()
    min_total = 82500  # Nova is cheapest

    apex = scoring.compute_score(
        calculated_total=90000,
        min_total_across_quotes=min_total,
        delivery_days=18,
        allowed_delivery_days=15,
        payment_terms_present=True,
        vendor=_vendor(quality_score=70, reliability_score=65, payment_score=70),
        risks=[_risk("high", "delivery_exceeds_deadline")],
        weights=weights,
    )
    bharat = scoring.compute_score(
        calculated_total=102500,
        min_total_across_quotes=min_total,
        delivery_days=10,
        allowed_delivery_days=15,
        payment_terms_present=True,
        vendor=_vendor(quality_score=85, reliability_score=90, payment_score=80),
        risks=[],
        weights=weights,
    )
    nova = scoring.compute_score(
        calculated_total=82500,
        min_total_across_quotes=min_total,
        delivery_days=20,
        allowed_delivery_days=15,
        payment_terms_present=False,
        vendor=_vendor(quality_score=55, reliability_score=50, payment_score=60),
        risks=[
            _risk("high", "delivery_exceeds_deadline"),
            _risk("medium", "missing_warranty"),
            _risk("medium", "missing_payment_terms"),
            _risk("high", "moq_exceeds_rfq_quantity"),
            _risk("medium", "suspicious_exclusion"),
        ],
        weights=weights,
    )

    assert bharat.total > apex.total > nova.total
    # The cheapest vendor (Nova) must not be ranked first.
    assert max(apex.total, bharat.total, nova.total) != nova.total
