# ProcureAI — Claude Development Rules

## Project

ProcureAI is an AI-powered Procurement ERP and Procurement Decision Intelligence platform built for AION 2026.

## Mission

Build a functional, polished prototype demonstrating:

RFQ
→ Quote Analysis
→ Vendor Selection
→ Approval
→ Purchase Order
→ Inventory
→ Finance

## Technology

Frontend:
Next.js + TypeScript + Tailwind + shadcn/ui

Backend:
Python + FastAPI + Pydantic

Database:
MongoDB Atlas

AI:
Claude API with provider abstraction

Document Processing:
Python PDF/Excel processing libraries

## Core Innovation

The core product is an AI Procurement Decision Engine.

It must:

* understand vendor quotations
* extract structured information
* normalize quotation data
* detect risks
* compare vendors
* calculate deterministic scores
* explain recommendations
* support dynamic procurement priorities

## AI Boundary

LLMs MAY:

* interpret documents
* extract information
* identify risks
* explain decisions
* generate natural-language insights

LLMs MUST NOT:

* invent financial numbers
* calculate authoritative totals
* determine final scores without application logic
* silently modify procurement records

Python application logic owns:

* calculations
* validation
* scoring
* ranking
* totals
* business rules
* state transitions

## Development Method

Always follow:

INSPECT
→ PLAN
→ IMPLEMENT
→ TEST
→ VERIFY

Never blindly modify large portions of the codebase.

Before major changes:

* inspect related files
* identify dependencies
* explain intended changes

After changes:

* run relevant tests
* run lint/typecheck
* verify runtime behavior
* fix errors

## Code Quality

Prefer:

* simple code
* readable code
* typed code
* reusable components
* small services
* explicit interfaces
* proper validation
* predictable error handling

Avoid:

* premature abstraction
* unnecessary dependencies
* duplicated logic
* magic numbers
* hardcoded secrets
* massive files
* giant components
* unrelated refactoring

## Frontend

Use reusable components.

Every important UI state must support:

* loading
* success
* empty
* error

Forms must validate input.

Tables must handle empty states.

AI processing must have clear visual states.

## Backend

Use:

routes
→ schemas
→ services
→ repositories
→ database

Keep business logic out of route handlers.

## API

All APIs should be under:

/api/v1/

Use proper HTTP status codes.

Return predictable JSON.

Validate external input.

## Database

Never directly scatter database queries throughout routes.

Use a repository/data-access layer where useful.

## Security

Never commit:

* API keys
* passwords
* JWT secrets
* MongoDB credentials

Use environment variables.

Validate uploaded files.

Restrict upload types and sizes.

## Procurement

A procurement decision must be auditable.

Track:

RFQ
→ Quotes
→ Decision
→ Approval
→ PO

## Scoring

Default scoring:

Price: 30%
Delivery: 20%
Quality: 15%
Reliability: 15%
Payment Terms: 10%
Risk: 10%

Scores must be calculated by deterministic application logic.

Weights must be configurable.

## Hackathon Priorities

P0:
RFQ → Quote Analysis → Vendor Selection

P1:
Approval → Purchase Order

P2:
Inventory → Finance

P3:
Dashboard → Analytics

P4:
Optional features

## Demo Principle

Every major feature must be demonstrable.

Do not sacrifice stability for feature count.

A working 5-feature prototype is better than a broken 15-feature ERP.

## UX Principle

The application should look like a serious enterprise product.

Prioritize:

* clarity
* trust
* speed
* information hierarchy
* explainability

## Communication

When asked to implement something:

1. Explain what you found.
2. Explain the plan briefly.
3. Implement.
4. Test.
5. Report results.

If something is ambiguous, choose the simplest reasonable solution and continue unless the ambiguity can cause data loss or architectural failure.
