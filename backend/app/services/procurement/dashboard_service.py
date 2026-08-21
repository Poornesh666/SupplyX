from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.dashboard import DashboardMetrics

_INACTIVE_RFQ_STATUSES = ("po_issued", "rejected")


async def build_dashboard_metrics(db: AsyncIOMotorDatabase) -> DashboardMetrics:
    """Compute live dashboard metrics via direct Mongo queries.

    Deliberately simple counts/loops (no aggregation pipelines needed at
    hackathon data scale) -- see app/api/routes/dashboard.py for the field
    definitions this implements.
    """
    active_rfqs = await db.rfqs.count_documents(
        {"status": {"$nin": list(_INACTIVE_RFQ_STATUSES)}}
    )

    quotes_analyzed = await db.quotes.count_documents({"status": "extracted"})

    risks_detected = 0
    cursor = db.quotes.find({"status": "extracted"}, {"risks": 1})
    async for quote in cursor:
        risks_detected += len(quote.get("risks") or [])

    potential_savings = 0.0
    decisions_cursor = db.procurement_decisions.find(
        {"potential_savings": {"$ne": None}}, {"potential_savings": 1}
    )
    async for decision in decisions_cursor:
        value = decision.get("potential_savings")
        if value is not None:
            potential_savings += value

    pending_approvals = await db.rfqs.count_documents({"status": "recommendation_ready"})

    return DashboardMetrics(
        active_rfqs=active_rfqs,
        quotes_analyzed=quotes_analyzed,
        risks_detected=risks_detected,
        potential_savings=round(potential_savings, 2),
        pending_approvals=pending_approvals,
    )
