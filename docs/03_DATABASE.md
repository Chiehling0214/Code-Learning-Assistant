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

### `quizzes` (Sprint 5)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| lesson_id | UUID (FK → lessons.id) | cascade delete |
| title | str | |
| slug | str | unique per lesson (`uq_quizzes_lesson_slug`) |
| description | text, nullable | |
| created_at / updated_at | timestamptz | |

### `questions` (Sprint 5)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| quiz_id | UUID (FK → quizzes.id) | cascade delete |
| prompt | text | the question |
| type | str | `single` (single correct choice) |
| order_index | int | display order |

### `choices` (Sprint 5)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| question_id | UUID (FK → questions.id) | cascade delete |
| text | text | choice label |
| is_correct | bool | answer key — **never serialized to learners** |
| order_index | int | display order |

### `quiz_attempts` (Sprint 5)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | cascade delete |
| quiz_id | UUID (FK → quizzes.id) | cascade delete |
| score | int | number of questions answered correctly |
| answers | jsonb | `{selected: {qid: cid}, total, results[]}` |
| created_at / updated_at | timestamptz | |

### `ai_interactions` (Sprint 6)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | cascade delete |
| kind | str | `teacher` \| `tutor` \| `generate` |
| model | str | model id used |
| total_tokens | int | usage logged for observability |
| created_at | timestamptz | indexed; backs per-user rate limiting |

> **Sprint 6 also adds** a `source` column (`human` \| `ai`, default `human`) to
> both `lessons` and `exercises` so AI-authored rows are reviewable.

### `progress_events` (Sprint 7)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | cascade delete |
| item_type | str | `lesson` \| `exercise` \| `quiz` |
| item_id | UUID | id of the completed item |
| status | str | `completed` (lesson/quiz) or grading verdict (exercise) |
| score | int, nullable | e.g. quiz score |
| completed_at | timestamptz | indexed; backs the day streak |

### `subscriptions` (Sprint 8)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | unique (one per user) |
| plan | str | `free` \| `pro` |
| status | str | `inactive` \| `active` \| `canceled` |
| stripe_customer_id | str, nullable | |
| stripe_subscription_id | str, nullable | |
| current_period_end | timestamptz, nullable | set from Stripe events |
| created_at / updated_at | timestamptz | |

### `language_tracks` (Sprint 9)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | cascade delete |
| language_id | UUID (FK → programming_languages.id) | cascade delete |
| level | str, nullable | assessed by the placement test (Sprint 10) |
| status | str | `onboarding` \| `active` |
| created_at / updated_at | timestamptz | unique `(user_id, language_id)` |

### `generation_jobs` (Sprint 11)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| track_id | UUID (FK → language_tracks.id) | cascade delete |
| user_id | UUID (FK → users.id) | cascade delete |
| status | str | `pending` \| `running` \| `done` \| `error` |
| total / completed | int | lessons planned / built (progress) |
| course_id | UUID, nullable | the course being generated |
| error | text, nullable | |
| created_at / updated_at | timestamptz | |

> **Sprint 11 also adds** a nullable `track_id` (FK → language_tracks) to
> `courses` so AI-generated courses belong to a learner's track (null = shared).

### `placement_assessments` (Sprint 10)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| track_id | UUID (FK → language_tracks.id) | unique (one per track) |
| user_id | UUID (FK → users.id) | cascade delete |
| status | str | `ready` \| `completed` |
| items | jsonb | generated MCQs + coding tasks **with** answer keys (stripped on serve) |
| result | jsonb, nullable | per-item breakdown on submit |
| score | int, nullable | weighted percent |
| level | str, nullable | `beginner` \| `intermediate` \| `advanced` |
| created_at / updated_at | timestamptz | |

## ER

```text
users 1───1 student_profiles
users 1───* submissions *───1 exercises
users 1───* quiz_attempts *───1 quizzes
users 1───* ai_interactions
users 1───* progress_events        (item_type/item_id → lesson|exercise|quiz)
users 1───1 subscriptions
users 1───* language_tracks *───1 programming_languages
language_tracks 1───1 placement_assessments
language_tracks 1───* generation_jobs
language_tracks 1───* courses (track_id; AI-generated, personalized)
programming_languages 1───* courses 1───* lessons 1───* exercises
lessons 1───* quizzes 1───* questions 1───* choices
```

## Migrations

Alembic lives under `backend/alembic/`. Migrations to date:

- `0001_initial` — users, student_profiles, programming_languages, courses.
- `0002_lessons` — lessons table.
- `0003_exercises` — exercises and submissions tables.
- `0004_quizzes` — quizzes, questions, choices, quiz_attempts tables.
- `0005_ai_interactions` — ai_interactions table (AI usage log / rate limiting).
- `0006_content_source` — `source` column on lessons and exercises.
- `0007_progress` — progress_events table.
- `0008_subscriptions` — subscriptions table.
- `0009_language_tracks` — language_tracks table (a learner's chosen languages).
- `0010_placement` — placement_assessments table.
- `0011_curriculum` — `courses.track_id` + generation_jobs table.

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
- Further entities (AI interactions, recommendations, subscriptions, etc.) are
  deferred to later sprints; see [01_PRD.md](01_PRD.md) for the schedule.

## Seeding

`python -m scripts.seed` (from `backend/`, or in the backend container) inserts
the **selectable languages** (Python, C++). As of Sprint 11 courses are
AI-generated per learner (placement → curriculum), so the seed no longer creates
sample courses; a dev-only `seed_sample_course()` helper remains for local
testing. Idempotent (rows keyed by slug).
