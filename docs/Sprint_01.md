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

- [ ] A valid Firebase ID token is verified server-side; an invalid/missing
      token returns `401`.
- [ ] First authenticated call creates exactly one `users` row and one
      `student_profiles` row.
- [ ] `GET /me` returns the persisted user; `PUT /me/profile` updates and
      persists changes.
- [ ] Frontend redirects unauthenticated users from private routes to `/login`.
- [ ] Sign-in, session persistence across refresh, and sign-out all work.
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 0** (scaffold, `User`/`StudentProfile` entities, auth stub, DI).
