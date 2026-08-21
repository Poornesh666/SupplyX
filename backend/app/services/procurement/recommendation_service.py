from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.repositories.recommendation_repository import RecommendationRepository
from app.schemas.common import utcnow
from app.schemas.recommendation import RecommendationExplanation, RecommendationResponse
from app.schemas.scoring import ComparisonResponse
from app.services.ai.factory import get_ai_provider
from app.services.procurement.comparison_service import NoExtractedQuotesError, build_comparison
from app.services.rfq import rfq_service


class NoQuotesAvailableError(ValueError):
    pass


def _ranking_signature(comparison: ComparisonResponse) -> list[list]:
    return [[e.vendor_id, e.total_score] for e in comparison.entries]


def _build_facts(rfq_title: str, comparison: ComparisonResponse) -> dict:
    winner = comparison.entries[0]
    alternative = comparison.entries[1] if len(comparison.entries) > 1 else None

    def entry_facts(entry):
        return {
            "vendor_name": entry.vendor_name,
            "total_score": entry.total_score,
            "score_breakdown": entry.score.model_dump(),
            "calculated_total": entry.calculated_total,
            "delivery_days": entry.delivery_days,
            "risks": [r.description for r in entry.risks],
        }

    return {
        "rfq_title": rfq_title,
        "scoring_weights": comparison.weights.model_dump(),
        "recommended_vendor": entry_facts(winner),
        "alternative_vendor": entry_facts(alternative) if alternative else None,
        "all_vendors_considered": len(comparison.entries),
    }


def _compute_potential_savings(comparison: ComparisonResponse) -> float | None:
    winner = comparison.entries[0]
    others = comparison.entries[1:]
    if not others:
        return None
    highest_other = max(e.calculated_total for e in others)
    savings = round(highest_other - winner.calculated_total, 2)
    return savings if savings > 0 else None


async def get_or_generate_recommendation(
    db: AsyncIOMotorDatabase, rfq_id: str
) -> RecommendationResponse:
    rfq = await rfq_service.get_rfq(db, rfq_id)

    try:
        comparison = await build_comparison(db, rfq_id)
    except NoExtractedQuotesError as exc:
        raise NoQuotesAvailableError(str(exc)) from exc

    if not comparison.entries:
        raise NoQuotesAvailableError(f"RFQ '{rfq_id}' has no scoreable vendor quotes yet")

    repo = RecommendationRepository(db)
    signature = _ranking_signature(comparison)

    cached = await repo.get_by_rfq(rfq_id)
    if cached is not None and cached.get("ranking_signature") == signature:
        await rfq_service.advance_status(db, rfq_id, "recommendation_ready")
        return RecommendationResponse.model_validate(cached)

    winner = comparison.entries[0]
    alternative = comparison.entries[1] if len(comparison.entries) > 1 else None

    facts = _build_facts(rfq.title, comparison)
    provider = get_ai_provider()
    explanation: RecommendationExplanation = await provider.explain_recommendation(facts)

    response = RecommendationResponse(
        rfq_id=rfq.id,
        recommended_vendor_id=winner.vendor_id,
        recommended_vendor_name=winner.vendor_name,
        recommended_score=winner.total_score,
        alternative_vendor_id=alternative.vendor_id if alternative else None,
        alternative_vendor_name=alternative.vendor_name if alternative else None,
        alternative_score=alternative.total_score if alternative else None,
        potential_savings=_compute_potential_savings(comparison),
        explanation=explanation,
        generated_at=utcnow(),
    )

    document = response.model_dump(mode="json")
    document["ranking_signature"] = signature
    await repo.upsert_for_rfq(rfq_id, document)
    await rfq_service.advance_status(db, rfq_id, "recommendation_ready")

    from app.services.audit.audit_service import record_event

    await record_event(
        db,
        rfq_id,
        "recommendation_generated",
        f"AI recommended {winner.vendor_name} (score {winner.total_score}/100)",
    )

    return response
