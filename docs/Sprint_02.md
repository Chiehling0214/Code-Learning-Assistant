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

- [ ] Migration `0002` creates the `lessons` table; `alembic upgrade head` is
      clean.
- [ ] Seed script populates ≥1 language, ≥1 course, ≥3 lessons.
- [ ] `GET /courses/{slug}` returns the course with its ordered lessons.
- [ ] Admin CRUD persists; non-admin write attempts return `403`.
- [ ] Course/Lesson/Admin pages render live data (no placeholders).
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 1** (auth + `is_admin` flag for admin guard).
