# API documentation

All endpoints are versioned under `/api/v1/`. Interactive OpenAPI docs are
served by FastAPI at `http://localhost:8000/docs` — that's the source of
truth for request/response shapes; this folder holds design notes that don't
belong in code (auth flow, error envelope conventions, pagination rules).

## Conventions

- REST, JSON in/out, versioned paths (`/api/v1/...`).
- Errors return `{"detail": "..."}` via FastAPI's default `HTTPException`
  handling, with the appropriate HTTP status code.
- Routes stay thin — see [../architecture/foundation.md](../architecture/foundation.md)
  for the routes → schemas → services → repositories layering rule.
