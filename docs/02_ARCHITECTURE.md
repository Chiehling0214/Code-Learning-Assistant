# 02 — Architecture

## System Overview

```text
            ┌─────────────────────────────────────────────┐
            │                  Browser                     │
            │  React + Vite + TS (TanStack Query, Zustand) │
            │  Monaco editor · shadcn/ui · Tailwind        │
            └───────────────┬─────────────────────────────┘
                            │ HTTPS (REST /api/v1)
                            │ Firebase ID token (Bearer)
            ┌───────────────▼─────────────────────────────┐
            │                 FastAPI                       │
            │  api → application → domain ← infrastructure  │
            │  (Clean Architecture, DI via Depends)        │
            └──────┬───────────────┬───────────────┬───────┘
                   │               │               │
        ┌──────────▼───┐   ┌───────▼──────┐  ┌─────▼─────────┐
        │ PostgreSQL   │   │ Judge0 (L2)  │  │ Gemini / AI   │
        │ (SQLAlchemy  │   │ code runner  │  │ (L4)          │
        │  + Alembic)  │   │ (later)      │  │ (later)       │
        └──────────────┘   └──────────────┘  └───────────────┘
```

`(L2)` / `(L4)` mark integrations deferred to later sprints.

## Clean Architecture Layers (backend)

The backend follows a dependency rule: **outer layers depend on inner layers,
never the reverse.**

```text
api            (presentation)   FastAPI routers, request/response wiring
  │  depends on
application     (use cases)      services / orchestration, no framework code
  │  depends on
domain          (enterprise)     entities + repository interfaces, pure Python
  ▲  implemented by
infrastructure  (details)        SQLAlchemy models, repo impls, db session,
                                 external clients (Firebase, Judge0, Gemini)
```

- **domain** is pure: dataclasses/entities and abstract repository protocols.
  No SQLAlchemy, no FastAPI imports here.
- **application** orchestrates domain objects through repository interfaces.
- **infrastructure** provides concrete implementations (DB, external APIs).
- **api** is thin: parse → call application service → serialize.

Dependency injection is done with FastAPI's `Depends`, wiring concrete
infrastructure implementations into application services at the edge.

## Request Lifecycle

1. Request hits a FastAPI route in `app/api/v1/routes/*`.
2. Auth dependency (`get_current_user`) verifies the Firebase token (stubbed
   in Sprint 0).
3. The route resolves an application service via `Depends`.
4. The service uses domain repository interfaces; concrete repos talk to the DB.
5. A Pydantic schema serializes the response.

## Technology Decisions

| Decision | Rationale |
|----------|-----------|
| FastAPI | Async, typed, great DI, OpenAPI out of the box. |
| Clean Architecture | Keeps AI/Judge0 swappable behind interfaces. |
| SQLAlchemy 2.0 + Alembic | Mature ORM + versioned migrations. |
| React + Vite | Fast DX, modern build. |
| TanStack Query | Server-state caching; pairs with REST. |
| Zustand | Minimal client-state store (UI/session). |
| Firebase Auth | Offloads identity; verify tokens server-side. |
| Docker Compose | Reproducible one-command local stack. |

## Cross-cutting Concerns

- **Config**: environment-driven via `pydantic-settings` (see [07](07_BACKEND.md)).
- **Logging**: structured JSON (see [07](07_BACKEND.md)).
- **Errors**: centralized exception handlers return consistent JSON.

See [03_DATABASE.md](03_DATABASE.md), [04_API.md](04_API.md), and
[07_BACKEND.md](07_BACKEND.md) for detail.
