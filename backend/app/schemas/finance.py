from datetime import datetime
from typing import Literal

from pydantic import BaseModel

FinanceTransactionType = Literal["po_commitment", "payment", "refund"]
FinanceTransactionStatus = Literal["pending", "approved", "paid"]


class FinanceTransaction(BaseModel):
    id: str
    po_id: str
    po_number: str
    vendor_id: str
    vendor_name: str
    amount: float
    transaction_type: FinanceTransactionType
    status: FinanceTransactionStatus
    created_at: datetime


class FinanceTransactionListResponse(BaseModel):
    items: list[FinanceTransaction]


class FinanceSummary(BaseModel):
    total_procurement_spend: float
    pending_payments: float
    paid_amount: float
    committed_spend: float
