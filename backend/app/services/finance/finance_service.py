from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.schemas.finance import FinanceSummary, FinanceTransaction, FinanceTransactionStatus

_STATUS_MAP: dict[str, FinanceTransactionStatus] = {
    "draft": "pending",
    "issued": "pending",
    "acknowledged": "approved",
    "received": "paid",
}


async def _non_cancelled_purchase_orders(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
    cursor = db.purchase_orders.find({"status": {"$ne": "cancelled"}}).sort("created_at", -1)
    return await cursor.to_list(length=None)


def _to_transaction(po: dict[str, Any]) -> FinanceTransaction:
    doc = doc_to_response_dict(po)
    return FinanceTransaction(
        id=doc["id"],
        po_id=doc["id"],
        po_number=doc["po_number"],
        vendor_id=doc["vendor_id"],
        vendor_name=doc["vendor_name"],
        amount=doc["total"],
        transaction_type="po_commitment",
        status=_STATUS_MAP.get(doc["status"], "pending"),
        created_at=doc["created_at"],
    )


async def list_finance_transactions(db: AsyncIOMotorDatabase) -> list[FinanceTransaction]:
    pos = await _non_cancelled_purchase_orders(db)
    return [_to_transaction(po) for po in pos]


async def get_finance_summary(db: AsyncIOMotorDatabase) -> FinanceSummary:
    transactions = await list_finance_transactions(db)

    total = sum(t.amount for t in transactions)
    pending = sum(t.amount for t in transactions if t.status == "pending")
    paid = sum(t.amount for t in transactions if t.status == "paid")
    committed = sum(t.amount for t in transactions if t.status == "approved")

    return FinanceSummary(
        total_procurement_spend=total,
        pending_payments=pending,
        paid_amount=paid,
        committed_spend=committed,
    )
