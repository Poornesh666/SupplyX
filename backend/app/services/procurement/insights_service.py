from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.insights import ProcurementInsight


async def build_insights(
    db: AsyncIOMotorDatabase, rfq_id: str | None = None
) -> list[ProcurementInsight]:
    """Derive factual procurement insights purely from stored data.

    No AI call is involved -- these are deterministic summaries of what is
    already in Mongo (risks, missing quote fields, recommendation savings/
    scores). If there isn't enough data for a given insight it is skipped
    rather than emitting a placeholder.
    """
    insights: list[ProcurementInsight] = []

    quote_filter: dict = {"status": "extracted"}
    if rfq_id:
        quote_filter["rfq_id"] = rfq_id

    quotes_analyzed = 0
    high_risk_quotes = 0
    missing_terms_quotes = 0
    delivery_risk_quotes = 0
    unit_prices: list[float] = []
    cursor = db.quotes.find(quote_filter, {"risks": 1, "extraction": 1, "normalized": 1})
    async for quote in cursor:
        quotes_analyzed += 1
        risks = quote.get("risks") or []
        if any(r.get("severity") == "high" for r in risks):
            high_risk_quotes += 1
        if any(r.get("type") in ("delivery_exceeds_deadline", "long_delivery_time") for r in risks):
            delivery_risk_quotes += 1

        extraction = quote.get("extraction") or {}
        if not extraction.get("warranty") or not extraction.get("payment_terms"):
            missing_terms_quotes += 1

        normalized = quote.get("normalized") or {}
        price = normalized.get("normalized_unit_price")
        if price:
            unit_prices.append(price)

    if quotes_analyzed > 0:
        noun = "quotation" if quotes_analyzed == 1 else "quotations"
        insights.append(
            ProcurementInsight(
                id="general-quotes-analyzed",
                rfq_id=rfq_id,
                summary=f"{quotes_analyzed} {noun} analyzed",
                category="general",
            )
        )

    if delivery_risk_quotes > 0:
        noun = "quotation" if delivery_risk_quotes == 1 else "quotations"
        verb = "shows" if delivery_risk_quotes == 1 else "show"
        insights.append(
            ProcurementInsight(
                id="risk-delivery",
                rfq_id=rfq_id,
                summary=f"{delivery_risk_quotes} {noun} {verb} a delivery-risk indicator",
                category="risk",
            )
        )

    if len(unit_prices) > 1:
        spread = (max(unit_prices) - min(unit_prices)) / min(unit_prices)
        if spread > 0.15:
            insights.append(
                ProcurementInsight(
                    id="quality-price-variance",
                    rfq_id=rfq_id,
                    summary=f"Unit prices vary by {spread * 100:.0f}% across quotes — worth reviewing before award",
                    category="quality",
                )
            )

    if high_risk_quotes > 0:
        noun = "quotation" if high_risk_quotes == 1 else "quotations"
        verb = "contains" if high_risk_quotes == 1 else "contain"
        insights.append(
            ProcurementInsight(
                id="risk-high-severity",
                rfq_id=rfq_id,
                summary=f"{high_risk_quotes} {noun} {verb} high-severity risk",
                category="risk",
            )
        )

    if missing_terms_quotes > 0:
        noun = "quotation is" if missing_terms_quotes == 1 else "quotations are"
        insights.append(
            ProcurementInsight(
                id="quality-missing-terms",
                rfq_id=rfq_id,
                summary=f"{missing_terms_quotes} {noun} missing warranty or payment terms information",
                category="quality",
            )
        )

    decision_filter: dict = {}
    if rfq_id:
        decision_filter["rfq_id"] = rfq_id

    total_savings = 0.0
    decisions: list[dict] = []
    cursor = db.procurement_decisions.find(decision_filter)
    async for decision in cursor:
        decisions.append(decision)
        savings = decision.get("potential_savings")
        if savings is not None:
            total_savings += savings

    if total_savings > 0:
        insights.append(
            ProcurementInsight(
                id="savings-total",
                rfq_id=rfq_id,
                summary=f"{total_savings:,.0f} potential savings identified across recommendations",
                category="savings",
            )
        )

    # Only meaningful across multiple RFQs, and only for the global view.
    if rfq_id is None and len(decisions) > 1:
        scores_by_vendor: dict[str, list[float]] = {}
        names_by_vendor: dict[str, str] = {}
        for decision in decisions:
            vendor_id = decision.get("recommended_vendor_id")
            score = decision.get("recommended_score")
            if vendor_id is None or score is None:
                continue
            scores_by_vendor.setdefault(vendor_id, []).append(score)
            names_by_vendor[vendor_id] = decision.get("recommended_vendor_name", vendor_id)

        if scores_by_vendor:
            best_vendor_id = max(
                scores_by_vendor,
                key=lambda vid: sum(scores_by_vendor[vid]) / len(scores_by_vendor[vid]),
            )
            insights.append(
                ProcurementInsight(
                    id="general-best-vendor",
                    rfq_id=None,
                    summary=(
                        f"{names_by_vendor[best_vendor_id]} offers the strongest "
                        "risk-adjusted value across recommendations"
                    ),
                    category="general",
                )
            )

    return insights
