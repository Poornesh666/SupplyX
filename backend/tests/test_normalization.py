from app.schemas.extraction import ExtractedItem, QuoteExtraction
from app.services.procurement.normalization import normalize_quote


def _extraction(**overrides) -> QuoteExtraction:
    base = dict(
        items=[ExtractedItem(description="Widget", quantity=500, unit_price=180)],
    )
    base.update(overrides)
    return QuoteExtraction(**base)


def test_calculated_subtotal_and_total_from_items():
    extraction = _extraction(tax=1000, shipping=500, discount=200)
    normalized = normalize_quote(extraction, required_quantity=500)

    assert normalized.calculated_subtotal == 90000
    assert normalized.calculated_total == 90000 - 200 + 1000 + 500


def test_total_matches_document_within_tolerance():
    extraction = _extraction(total=90000.5)
    normalized = normalize_quote(extraction, required_quantity=500)

    assert normalized.total_matches_document is True


def test_inconsistent_total_detected():
    extraction = _extraction(total=120000)
    normalized = normalize_quote(extraction, required_quantity=500)

    assert normalized.total_matches_document is False
    assert normalized.document_total == 120000


def test_no_document_total_is_not_flagged_as_mismatch():
    extraction = _extraction(total=None)
    normalized = normalize_quote(extraction, required_quantity=500)

    assert normalized.total_matches_document is True


def test_normalized_unit_price_divides_by_required_quantity():
    extraction = _extraction()
    normalized = normalize_quote(extraction, required_quantity=500)

    assert normalized.normalized_unit_price == 180.0
