import logging

import google.generativeai as genai
from pydantic import ValidationError

from app.schemas.extraction import QuoteExtraction
from app.schemas.recommendation import RecommendationExplanation
from app.services.ai.json_utils import parse_json_response
from app.services.ai.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    RECOMMENDATION_SYSTEM_PROMPT,
    build_extraction_retry_prompt,
    build_extraction_user_prompt,
    build_recommendation_user_prompt,
)
from app.services.ai.provider import AIProvider, AIProviderError

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-3.6-flash"


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)

    def _model(self, system_prompt: str) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name=_MODEL_NAME,
            system_instruction=system_prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        )

    async def extract_quote(self, document_text: str) -> QuoteExtraction:
        model = self._model(EXTRACTION_SYSTEM_PROMPT)
        prompt = build_extraction_user_prompt(document_text)

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = await model.generate_content_async(prompt)
                payload = parse_json_response(response.text)
                return QuoteExtraction.model_validate(payload)
            except (ValueError, ValidationError) as exc:
                last_error = exc
                logger.warning("Gemini extraction attempt %d failed: %s", attempt + 1, exc)
                prompt = build_extraction_retry_prompt(document_text, str(exc))
            except Exception as exc:
                raise AIProviderError(f"Gemini extraction call failed: {exc}") from exc

        raise AIProviderError(
            f"Gemini returned an unparseable/invalid extraction after retry: {last_error}"
        )

    async def explain_recommendation(self, facts: dict) -> RecommendationExplanation:
        model = self._model(RECOMMENDATION_SYSTEM_PROMPT)
        prompt = build_recommendation_user_prompt(facts)

        try:
            response = await model.generate_content_async(prompt)
            payload = parse_json_response(response.text)
            return RecommendationExplanation.model_validate(payload)
        except (ValueError, ValidationError) as exc:
            raise AIProviderError(f"Gemini returned an invalid recommendation: {exc}") from exc
        except Exception as exc:
            raise AIProviderError(f"Gemini recommendation call failed: {exc}") from exc
