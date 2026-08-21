# SupplyX Backend

FastAPI service for the SupplyX Procurement Decision Intelligence platform.

## Stack

- Python 3.13, FastAPI, Pydantic v2
- MongoDB Atlas via Motor (async)
- Claude API (Anthropic) as primary AI provider, Gemini as optional fallback

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env      # then fill in real values
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`. Interactive docs at `/docs`.

## Structure

```
app/
  api/routes/         # FastAPI routers (thin, no business logic)
  api/dependencies/   # Shared FastAPI dependencies (auth, pagination, ...)
  core/                # config, security, logging
  database/            # Mongo connection + repositories
  models/              # Internal domain models
  schemas/             # Pydantic request/response schemas
  services/            # Business logic, grouped by domain
    ai/                # AI provider abstraction + prompts
    document/           # PDF/Excel extraction
    procurement/ vendor/ rfq/ purchase_order/ inventory/ finance/
  utils/
```

Routes stay thin: they validate input via Pydantic, call a service, and
return a schema. All calculations, scoring, and state transitions live in
`services/`, never in a route handler or in an LLM prompt.

## Environment variables

See [.env.example](.env.example). Never commit a real `.env`.
