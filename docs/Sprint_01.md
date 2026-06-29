# Sprint 01 — Authentication & User Profile

**Duration:** ~3 days
**Theme:** Turn the stubbed auth into real Firebase verification; provision users
and profiles in the database; let learners view and edit their profile.

## Goal

Replace the Sprint 0 auth stub with end-to-end Firebase authentication. On first
authenticated request a `User` (and empty `StudentProfile`) is created. The
frontend can sign in, persist the session, guard private routes, and edit the
profile.

## User Story

- As a learner, I can sign in with Firebase (Google / email) so my progress is
  saved to my account.
- As a learner, my account is created automatically the first time I sign in.
- As a learner, I can view and update my profile (display name, skill level).
- As an unauthenticated visitor, I am redirected to `/login` when I open a
  private page.

## Tasks

### Backend
1. Disable stub by default in non-dev; ensure `verify_token` real path works
   (`app/core/security.py` already wired for `firebase-admin`).
2. Add write methods to the user repository interface and implementation
   (`create`, `update`) plus a `StudentProfileRepository`.
3. Add `UserService` (application layer): `get_or_create_from_identity()` —
   provisions `User` + `StudentProfile` on first login; `update_profile()`.
4. Expand `GET /api/v1/me` to return the DB-backed user (not just the token).
5. Add `GET /api/v1/me/profile` and `PUT /api/v1/me/profile`.
6. Wire repositories/services via `app/api/deps.py`.
7. Tests for provisioning + profile update (fake repositories).

### Frontend
1. `AuthProvider` (React context) wrapping Firebase `onAuthStateChanged`;
   populate the Zustand session store.
2. Real login actions in `Login.tsx` (Google + email/password).
3. `ProtectedRoute` wrapper; redirect unauthenticated users to `/login`.
4. `Profile` page (view + edit form) using a TanStack Query mutation.
5. Sign-out control in `AppLayout`.

## Expected Files

```text
backend/
  app/domain/repositories.py            # + write methods, StudentProfileRepository
  app/application/services/user_service.py        (new)
  app/infrastructure/repositories/sqlalchemy_repositories.py   # + impls
  app/api/v1/routes/me.py               # expanded
  app/api/v1/routes/profile.py          (new)
  app/schemas/user.py                   # + UpdateProfileRequest, ProfileResponse
  tests/test_user_service.py            (new)
frontend/
  src/lib/auth.tsx                      (new — AuthProvider, useAuth)
  src/components/ProtectedRoute.tsx     (new)
  src/pages/Profile.tsx                 (new)
  src/pages/Login.tsx                   # real sign-in
  src/components/layout/AppLayout.tsx   # + sign out
  src/routes.tsx                        # wrap private routes
  src/store/session.ts                  # populated from auth state
```

## Acceptance Criteria

- [x] A valid Firebase ID token is verified server-side; an invalid/missing
      token returns `401` (`test_me_requires_token_when_stub_disabled`).
- [x] First authenticated call creates exactly one `users` row and one
      `student_profiles` row (verified live; repeat `/me` keeps `count = 1`).
- [x] `GET /me` returns the persisted user; `PUT /me/profile` updates and
      persists changes.
- [x] Frontend redirects unauthenticated users from private routes to `/login`
      (`ProtectedRoute`).
- [x] Sign-in, session persistence across refresh, and sign-out all work
      (Firebase `onAuthStateChanged` + dev-mode `localStorage`).
- [x] `ruff`, `pytest` (9 tests), frontend `lint` + `build` pass.

## Dependency

- **Sprint 0** (scaffold, `User`/`StudentProfile` entities, auth stub, DI).

## Status — ✅ Complete

**Date:** 2026-06-29

### Delivered

**Backend**
- Per-request unit-of-work session (commit/rollback) in
  `infrastructure/db/session.py`.
- `UserRepository` write methods + new `StudentProfileRepository`
  (interfaces in `domain/repositories.py`, impls in
  `infrastructure/repositories/sqlalchemy_repositories.py`).
- `UserService` (`application/services/user_service.py`):
  `get_or_create_from_identity` (idempotent provisioning) + `update_profile`.
- `GET /api/v1/me` now DB-backed; new `GET`/`PUT /api/v1/me/profile`
  (`api/v1/routes/profile.py`), wired via `api/deps.py`
  (`get_user_service`, `get_current_db_user`).
- Schemas: `CurrentUserResponse`, `ProfileResponse`, `UpdateProfileRequest`.
- Tests: `tests/fakes.py`, `tests/conftest.py`, `tests/test_user_service.py`,
  `tests/test_me_api.py` (DB-free; 9 tests pass).

**Frontend**
- `lib/auth.tsx` (`AuthProvider` + `useAuth`): Firebase `onAuthStateChanged`,
  Google + email sign-in, dev-mode sign-in, sign-out; populates the Zustand
  session store from `/me`.
- `components/ProtectedRoute.tsx`; private routes wrapped in `routes.tsx`.
- `pages/Profile.tsx` (view/edit display name + skill level via TanStack Query
  mutation); real sign-in in `pages/Login.tsx`; sign-out + profile link in
  `AppLayout`.

### Verification

- Backend: `ruff` clean, `pytest` 9/9 pass.
- Frontend: `lint` clean, `build` succeeds (138 modules).
- Live (Docker stack): `/me` provisioned one user + profile; `/me/profile`
  defaulted to `beginner`; `PUT` persisted `display_name` + `skill_level`;
  repeat `/me` kept user count at 1; confirmed via `psql`.

### Notes / follow-ups

- No schema migration was needed — the Sprint 0 `users` / `student_profiles`
  tables already matched. Future profile fields will add a migration.
- Real Firebase verification is implemented but exercised only with
  `AUTH_STUB_ENABLED=false` + configured credentials; local/dev defaults to stub
  mode and the frontend dev sign-in.
