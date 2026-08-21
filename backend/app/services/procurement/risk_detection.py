from datetime import date, datetime, timedelta
from statistics import median

from app.schemas.extraction import QuoteExtraction
from app.schemas.quote import NormalizedQuote
from app.schemas.risk import Risk

LONG_DELIVERY_ABSOLUTE_DAYS = 30
UNUSUAL_PRICE_DEVIATION_RATIO = 0.5
SUSPICIOUS_EXCLUSION_KEYWORDS = [
    "no warranty",
    "no returns",
    "as-is",
    "as is",
    "final sale",
    "excludes tax",
    "excludes shipping",
    "non-refundable",
]


def _rule_long_delivery(extraction: QuoteExtraction) -> Risk | None:
    if extraction.delivery_days is not None and extraction.delivery_days > LONG_DELIVERY_ABSOLUTE_DAYS:
        return Risk(
            type="long_delivery_time",
            severity="medium",
            description=f"Delivery time of {extraction.delivery_days} days is unusually long.",
            source="deterministic",
            affected_field="delivery_days",
        )
    return None


def _rule_delivery_exceeds_deadline(
    extraction: QuoteExtraction, allowed_delivery_days: int
) -> Risk | None:
    if extraction.delivery_days is not None and extraction.delivery_days > allowed_delivery_days:
        overage = extraction.delivery_days - allowed_delivery_days
        return Risk(
            type="delivery_exceeds_deadline",
            severity="high",
            description=(
                f"Vendor delivery ({extraction.delivery_days} days) exceeds the RFQ "
                f"deadline ({allowed_delivery_days} days) by {overage} days."
            ),
            source="deterministic",
            affected_field="delivery_days",
        )
    return None


def _rule_quote_expiration(
    extraction: QuoteExtraction, required_delivery_date: date
) -> Risk | None:
    if extraction.validity_days is None:
        return Risk(
            type="quote_expiration_unknown",
            severity="low",
            description="Quote validity period was not specified.",
            source="deterministic",
            affected_field="validity_days",
        )
    if extraction.quote_date:
        try:
            quote_date = datetime.fromisoformat(extraction.quote_date).date()
        except ValueError:
            return None
        expiry = quote_date + timedelta(days=extraction.validity_days)
        if expiry < required_delivery_date:
            return Risk(
                type="quote_expires_before_delivery",
                severity="medium",
                description=(
                    f"Quote expires {expiry.isoformat()}, before the required "
                    f"delivery date {required_delivery_date.isoformat()}."
                ),
                source="deterministic",
                affected_field="validity_days",
            )
    return None


def _rule_missing_warranty(extraction: QuoteExtraction) -> Risk | None:
    if not extraction.warranty:
        return Risk(
            type="missing_warranty",
            severity="medium",
            description="Warranty information was not provided.",
            source="deterministic",
            affected_field="warranty",
        )
    return None


def _rule_missing_payment_terms(extraction: QuoteExtraction) -> Risk | None:
    if not extraction.payment_terms:
        return Risk(
            type="missing_payment_terms",
            severity="medium",
            description="Payment terms were not provided.",
            source="deterministic",
            affected_field="payment_terms",
        )
    return None


def _rule_missing_mandatory_fields(extraction: QuoteExtraction) -> list[Risk]:
    risks: list[Risk] = []
    if not extraction.items:
        risks.append(
            Risk(
                type="missing_line_items",
                severity="high",
                description="No line items could be extracted from the quote.",
                source="deterministic",
                affected_field="items",
            )
        )
    if not extraction.quote_number:
        risks.append(
            Risk(
                type="missing_quote_number",
                severity="low",
                description="Quote number was not provided.",
                source="deterministic",
                affected_field="quote_number",
            )
        )
    if extraction.delivery_days is None:
        risks.append(
            Risk(
                type="missing_delivery_time",
                severity="medium",
                description="Delivery time was not stated.",
                source="deterministic",
                affected_field="delivery_days",
            )
        )
    return risks


