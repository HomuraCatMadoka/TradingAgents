# Phase 0 Remaining Plan (Telegram Mini App Dashboard)

## Completed Work Assessment
- Backend stub covers only Task 0.2 essentials: FastAPI app with health, mock protocols, Telegram auth/JWT; no persistence, no request schemas, permissive CORS, synchronous crypto, no auth freshness check, weak default secrets, all logic in one file (`miniapp/backend/main.py:14-69`).
- Telegram initData verification is minimal: lacks auth_date expiry/replay guard and swallows errors silently (`miniapp/backend/auth.py:7-27`).
- Frontend prototype only proves SDK boot and a fetch: no routing/state management/theme hook, no token handling, blocking fetch without cancel/retry, inline styles, no build-time env guard (`miniapp/frontend/src/App.tsx:10-105`).
- Env handling loads root `.env`, but there is no miniapp `.env.example`; backend deps stop at FastAPI/JWT, missing DB/ORM/WebSocket/Alembic; frontend has required libs installed but no project structure or lint/test setup.

## Remaining Tasks Priority & Dependencies
- P0 – Task 0.3 Database design/migrations: prerequisite for user/history/favorites and JWT session anchoring; required before real APIs.
- P0 – Task 0.4 Frontend scaffold: depends on API contracts; can start with mock services but must align types with 0.3/0.1-0.2 outcomes.
- P1 – Task 0.6 CI/CD: depends on repo structure and commands from 0.3/0.4; workflow skeleton can land early with TODOs.
- P1 – Task 0.5 Dev guidelines: low coupling; finalize after 0.4 so tooling commands are accurate.

## Task Details
### Task 0.3 – Database design & Alembic (est. 6-8h)
- Files/structure: `miniapp/backend/db.py` (async engine/session), `miniapp/backend/models/{user.py,analysis.py,favorite.py,session.py,watchlist.py}`, `miniapp/backend/schemas/*.py`, `miniapp/backend/alembic/{env.py,versions/001_initial_schema.py}`, `miniapp/backend/scripts/seed_data.py`.
- Key implementation points: define SQLAlchemy Base and typed models with JSONB for results/settings, UUID for sessions, FK/indexes per architecture spec; Alembic autogenerate wired to models; timestamps timezone-aware with server defaults; seed script for demo users/analyses.
- Integration: FastAPI lifespan creates engine; dependency for DB session; `/api/auth/telegram` stores/looks up users and sessions instead of returning raw user dict; replace mock `/api/protocols` with stubbed table/service; add `.env.example` with `DATABASE_URL`, `ALEMBIC_CONFIG`.

### Task 0.4 – Frontend scaffold (routing/state/components) (est. 6-8h)
- Files/structure: `miniapp/frontend/src/router.tsx`, pages `{Dashboard,Analysis,History,Watchlist,Settings}.tsx`, store `{auth.ts,ui.ts}`, services `{api.ts,protocols.ts,auth.ts,ws.ts}`, components `{Layout.tsx,ProtocolCard.tsx,ProgressBar.tsx,ErrorBoundary.tsx,ThemeProvider.tsx}`, types `{protocol.ts,analysis.ts,auth.ts}`.
- Key implementation points: React Router + layout TabBar; theme hook tied to Telegram events; auth guard using initData -> `/api/auth/telegram` -> JWT persisted; Axios client with interceptors; React Query provider; Zustand stores for auth/theme; WebSocket client placeholder; replace inline styles with AntD Mobile tokens and scoped CSS.
- Integration: health banner via `/api/health`; protocol list via `/api/protocols`; ensure Vite proxy matches backend path; mock services align with backend schemas until APIs land.
### Task 0.5 – Development guidelines (est. 3-4h)
- Files: `docs/CONTRIBUTING.md`, `docs/API_DESIGN.md`, `docs/FRONTEND_GUIDE.md`, `.github/ISSUE_TEMPLATE/{bug_report.md,feature_request.md}`.
- Key implementation points: document branch strategy (trunk or short-lived), Conventional Commits, lint/format commands (frontend lint/build/test, backend ruff/mypy/pytest), API error envelope + pagination rules, frontend state rules (React Query for server data, Zustand for UI), XSS/initData safety notes.
- Integration: reference miniapp npm scripts and backend commands so CI can reuse; add checklist for updating PROJECT_STATUS/CHANGELOG per CLAUDE.md.

### Task 0.6 – CI/CD pipeline (est. 6-8h)
- Files: `.github/workflows/frontend-ci.yml`, `.github/workflows/backend-ci.yml`, optional `vercel.json` and Railway template.
- Key implementation points: frontend workflow runs npm ci -> lint (eslint) -> tests (vitest placeholder) -> build with cached node_modules; backend workflow sets up Python 3.11, installs `miniapp/backend/requirements.txt` + dev deps, runs ruff/mypy/pytest, starts Postgres service, applies Alembic upgrade before tests; fail on type or lint errors.
- Integration: align env vars with `.env.example`; workflows run from repo root and target miniapp paths; set required checks on `main`/`develop` branches.
## Risks / Technical Debt
- Auth flow lacks auth_date freshness/replay checks and uses default secrets; must be fixed while implementing Task 0.3.
- No structured logging/telemetry; WebSocket/debugging will be painful without baseline logging middleware and request IDs.
- CORS is wide open and no rate limiting; unacceptable beyond local dev.
- Frontend missing error boundaries and theme persistence; current inline styles are not maintainable.
- Zero tests around auth/SDK integration; need unit tests with mocked initData and fetch to prevent regressions.

## Actionable Checklist
- [ ] Finalize DB schema + Alembic migration; add seed script.
- [ ] Wire DB session + token storage; harden Telegram auth expiry/replay.
- [ ] Scaffold frontend routing/state/components with SDK-driven theme and auth guard.
- [ ] Add dev docs (CONTRIBUTING/API_DESIGN/FRONTEND_GUIDE + issue templates).
- [ ] Add CI workflows (frontend/backend) with lint+test+build and Postgres service.
