# 03 — Database

## Engine

- **PostgreSQL 16**.
- Access via **SQLAlchemy 2.0** ORM.
- Schema versioned with **Alembic**.

Connection string (see `.env`):

```text
postgresql+psycopg2://<user>:<password>@<host>:<port>/<db>
```

## Sprint 0 Entities (placeholders)

Only the minimal tables needed to prove the migration pipeline exist. **No
business logic, constraints beyond keys, or relationships behavior is
implemented yet** — fields will be expanded in later sprints.

### `users`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | generated |
| firebase_uid | str, unique | maps to Firebase identity |
| email | str, unique | |
| display_name | str, nullable | |
| is_admin | bool | default false |
| created_at | timestamptz | default now |
| updated_at | timestamptz | auto-update |

### `student_profiles`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | unique |
| skill_level | str | e.g. beginner/intermediate (placeholder) |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `programming_languages`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| name | str, unique | e.g. "Python" |
| slug | str, unique | e.g. "python" |
| created_at | timestamptz | |

### `courses`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| language_id | UUID (FK → programming_languages.id) | |
| title | str | |
| slug | str, unique | |
| description | text, nullable | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `lessons` (Sprint 2)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| course_id | UUID (FK → courses.id) | cascade delete |
| title | str | |
| slug | str | unique per course (`uq_lessons_course_slug`) |
| order_index | int | ordering within the course |
| content | text | markdown |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `exercises` (Sprint 3)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| lesson_id | UUID (FK → lessons.id) | cascade delete |
| language | str | e.g. "python" (Judge0 language in Sprint 4) |
| title | str | |
| slug | str | unique per lesson (`uq_exercises_lesson_slug`) |
| prompt | text | exercise statement |
| starter_code | text | seeds the editor |
| test_spec | jsonb | hidden test cases (used by the grader in Sprint 4) |
| created_at / updated_at | timestamptz | |

### `submissions` (Sprint 3)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | cascade delete |
| exercise_id | UUID (FK → exercises.id) | cascade delete |
| code | text | submitted source |
| status | str | `pending` \| `passed` \| `failed` \| `error` (starts `pending`) |
| result | jsonb, nullable | grading output (populated in Sprint 4) |
| created_at / updated_at | timestamptz | |

## ER

```text
users 1───1 student_profiles
users 1───* submissions *───1 exercises
programming_languages 1───* courses 1───* lessons 1───* exercises
```

## Migrations

Alembic lives under `backend/alembic/`. Migrations to date:

- `0001_initial` — users, student_profiles, programming_languages, courses.
- `0002_lessons` — lessons table.
- `0003_exercises` — exercises and submissions tables.

```bash
# create/upgrade to latest
alembic upgrade head

# autogenerate after editing ORM models
alembic revision --autogenerate -m "describe change"
```

The compose stack runs `alembic upgrade head` automatically on backend start.

## Conventions

- Primary keys are UUIDs.
- Timestamps are `timestamptz`, UTC.
- Table names are snake_case plural.
- Further entities (exercises, submissions, quizzes, attempts, etc.) are deferred
  to later sprints; see [01_PRD.md](01_PRD.md) for the schedule.

## Seeding

`python -m scripts.seed` (from `backend/`, or in the backend container) inserts a
sample language, course, and lessons. It is idempotent (rows keyed by slug).
