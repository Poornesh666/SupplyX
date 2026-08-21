# SupplyX — Hackathon Readiness

_Last updated: 2026-08-21_

## Prerequisites

- MongoDB running locally on `27017` (or set `MONGODB_URI` in `backend/.env` to Atlas)
- `backend/.env` has a real `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY` — the app auto-selects whichever is set, Gemini first)
- Node 20+, Python 3.13+

## How to start

**Backend** (from repo root):

```bash
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Frontend** (separate terminal):

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`. Confirm the topbar shows **"AI Engine Online"** (green, pulsing) — that's a real health check against the backend + MongoDB, not decoration. Backend interactive docs: `http://localhost:8000/docs`.

## Reset demo data to a clean starting state

From `backend/`:

```bash
.venv/Scripts/python.exe ../scripts/seed_demo_data.py
```

This wipes and reseeds `vendors`, `rfqs`, `quotes`, `procurement_decisions`, `approvals`, `purchase_orders`, `inventory`, and `audit_logs`, and creates:

- **3 vendors**: Apex Industrial Supplies (medium risk), Bharat Components Ltd. (low risk), Nova Mechanical Systems (high risk)
- **1 RFQ**: `RFQ-2026-001` — Industrial Bearing Procurement, 500 pcs, 15-day delivery window, all 3 vendors invited

The 3 differentiated demo quote PDFs to upload live in `docs/demo/sample_quotes/` — they are **real PDF files with real extractable text**, not fixtures faked into the database. Uploading them triggers genuine Gemini extraction every time.

## Exact demo flow (~5–7 minutes)

1. **Dashboard** — point out the Live Procurement Pipeline (real per-stage counts), the KPI row, and the AI Insights panel are all live MongoDB queries.
2. **RFQs → RFQ-2026-001** — open the RFQ, show the workflow tracker.
3. **Upload all 3 quote PDFs** from `docs/demo/sample_quotes/` (select vendor, drag-drop or browse) — narrate that each upload triggers a real Gemini call: extraction → Pydantic validation → Python-computed totals → 10-rule deterministic risk engine, live.
4. **Compare vendors** — the score table renders with per-criterion animated bars. Point at the callout: *"Bharat wins despite costing ~19–24% more than Nova — the price difference is outweighed by delivery/quality/reliability/risk."* This is the single most important proof point: cheapest ≠ best, and the app says so in plain numbers, not just narratively.
5. **What-if simulator** — nudge the Price weight up, Quality/Reliability down, hit Simulate. Show the rank/score recompute live and explain it's the exact same deterministic function, just re-run with different inputs — nothing hardcoded per scenario.
6. **AI Recommendation** — the hero screen. Point out the two explicitly-labeled sections: **"Calculated by SupplyX Decision Engine"** (the score, deterministic) vs. **"AI-Generated Explanation"** (the prose, LLM-written, cannot change the number above it).
7. **Approve** — fill approver name, optional note, Approve. The outcome card appears immediately.
8. **Create Purchase Order → Issue** — show the generated PO looks like a real business document (line items, terms, totals) built entirely from the already-normalized quote data, not re-typed.
9. **Inventory → Receive** — select the issued PO, Receive. Stock jumps to 500 units; the PO status flips to `received` automatically.
10. **Finance** — show the Paid Amount now reflects the received PO — this number is a live derived view over Purchase Orders, not a separately-maintained ledger that could drift.
11. **Dashboard again** — metrics have moved (Active RFQs down, Recent POs updated, a new AI Insight or two).
12. **Analytics** — vendor performance table + real risk-severity chart.
13. **Activity timeline** (bottom of the RFQ page) — scroll through the full, real, timestamped chain from `quote_analyzed` through `inventory_received`. This is the traceability closer: *"Every decision in this system is reconstructable after the fact."*
14. (Optional, if asked) **Dark/light toggle** and a resize to mobile width to show responsiveness — both were designed properly, not inverted/afterthought.

## Test results

```
Backend:  90/90 pytest passing
Frontend: tsc --noEmit clean · next lint 0 errors · next build succeeds (13 routes)
```

Everything above was also driven live through the running app end-to-end (not just asserted by tests) as part of closing out this feature sprint, including the newly-added PO lifecycle audit events (`po_acknowledged`, `po_received`, `po_cancelled`) and the risk/price-variance insight types.

## Known limitations (say these proactively if asked, don't wait to be caught out)

- No authentication system — approver name is free text. Deliberate scope cut for the hackathon window.
- No standalone finance ledger — Finance is a live, always-consistent *view* over Purchase Orders rather than an independently-recorded transaction log.
- Analytics' risk chart fans out one request per RFQ client-side rather than using a single aggregation endpoint — acceptable at hackathon data volumes, would need a real aggregation pipeline at scale.
- Nothing has been committed to git this session.

## What could fail during judging, and the fix

| Risk | Mitigation |
|---|---|
| Backend was started before a code change and is serving stale routes | Symptom: a 404 on an endpoint you just saw work in code. Fix: kill the uvicorn process and restart it (it is **not** run with `--reload` in this setup). |
| Gemini API key missing/expired/rate-limited | Quote upload will return `status: "extraction_failed"` with a clear error message in the UI (never a crash) — but the demo needs it working. Verify `backend/.env`'s `GEMINI_API_KEY` before presenting. |
| Demo data left in a mid-workflow state from a rehearsal | Always re-run `seed_demo_data.py` right before presenting. |
| MongoDB not running | Backend health check and the "AI Engine Online" badge will show red/offline immediately — check this first if anything looks broken. |
| Browser tab left open from a previous session showing a stale compiled bundle | Open a fresh tab/hard-reload if any page looks like it's missing an element that should be there — Turbopack HMR occasionally serves a stale client bundle after many rapid navigations. |
| Judges ask "is this real AI or hardcoded" | Show the Network tab during a quote upload — the request to `/quotes/upload` genuinely takes a few seconds (real Gemini latency), and re-uploading the same file produces slightly different AI-written risk phrasing each time (proof it's a live call, not a cached fixture). |
