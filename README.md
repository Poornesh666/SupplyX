# SupplyX

AI-powered Procurement ERP and Procurement Decision Intelligence platform, built for AION 2026.

Core flow: **RFQ → Quote Analysis → Vendor Selection → Approval → Purchase Order → Inventory → Finance**

The core product is an **AI Procurement Decision Engine** that turns unstructured vendor
quotes into structured data, normalizes and compares them, detects risk, and produces
an explainable, deterministically-scored vendor recommendation. See [CLAUDE.md](CLAUDE.md)
for the full engineering rules, including the AI/application boundary.

## Project layout

```
frontend/   Next.js + TypeScript + Tailwind + shadcn/ui
backend/    FastAPI + Pydantic + Motor (MongoDB)
docs/       Architecture, API, AI, and demo documentation
scripts/    Dev/ops helper scripts
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- A MongoDB instance (local, or MongoDB Atlas)

## Quick start

**Backend** (from `backend/`):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000` (docs at `/docs`).

**Frontend** (from `frontend/`):

```bash
npm install
copy .env.example .env.local
npm run dev
```

Runs on `http://localhost:3000` and calls the backend at
`NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000/api/v1`).

## Status

Foundation stage: project scaffolding, health check, and frontend↔backend
connectivity are verified. See [docs/architecture](docs/architecture) for
decisions and next steps.
