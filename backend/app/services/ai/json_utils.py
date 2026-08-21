import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_response(raw_text: str) -> dict:
    """Best-effort cleanup of an LLM's JSON response (strips markdown code
    fences some models add despite instructions) before parsing. Raises
    json.JSONDecodeError on genuinely malformed output — callers decide
    whether to retry."""
    cleaned = _FENCE_RE.sub("", raw_text.strip()).strip()
    return json.loads(cleaned)
