# Foundation architecture decisions

## Stack choices

- **Frontend**: Next.js (App Router) + TypeScript + Tailwind v4 + shadcn/ui.
  shadcn was initialized with the neutral/slate base color to match the
  "professional, trustworthy" enterprise UX principle — no default purple/blue
  SaaS gradient look.
- **Backend**: FastAPI + Pydantic v2, async throughout via Motor for MongoDB.
- **AI provider abstraction**: lives under `backend/app/services/ai/` (not yet
  implemented). Claude is primary, Gemini is an optional fallback, selected
  behind a common interface so routes/services never call a vendor SDK directly.
- **Auth**: JWT (PyJWT) + bcrypt password hashing (passlib), issued by the
  backend. Kept intentionally simple for the hackathon timeline — no OAuth,
  no session store, no refresh-token rotation.

## Layering rule (backend)

`routes → schemas → services → repositories → database`

Route handlers only validate input (via Pydantic schemas) and call a service.
All calculations, scoring, ranking, and state transitions live in
`services/`, per the AI/application boundary in the root CLAUDE.md — the LLM
never computes a final score or financial total.

## What's built in the foundation pass

- Repo skeleton (`frontend/`, `backend/`, `docs/`, `scripts/`) per the agreed
  project structure.
- FastAPI app with CORS, a Mongo connection lifecycle (connect on startup,
  close on shutdown), and `GET /api/v1/health` reporting app + DB status.
- Next.js shell: sidebar navigation (Dashboard, Procurement, RFQs, Quotes,
  Vendors, Purchase Orders, Inventory, Finance, Analytics), topbar with a
  live API-connection badge, and a placeholder dashboard.
- Typed frontend API client (`frontend/lib/api.ts`) wrapping `fetch`, plus a
  `useHealth` hook proving frontend → backend connectivity end-to-end.
- `.env.example` for both apps; local `.env` / `.env.local` created for dev
  only, gitignored.

## Verified

- `uvicorn app.main:app` boots, `/` and `/api/v1/health` return 200.
- Local MongoDB reachable at `mongodb://localhost:27017` (health check
  reports `database_connected: true`); production will point this at
  MongoDB Atlas via `MONGODB_URI`.
- `npm run dev` serves the dashboard; the API-status badge renders
  "API connected" confirming the frontend reached the backend.
- `tsc --noEmit`, `next lint`, and `next build` all pass clean.

## Not yet built (next steps)

Feature implementation has not started. Next, per the hackathon priorities:
RFQ creation → vendor quote upload → AI extraction (`services/document`,
`services/ai`) → normalization → comparison/scoring (`services/procurement`)
→ explainable recommendation → approval → PO generation.
