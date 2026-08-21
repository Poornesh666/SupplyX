from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.quote_repository import QuoteRepository
from app.database.repositories.vendor_repository import VendorRepository
from app.schemas.quote import NormalizedQuote, QuoteResponse
from app.schemas.risk import Risk
from app.schemas.scoring import ComparisonResponse, ScoringWeights, VendorComparisonEntry
from app.schemas.vendor import VendorResponse
from app.services.procurement import scoring
from app.services.procurement.risk_detection import detect_cross_quote_pricing_risk
from app.services.rfq import rfq_service


class NoExtractedQuotesError(ValueError):
    pass


async def _load_extracted_quotes(db: AsyncIOMotorDatabase, rfq_id: str) -> list[QuoteResponse]:
    quote_repo = QuoteRepository(db)
    docs = await quote_repo.list_extracted_by_rfq(rfq_id)
    return [QuoteResponse.model_validate(doc_to_response_dict(d)) for d in docs]


async def build_comparison(
    db: AsyncIOMotorDatabase, rfq_id: str, weights: ScoringWeights | None = None
) -> ComparisonResponse:
    rfq = await rfq_service.get_rfq(db, rfq_id)
    weights = weights or ScoringWeights()

    quotes = await _load_extracted_quotes(db, rfq_id)
    if not quotes:
        raise NoExtractedQuotesError(f"RFQ '{rfq_id}' has no successfully extracted quotes yet")

    vendor_repo = VendorRepository(db)
    vendor_docs = await vendor_repo.get_many_by_ids([q.vendor_id for q in quotes])
    vendors_by_id = {str(v["_id"]): v for v in vendor_docs}

    unit_prices = [q.normalized.normalized_unit_price for q in quotes if q.normalized]
    min_total = min(q.normalized.calculated_total for q in quotes if q.normalized)

    entries: list[VendorComparisonEntry] = []
    for quote in quotes:
        if quote.normalized is None or quote.extraction is None:
            continue
        vendor_doc = vendors_by_id.get(quote.vendor_id)
        if vendor_doc is None:
            continue
        vendor = VendorResponse.model_validate(doc_to_response_dict(vendor_doc))

        risks: list[Risk] = list(quote.risks)
        pricing_risk = detect_cross_quote_pricing_risk(
            quote.normalized.normalized_unit_price, unit_prices
        )
        if pricing_risk is not None:
            risks.append(pricing_risk)

        score = scoring.compute_score(
            calculated_total=quote.normalized.calculated_total,
            min_total_across_quotes=min_total,
            delivery_days=quote.extraction.delivery_days,
            allowed_delivery_days=rfq.allowed_delivery_days,
            payment_terms_present=bool(quote.extraction.payment_terms),
            vendor=vendor,
            risks=risks,
            weights=weights,
        )

        entries.append(
            VendorComparisonEntry(
                vendor_id=vendor.id,
                vendor_name=vendor.company,
                quote_id=quote.id,
                calculated_total=quote.normalized.calculated_total,
                delivery_days=quote.extraction.delivery_days,
                score=score,
                total_score=score.total,
                rank=0,
                risks=risks,
            )
        )

    entries.sort(key=lambda e: e.total_score, reverse=True)
    for index, entry in enumerate(entries, start=1):
        entry.rank = index

    lowest_price_vendor_id = None
    if entries:
        lowest_price_vendor_id = min(entries, key=lambda e: e.calculated_total).vendor_id
        await rfq_service.advance_status(db, rfq_id, "analysis_complete")

    return ComparisonResponse(
        rfq_id=rfq.id,
        weights=weights,
        entries=entries,
        lowest_price_vendor_id=lowest_price_vendor_id,
        recommended_vendor_id=entries[0].vendor_id if entries else None,
    )
