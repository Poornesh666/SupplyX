from fastapi import APIRouter

from app.core.config import get_settings
from app.database.connection import database
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    db_connected = False
    if database.client is not None:
        try:
            await database.client.admin.command("ping")
            db_connected = True
        except Exception:
            db_connected = False

    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.environment,
        database_connected=db_connected,
    )
