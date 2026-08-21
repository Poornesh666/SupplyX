# SupplyX — Hackathon State

_Last updated: 2026-08-21_

## Problem statement

AION 2026's brief: build an AI-powered Procurement ERP that automates Vendor Management → RFQ → Quote Processing → Vendor Comparison → Vendor Selection → Purchase Order → Inventory → Finance → Dashboard, with the MVP focus explicitly recommended on **RFQ → Quote Analysis → Vendor Selection**.

## Solution

SupplyX is an **AI Procurement Decision Engine**, not a CRUD ERP. It turns unstructured vendor PDF/XLSX/CSV quotes into structured data, normalizes them, detects risk, scores vendors deterministically, and produces an explainable AI-narrated recommendation — with a human required to approve before anything becomes a Purchase Order. The core positioning: **AI-assisted, data-driven, human-controlled** — SupplyX never lets the AI silently decide a score or a total.

## Architecture

```
frontend/   Next.js 16 (App Router, Turbopack) + TypeScript + Tailwind v4 + shadcn/ui
backend/    FastAPI + Pydantic v2 + Motor (async MongoDB)
database/   MongoDB (local dev; Atlas-ready via MONGODB_URI)
AI/         Google Gemini (gemini-3.6-flash), Claude provider also implemented and
            swappable via the same AIProvider interface
```

Backend layering: `routes → schemas → services → repositories → database`. Routes are thin; all business logic (scoring, risk rules, state transitions) lives in `services/`. Every collection has its own repository class wrapping Motor.

**MongoDB collections**: `rfqs`, `vendors`, `quotes`, `procurement_decisions`, `approvals`, `purchase_orders`, `inventory`, `finance` (derived live from `purchase_orders`, not a separate synced collection), `audit_logs`.

### The AI/deterministic boundary (the core engineering principle)

| | LLM does | Python does |
|---|---|---|
| Extraction | Reads a quote document, returns structured JSON facts | Validates every field against a Pydantic schema; retries once on malformed JSON, then fails loudly — never invents values |
| Totals | Reports whatever the document states | Independently recomputes `subtotal`/`total` from line items; if it disagrees with the document's stated total, that's a deterministic **inconsistent_totals** risk flag |
| Risk | May note semantic risks in free text | 10 deterministic rule functions (delivery deadline, MOQ, missing fields, unusual pricing, suspicious exclusions, etc.) run regardless of what the AI said |
| Scoring | Never touches scores | `VendorScoringService` — 6 pure functions (price/delivery/quality/reliability/payment/risk), weights validated to sum to 100, 100% deterministic and unit-tested |
| Recommendation | Explains *why* the Python-decided winner won, in plain language | Decides the winner and the ranking; the AI is given the facts as fixed and told explicitly it cannot alter them |
| Insights | Not used at all | `insights_service.py` derives every "AI Insight" card straight from stored data — no LLM call in this path |

### Deterministic scoring formula

Default weights (configurable, must sum to 100): Price 30 / Delivery 20 / Quality 15 / Reliability 15 / Payment 10 / Risk 10.

- **Price**: `weight × (min_total / this_total)` — cheapest gets full marks, others scaled down.
- **Delivery**: `weight × min(allowed_days / quoted_days, 1)` — capped at full marks for on-time-or-better, penalized proportionally for late.
- **Quality / Reliability / Payment**: `weight × (vendor_baseline_score / 100)`, with a further penalty on Payment if the quote is missing payment terms.
- **Risk**: starts at full weight, `-4` per high-severity risk, `-2` per medium, `-1` per low, floored at 0.

### Risk engine (10 deterministic rules + AI-surfaced semantic risks)

`risk_detection.py`: long delivery time, delivery-exceeds-deadline, quote expiration, missing warranty, missing payment terms, missing mandatory fields, unusual pricing (cross-quote), inconsistent totals, MOQ exceeds RFQ quantity, suspicious exclusion clauses — plus the AI's own free-text risk notes and "missing information" observations, carried through with `source: "ai"` so the UI can distinguish them from `source: "deterministic"` ones.

### What-If simulator

`POST /api/v1/rfqs/{id}/what-if` — a thin wrapper that reuses `comparison_service.build_comparison()` with caller-supplied weights instead of the defaults. Nothing is persisted; it's a pure recompute for simulation. The frontend shows current vs. simulated rank/score side by side with a rank-change indicator per vendor.

