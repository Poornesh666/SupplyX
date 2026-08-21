from app.schemas.extraction import QuoteExtraction
from app.schemas.quote import NormalizedQuote

TOTAL_MISMATCH_TOLERANCE_RATIO = 0.01
TOTAL_MISMATCH_MIN_ABSOLUTE = 1.0


def normalize_quote(extraction: QuoteExtraction, required_quantity: float) -> NormalizedQuote:
    """Pure, deterministic arithmetic over AI-extracted facts. The AI never
    computes these values — Python does, every time, the same way."""
    calculated_subtotal = sum(item.quantity * item.unit_price for item in extraction.items)
    calculated_total = (
        calculated_subtotal
        - (extraction.discount or 0)
        + (extraction.tax or 0)
        + (extraction.shipping or 0)
    )

    document_total = extraction.total
    if document_total is None:
        total_matches_document = True
    else:
        tolerance = max(
            TOTAL_MISMATCH_MIN_ABSOLUTE, calculated_total * TOTAL_MISMATCH_TOLERANCE_RATIO
        )
        total_matches_document = abs(document_total - calculated_total) <= tolerance

    normalized_unit_price = (
        calculated_subtotal / required_quantity if required_quantity else 0.0
    )

    return NormalizedQuote(
        calculated_subtotal=round(calculated_subtotal, 2),
        calculated_total=round(calculated_total, 2),
        document_total=document_total,
        total_matches_document=total_matches_document,
        normalized_unit_price=round(normalized_unit_price, 4),
    )
