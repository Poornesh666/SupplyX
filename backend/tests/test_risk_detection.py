from datetime import date

from app.schemas.extraction import ExtractedItem, QuoteExtraction
from app.services.procurement.normalization import normalize_quote
from app.services.procurement.risk_detection import (
    detect_cross_quote_pricing_risk,
    detect_quote_risks,
)

REQUIRED_DELIVERY_DATE = date(2026, 9, 15)
ALLOWED_DELIVERY_DAYS = 26
RFQ_QUANTITY = 500


def _extraction(**overrides) -> QuoteExtraction:
    base = dict(
        items=[ExtractedItem(description="Widget", quantity=500, unit_price=180)],
        delivery_days=10,
        warranty="1 year",
        payment_terms="Net 30",
    )
    base.update(overrides)
    return QuoteExtraction(**base)


def _risks(extraction: QuoteExtraction):
    normalized = normalize_quote(extraction, required_quantity=RFQ_QUANTITY)
    return detect_quote_risks(
        extraction,
        normalized,
        rfq_quantity=RFQ_QUANTITY,
        allowed_delivery_days=ALLOWED_DELIVERY_DAYS,
        required_delivery_date=REQUIRED_DELIVERY_DATE,
    )


def test_clean_quote_has_no_deterministic_risks():
    risks = _risks(_extraction(quote_number="Q-1", validity_days=30))
    assert [r for r in risks if r.source == "deterministic"] == []


def test_delivery_exceeds_deadline_is_high_severity():
    risks = _risks(_extraction(delivery_days=40))
    matches = [r for r in risks if r.type == "delivery_exceeds_deadline"]
    assert len(matches) == 1
    assert matches[0].severity == "high"


def test_missing_warranty_detected():
    risks = _risks(_extraction(warranty=None))
    assert any(r.type == "missing_warranty" for r in risks)


def test_missing_payment_terms_detected():
    risks = _risks(_extraction(payment_terms=None))
    assert any(r.type == "missing_payment_terms" for r in risks)


def test_moq_exceeds_rfq_quantity_detected():
    risks = _risks(_extraction(moq=600))
    matches = [r for r in risks if r.type == "moq_exceeds_rfq_quantity"]
    assert len(matches) == 1
    assert matches[0].severity == "high"


def test_moq_within_quantity_not_flagged():
    risks = _risks(_extraction(moq=50))
    assert not any(r.type == "moq_exceeds_rfq_quantity" for r in risks)


def test_inconsistent_totals_detected():
    risks = _risks(_extraction(total=999999))
    matches = [r for r in risks if r.type == "inconsistent_totals"]
    assert len(matches) == 1
    assert matches[0].severity == "high"


def test_suspicious_exclusion_keyword_detected():
    risks = _risks(_extraction(exclusions=["No warranty on bulk orders"]))
    assert any(r.type == "suspicious_exclusion" for r in risks)


def test_missing_line_items_is_high_severity():
    risks = _risks(_extraction(items=[]))
    matches = [r for r in risks if r.type == "missing_line_items"]
    assert len(matches) == 1
    assert matches[0].severity == "high"


def test_ai_identified_risks_are_carried_through_with_ai_source():
    risks = _risks(_extraction(risks=["Vendor mentions possible supply shortage"]))
    matches = [r for r in risks if r.type == "ai_identified_risk"]
    assert len(matches) == 1
    assert matches[0].source == "ai"


def test_cross_quote_unusual_pricing_flags_outlier():
    risk = detect_cross_quote_pricing_risk(50.0, [180.0, 190.0, 50.0])
    assert risk is not None
    assert risk.type == "unusual_pricing"


def test_cross_quote_pricing_no_flag_when_similar():
    risk = detect_cross_quote_pricing_risk(185.0, [180.0, 190.0, 185.0])
    assert risk is None


def test_cross_quote_pricing_requires_multiple_quotes():
    risk = detect_cross_quote_pricing_risk(180.0, [180.0])
    assert risk is None
