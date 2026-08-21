from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    active_rfqs: int
    quotes_analyzed: int
    risks_detected: int
    potential_savings: float
    pending_approvals: int
