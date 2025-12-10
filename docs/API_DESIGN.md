# API Design Guide

- [Principles](#principles)
- [Resource Naming](#resource-naming)
- [Authentication](#authentication)
- [Error Responses](#error-responses)
- [Pagination](#pagination)
- [Sorting](#sorting)
- [Request/Response Examples](#requestresponse-examples)
- [Versioning](#versioning)
- [FAQ](#faq)

## Principles
- Keep endpoints small and purpose-driven; avoid mixing write and read concerns.
- Favor explicit parameters over magic defaults; document every nullable field.
- Return consistent envelopes and HTTP status codes; no silent failures.

## Resource Naming
- Base path: `/api/v1/{resource}` with plural nouns (e.g., `/api/v1/protocols`, `/api/v1/analyses`).
- Nested resources only when ownership is strict: `/api/v1/users/{user_id}/watchlist`.
- Use nouns for resources, verbs only for actions that do not map cleanly to CRUD (e.g., `/api/v1/auth/telegram`, `/api/v1/analyses/{id}/retry`).

## Authentication
- Header: `Authorization: Bearer <JWT>`.
- Reject requests without token or with expired/invalid signatures using `401` and the standard error envelope.
- For Telegram Mini App, validate `initData` freshness before issuing JWT; refuse replayed payloads.

## Error Responses
- Unified JSON envelope:
```json
{
  "error": {
    "code": "string",        // machine-readable, e.g., VALIDATION_ERROR
    "status": 400            // mirrors HTTP status
  },
  "message": "human-readable summary",
  "details": [ "field errors or hints" ]
}
```
- Use precise HTTP codes: `400` validation, `401` auth, `403` forbidden, `404` missing, `409` conflict, `422` semantic errors, `429` rate limit, `500` server.

## Pagination
- Support `limit` (default 20, max 100) and `offset` for simple lists.
- Prefer cursor-based pagination for frequently changing lists: `cursor` + `limit`, return `next_cursor`.
- Always return `total` when available; for cursor mode include `has_more`.

## Sorting
- Query params: `sort_by` (field name) and `order` (`asc` | `desc`). Validate against an allowlist per endpoint.
- Default sort must be documented; avoid implicit field changes.

## Request/Response Examples
### List protocols (offset)
```
GET /api/v1/protocols?limit=20&offset=0&sort_by=tvl&order=desc
Authorization: Bearer <JWT>
```
```json
{
  "items": [
    { "id": "aave-v3", "name": "Aave V3", "chain": "ethereum", "tvl": 123456789.12 }
  ],
  "total": 42
}
```

### List analyses (cursor)
```
GET /api/v1/analyses?cursor=eyJpZCI6IjEyMyJ9&limit=10
Authorization: Bearer <JWT>
```
```json
{
  "items": [
    { "id": "analysis-123", "protocol": "aave-v3", "status": "completed" }
  ],
  "next_cursor": "eyJpZCI6IjEyNCJ9",
  "has_more": true
}
```

### Error example
```json
{
  "error": { "code": "VALIDATION_ERROR", "status": 400 },
  "message": "limit must be between 1 and 100",
  "details": [ "limit: 500" ]
}
```

## Versioning
- Use URI versioning (`/api/v1/...`) for breaking changes; keep backward compatibility inside a major version.
- Deprecate endpoints with `Deprecation` headers and changelog notes; remove only after a grace period.
- Keep response shapes stable; add fields in a backward-compatible way and document them.

## FAQ
- **How do we add a new endpoint?** Define resource noun, confirm envelope and pagination pattern, add request/response examples, and document defaults.
- **Can we return partial errors?** No mixed success; use `207` only if the operation is explicitly batch and documented.
- **Should we include server time?** Include `Date` header; add `server_time` field only when clients must sync clocks.
