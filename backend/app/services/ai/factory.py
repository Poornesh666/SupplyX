from functools import lru_cache

from app.core.config import get_settings
from app.services.ai.provider import AIProvider


class AIProviderNotConfiguredError(Exception):
    pass


@lru_cache
def get_ai_provider() -> AIProvider:
    """Selects the active AI provider. Gemini is primary for this build;
    Claude is fully implemented and becomes primary automatically once
    ANTHROPIC_API_KEY is set and GEMINI_API_KEY is not — same interface,
    zero call-site changes either way."""
    settings = get_settings()

    if settings.gemini_api_key:
        from app.services.ai.gemini_provider import GeminiProvider

        return GeminiProvider(api_key=settings.gemini_api_key)

    if settings.anthropic_api_key:
        from app.services.ai.claude_provider import ClaudeProvider

        return ClaudeProvider(api_key=settings.anthropic_api_key)

    raise AIProviderNotConfiguredError(
        "No AI provider configured — set GEMINI_API_KEY or ANTHROPIC_API_KEY in backend/.env"
    )
