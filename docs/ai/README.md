# AI design notes

Documents the provider abstraction, prompts, and — most importantly — the
boundary between LLM reasoning and deterministic application logic.

## AI boundary (from CLAUDE.md)

LLMs may: interpret documents, extract structured data, identify risks,
explain decisions, generate natural-language insights.

LLMs must never: invent financial numbers, calculate authoritative totals,
determine a final vendor score, or silently modify procurement records.
All calculations, scoring, ranking, and totals are owned by Python
application logic in `backend/app/services/procurement/`.

## Provider abstraction

`backend/app/services/ai/` will define a single interface (e.g.
`AIProvider.extract_quote(...)`, `AIProvider.explain_recommendation(...)`)
implemented by a Claude client (primary) and a Gemini client (fallback), so
the rest of the app never imports a vendor SDK directly.
