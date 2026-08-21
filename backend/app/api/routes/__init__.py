from fastapi import APIRouter

from app.api.routes.approvals import router as approvals_router
from app.api.routes.audit import router as audit_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.finance import router as finance_router
from app.api.routes.health import router as health_router
from app.api.routes.insights import router as insights_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.purchase_orders import router as purchase_orders_router
from app.api.routes.quotes import router as quotes_router
from app.api.routes.rfqs import router as rfqs_router
from app.api.routes.vendors import router as vendors_router
from app.api.routes.what_if import router as what_if_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(rfqs_router)
api_router.include_router(vendors_router)
api_router.include_router(quotes_router)
api_router.include_router(approvals_router)
api_router.include_router(purchase_orders_router)
api_router.include_router(what_if_router)
api_router.include_router(dashboard_router)
api_router.include_router(audit_router)
api_router.include_router(insights_router)
api_router.include_router(inventory_router)
api_router.include_router(finance_router)