def _rule_inconsistent_totals(normalized: NormalizedQuote) -> Risk | None:
    if not normalized.total_matches_document:
        return Risk(
            type="inconsistent_totals",
            severity="high",
            description=(
                f"Document states a total of {normalized.document_total}, but line "
                f"items sum to {normalized.calculated_total} — figures don't reconcile."
            ),
            source="deterministic",
            affected_field="total",
        )
    return None


def _rule_moq_exceeds_quantity(extraction: QuoteExtraction, rfq_quantity: float) -> Risk | None:
    if extraction.moq is not None and extraction.moq > rfq_quantity:
        return Risk(
            type="moq_exceeds_rfq_quantity",
            severity="high",
            description=(
                f"Vendor's minimum order quantity ({extraction.moq}) exceeds the "
                f"RFQ quantity ({rfq_quantity})."
            ),
            source="deterministic",
            affected_field="moq",
        )
    return None


def _rule_suspicious_exclusions(extraction: QuoteExtraction) -> list[Risk]:
    risks: list[Risk] = []
    for exclusion in extraction.exclusions:
        lowered = exclusion.lower()
        if any(keyword in lowered for keyword in SUSPICIOUS_EXCLUSION_KEYWORDS):
            risks.append(
                Risk(
                    type="suspicious_exclusion",
                    severity="medium",
                    description=f"Exclusion clause may disadvantage the buyer: \"{exclusion}\".",
                    source="deterministic",
                    affected_field="exclusions",
                )
            )
    return risks


def detect_quote_risks(
    extraction: QuoteExtraction,
    normalized: NormalizedQuote,
    rfq_quantity: float,
    allowed_delivery_days: int,
    required_delivery_date: date,
) -> list[Risk]:
    """Deterministic risk rules for a single quote (rules 1-5, 7-10). Rule 6
    (unusual pricing) is cross-quote and lives in detect_cross_quote_risks."""
    risks: list[Risk] = []

    for maybe_risk in (
        _rule_long_delivery(extraction),
        _rule_delivery_exceeds_deadline(extraction, allowed_delivery_days),
        _rule_quote_expiration(extraction, required_delivery_date),
        _rule_missing_warranty(extraction),
        _rule_missing_payment_terms(extraction),
        _rule_inconsistent_totals(normalized),
        _rule_moq_exceeds_quantity(extraction, rfq_quantity),
    ):
        if maybe_risk is not None:
            risks.append(maybe_risk)

    risks.extend(_rule_missing_mandatory_fields(extraction))
    risks.extend(_rule_suspicious_exclusions(extraction))

    for note in extraction.risks:
        risks.append(
            Risk(
                type="ai_identified_risk",
                severity="medium",
                description=note,
                source="ai",
                affected_field=None,
            )
        )
    for missing in extraction.missing_information:
        risks.append(
            Risk(
                type="missing_information",
                severity="low",
                description=f"AI noted missing information: {missing}",
                source="ai",
                affected_field=None,
            )
        )

    return risks


def detect_cross_quote_pricing_risk(
    normalized_unit_price: float, all_unit_prices: list[float]
) -> Risk | None:
    """Rule 6: flag a quote whose unit price deviates sharply from the
    median of the other quotes for the same RFQ (either direction)."""
    if len(all_unit_prices) < 2:
        return None
    reference_prices = [p for p in all_unit_prices if p != normalized_unit_price] or all_unit_prices
    reference_median = median(reference_prices)
    if reference_median == 0:
        return None
    deviation = abs(normalized_unit_price - reference_median) / reference_median
    if deviation > UNUSUAL_PRICE_DEVIATION_RATIO:
        direction = "higher" if normalized_unit_price > reference_median else "lower"
        return Risk(
            type="unusual_pricing",
            severity="medium",
            description=(
                f"Unit price is {deviation * 100:.0f}% {direction} than other vendors' "
                f"median — worth double-checking before awarding."
            ),
            source="deterministic",
            affected_field="unit_price",
        )
    return None
