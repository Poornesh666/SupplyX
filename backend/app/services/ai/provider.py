from abc import ABC, abstractmethod

from app.schemas.extraction import QuoteExtraction
from app.schemas.recommendation import RecommendationExplanation


class AIProviderError(Exception):
    """Raised when a provider fails to produce a usable, validated result
    after its retry budget is exhausted. Callers must treat this as a hard
    failure — never fall back to inventing data."""


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def extract_quote(self, document_text: str) -> QuoteExtraction: ...

    @abstractmethod
    async def explain_recommendation(self, facts: dict) -> RecommendationExplanation: ...
