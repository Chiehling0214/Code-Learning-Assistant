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

## ER (Sprint 0)

```text
users 1───1 student_profiles
programming_languages 1───* courses
```

## Migrations

Alembic is initialized under `backend/alembic/`. The initial migration creates
the four tables above.

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
- Future relationships (enrollments, lessons, attempts, etc.) are deferred to
  later sprints; see [01_PRD.md](01_PRD.md) for the schedule.
