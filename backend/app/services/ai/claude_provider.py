import logging

import anthropic
from pydantic import ValidationError

from app.schemas.extraction import QuoteExtraction
from app.schemas.recommendation import RecommendationExplanation
from app.services.ai.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    RECOMMENDATION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
    build_recommendation_user_prompt,
)
from app.services.ai.provider import AIProvider, AIProviderError

logger = logging.getLogger(__name__)

_MODEL_NAME = "claude-sonnet-5"


def _tool_use_input(message: anthropic.types.Message, tool_name: str) -> dict:
    for block in message.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise AIProviderError(f"Claude did not call the required '{tool_name}' tool")


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(self, api_key: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def extract_quote(self, document_text: str) -> QuoteExtraction:
        tool_name = "record_quote_extraction"
        try:
            message = await self._client.messages.create(
                model=_MODEL_NAME,
                max_tokens=4096,
                system=EXTRACTION_SYSTEM_PROMPT,
                tools=[
                    {
                        "name": tool_name,
                        "description": "Record the structured facts extracted from the quote.",
                        "input_schema": QuoteExtraction.model_json_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": tool_name},
                messages=[{"role": "user", "content": build_extraction_user_prompt(document_text)}],
            )
            payload = _tool_use_input(message, tool_name)
            return QuoteExtraction.model_validate(payload)
        except ValidationError as exc:
            raise AIProviderError(f"Claude returned an invalid extraction: {exc}") from exc
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"Claude extraction call failed: {exc}") from exc

    async def explain_recommendation(self, facts: dict) -> RecommendationExplanation:
        tool_name = "record_recommendation_explanation"
        try:
            message = await self._client.messages.create(
                model=_MODEL_NAME,
                max_tokens=2048,
                system=RECOMMENDATION_SYSTEM_PROMPT,
                tools=[
                    {
                        "name": tool_name,
                        "description": "Record the recommendation explanation.",
                        "input_schema": RecommendationExplanation.model_json_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": tool_name},
                messages=[{"role": "user", "content": build_recommendation_user_prompt(facts)}],
            )
            payload = _tool_use_input(message, tool_name)
            return RecommendationExplanation.model_validate(payload)
        except ValidationError as exc:
            raise AIProviderError(f"Claude returned an invalid recommendation: {exc}") from exc
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"Claude recommendation call failed: {exc}") from exc
