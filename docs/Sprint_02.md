# Sprint 02 — Content: Languages, Courses & Lessons

**Duration:** ~4 days
**Theme:** A real content model. Learners browse languages → courses → lessons;
admins manage that content.

## Goal

Introduce the `Lesson` entity and flesh out `Course` / `ProgrammingLanguage`
with read APIs for learners and full CRUD for admins. Wire the existing
`Course`, `Lesson`, and `Admin` frontend pages to live data.

## User Story

- As a learner, I can browse available programming languages and their courses.
- As a learner, I can open a course and see its ordered lessons.
- As a learner, I can read a lesson's content (rendered markdown).
- As an admin, I can create, edit, reorder, and delete languages, courses, and
  lessons.

## Tasks

### Backend
1. Add `Lesson` ORM model (FK → course, `order_index`, `title`, `slug`,
   `content` markdown) + Alembic migration `0002`.
2. Add domain entities + repositories for Course, Lesson, Language.
3. `ContentService` (application): list/get courses, list lessons, get lesson.
4. Public read endpoints: `GET /languages`, `GET /courses`,
   `GET /courses/{slug}` (with lessons), `GET /lessons/{id}`.
5. Admin write endpoints (guarded by `is_admin`): create/update/delete for
   language, course, lesson; return `403` for non-admins.
6. Seed script (`scripts/seed.py`) inserting a sample language + course +
   lessons.
7. Tests: read endpoints, admin guard.

### Frontend
1. Query hooks (`src/features/content/`) for languages/courses/lessons.
2. `Course` page: course header + lesson list (replace placeholder).
3. `Lesson` page: render markdown content.
4. `Admin` page: tables + forms for CRUD.
5. Dashboard: link to real course list.

## Expected Files

```text
backend/
  app/infrastructure/models/models.py        # + Lesson
  app/infrastructure/models/__init__.py       # export Lesson
  alembic/versions/0002_lessons.py            (new)
  app/domain/entities.py                       # + Lesson
  app/domain/repositories.py                   # + Course/Lesson/Language repos
  app/infrastructure/repositories/sqlalchemy_repositories.py
  app/application/services/content_service.py  (new)
  app/api/v1/routes/{languages,courses,lessons,admin_content}.py  (new)
  app/schemas/content.py                       (new)
  scripts/seed.py                              (new)
  tests/test_content.py                        (new)
frontend/
  src/features/content/hooks.ts                (new)
  src/lib/markdown.ts                          (new — render helper)
  src/pages/{Course,Lesson,Admin}.tsx          # wired to API
```

## Acceptance Criteria

- [x] Migration `0002` creates the `lessons` table; `alembic upgrade head` is
      clean (applied live by the backend container on startup).
- [x] Seed script populates ≥1 language, ≥1 course, ≥3 lessons (verified:
      "Seeded language 'python', course 'python-basics', 3 new lesson(s)").
- [x] `GET /courses/{slug}` returns the course with its ordered lessons
      (verified: lessons returned in order 1, 2, 3).
- [x] Admin CRUD persists; non-admin write attempts return `403`
      (`test_content.py`; live admin write without token → `401`).
- [x] Course/Lesson/Admin pages render live data (no placeholders).
- [x] `ruff`, `pytest` (16 tests), frontend `lint` + `build` pass.

## Dependency

- **Sprint 1** (auth + `is_admin` flag for admin guard).

## Status — ✅ Complete

**Date:** 2026-06-29

### Delivered

**Backend**
- `Lesson` ORM model + relationship on `Course`; migration `0002_lessons`
  (unique slug per course, `order_index`, markdown `content`).
- Domain `Lesson` entity; `Language`/`Course`/`Lesson` repository interfaces and
  SQLAlchemy implementations (full CRUD).
- `ContentService` (`application/services/content_service.py`) for reads + admin
  writes; `require_admin` dependency in `api/deps.py`.
- Public reads: `GET /languages`, `/courses`, `/courses/{slug}` (with ordered
  lessons), `/lessons/{id}`. Admin CRUD under `/admin/*` (languages, courses,
  lessons), guarded by `is_admin`.
- `IntegrityError` handler → `409` on duplicate slugs.
- Scripts: `scripts/seed.py` (sample content, idempotent),
  `scripts/set_admin.py` (promote a user to admin).
- Tests: `tests/test_content.py` + content fakes (16 tests total, DB-free).

**Frontend**
- `features/content/hooks.ts` (TanStack Query hooks + admin mutations).
- `lib/markdown.ts` (`marked` + `DOMPurify`) for safe lesson rendering.
- Wired pages: `Course` (header + ordered lessons), `Lesson` (rendered
  markdown), `Admin` (languages/courses/lessons CRUD with non-admin banner),
  `Dashboard` (live course list).

### Verification

- Backend: `ruff` clean, `pytest` 16/16 pass.
- Frontend: `lint` clean, `build` succeeds.
- Live (Docker stack): migration `0002` applied automatically; `seed`
  inserted Python / python-basics / 3 lessons; `GET /courses/python-basics`
  returned lessons in order; admin write without token → `401`; missing
  course/lesson → `404`.

### Notes / follow-ups

- Users are provisioned non-admin; promote with `python -m scripts.set_admin
  <email>` then sign out/in. The Admin page shows a banner with this hint for
  non-admins.
- Admin UI covers create + delete + list (and full update via the API); richer
  inline editing/reordering can be added later if needed.
- The production JS bundle now exceeds Vite's 500 kB hint (Monaco + Firebase);
  code-splitting is a future optimization, not a Sprint 2 blocker.