### Approval → Purchase Order → Inventory → Finance

- **Approval**: `POST /api/v1/rfqs/{id}/approval` — approves/rejects the system's *current* recommendation (no vendor override, keeps the audit trail unambiguous). Records approver, timestamp, optional note.
- **Purchase Order**: `POST /api/v1/purchase-orders` — builds line items/totals from the approved vendor's already-normalized quote (never re-derives numbers from scratch). Lifecycle: `draft → issued → acknowledged → received`, with `cancelled` from `draft` or `issued`. Every transition is validated against an explicit legal-transition map.
- **Inventory**: `POST /api/v1/inventory/receive` — walks the PO through `issued/acknowledged → received` and upserts stock by SKU.
- **Finance**: derived live from the `purchase_orders` collection (draft/issued → pending, acknowledged → approved, received → paid) — no separate ledger to keep in sync, so it can never drift from the real PO state.

### Audit trail

Every state-changing action calls `audit_service.record_event()`. Real events, not simulated: `rfq_created, quote_analyzed, quote_extraction_failed, risk_detected, recommendation_generated, rfq_approved, rfq_rejected, po_created, po_issued, po_acknowledged, po_received, po_cancelled, inventory_received, finance_transaction_created`. Exposed at `GET /api/v1/rfqs/{id}/audit-trail`, rendered as a vertical timeline on the RFQ detail page.

### AI Procurement Insights

`GET /api/v1/insights[?rfq_id=]` — derives factual observations purely from stored data (quotations analyzed, high-severity risk count, delivery-risk count, price variance across quotes, missing warranty/payment terms count, potential savings, strongest vendor across RFQs). No LLM call in this path; insights with insufficient data are skipped rather than faked.

### Frontend

Floating collapsible nav rail (grouped: Workspace / Supply / Insights) replacing a conventional sidebar; Instrument Serif for editorial headlines + Geist Sans/Mono for UI; a cyan "intelligence" accent token reserved for AI-touched moments; a lazy-loaded Three.js procurement node-graph on the dashboard hero (WebGL-fallback + reduced-motion aware); a "Live Procurement Pipeline" showing real per-stage RFQ counts; framer-motion throughout (count-up numbers, staggered reveals, workflow-timeline transitions). Dark and light themes both fully designed (not just inverted).

## Test results

- **Backend**: 90/90 `pytest` passing (scoring, all 10 risk rules, normalization, document extraction, RFQ/vendor/quote/approval/PO/inventory/finance/what-if/dashboard/insights APIs, full-lifecycle regression tests).
- **Frontend**: `tsc --noEmit` clean, `next lint` 0 errors, `next build` succeeds — 13 routes.
- **Live verification**: the full pipeline (upload → real Gemini extraction ×3 → comparison → real Gemini recommendation → approve → PO create → issue → acknowledge → receive → inventory → finance → dashboard → analytics → audit trail) has been driven end-to-end against the running app, not just unit-tested.

## Known limitations

- No authentication — approver identity is a free-text field, by design, to keep the hackathon scope tight.
- Analytics' risk-severity chart does a client-side fan-out over each RFQ's quotes rather than one backend aggregation endpoint — fine at demo data scale.
- Finance is a live *view* over Purchase Orders, not an independent ledger — intentional (can't drift out of sync), but means there's no standalone payment/refund recording flow beyond what a PO's status implies.
- Nothing in this repository has been committed to git this session — everything is on disk, uncommitted, pending an explicit request.

## Judge talking points

1. **The core differentiator isn't "we called an LLM"** — it's the strict separation: AI extracts and explains, Python calculates and decides. Ask to see `risk_detection.py` or `scoring.py` — zero AI calls in either.
2. **The demo's central proof point**: the cheapest vendor (Nova, ~19% cheaper) loses because its risk and delivery scores drag it down — show the comparison page's callout that says so explicitly, in numbers.
3. **Every decision is traceable**: open the Activity timeline on the RFQ and show the unbroken chain from quote upload to inventory receipt, each with a real timestamp.
4. **Nothing here is fabricated**: every dashboard number, every insight card, every finance total is a live query against MongoDB — there is no hardcoded demo number anywhere in the UI layer.
