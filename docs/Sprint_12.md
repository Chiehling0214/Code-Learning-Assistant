# Sprint 12 — Continuous Learning: Extend & In-Course Chat

**Duration:** ~4 days
**Theme:** Keep the course growing — a one-click "generate more" when the learner
nears the end, and an in-course chat where they ask for specific topics and the
AI adds them.

## Goal

When a learner is close to finishing a course (progress ≥ a threshold), surface a
**"Learn more"** action that generates additional lessons/exercises/quizzes into
the same course. Add an **in-course chat**: the learner types "I want to learn
X", and the AI generates matching content (a lesson + exercises + quiz) appended
to the course. Both reuse the Sprint 11 generation pipeline.

## User Story

- As a learner nearing the end of a course, I can click to get more to learn
  without leaving the course.
- As a learner, I can chat inside a course — "teach me decorators" — and new
  lessons/exercises/quizzes appear.
- As the platform, all generated additions are self-verified and land in the
  existing tables.

## Tasks

### Backend
1. `CurriculumService.extend_course(course_id, topic=None)`: generate N more
   lessons (with exercises + quiz) for the course; when `topic` is given, target
   it. Appends with correct `order_index`; `source="ai"`; self-verified.
2. `CourseChatMessage` model + migration `0012_course_chat` (FK → user, course,
   `role` user|assistant, `content`, created_at) to persist the conversation.
3. `CourseChatService.send(course_id, message)`: interpret the request via the
   provider, decide topic(s), call `extend_course`, and return an assistant reply
   summarizing what was added.
4. Endpoints: `POST /courses/{id}/extend`, `GET /courses/{id}/chat`,
   `POST /courses/{id}/chat`. Ownership-checked; generation quota applies.
5. "Near completion" signal: `GET /courses/{id}` (or progress) exposes a
   `completion_percent` and a `can_extend` hint (≥ threshold, e.g. 80%).
6. Tests (AI + Judge0 mocked): extend adds content in order; chat request
   generates targeted content and stores the exchange; ownership + quota enforced.

### Frontend
1. Course page: a **"Learn more"** button shown when `can_extend`; triggers extend
   and refreshes the lesson list.
2. In-course **chat panel**: message list + input; sending generates content and
   shows the assistant summary; new lessons appear inline.
3. `features/curriculum/hooks.ts` (+ `useExtendCourse`, `useCourseChat`).

## Expected Files

```text
backend/
  app/application/services/curriculum_service.py     # + extend_course
  app/application/services/course_chat_service.py     (new)
  app/infrastructure/models/models.py                # + CourseChatMessage
  alembic/versions/0012_course_chat.py                (new)
  app/api/v1/routes/curriculum.py                     # + extend / chat
  app/schemas/curriculum.py                           # + chat schemas
  tests/test_course_chat.py                           (new, mocked AI + Judge0)
frontend/
  src/features/curriculum/hooks.ts
  src/components/CourseChatPanel.tsx                  (new)
  src/pages/Course.tsx                               # learn-more + chat
```

## Acceptance Criteria

- [x] "Learn more" appends lessons/exercises/quizzes to the course.
- [x] Chat "I want to learn X" generates targeted content and persists the
      exchange; the assistant summarizes what was added.
- [x] The extend action appears only when the course is near completion.
- [x] Ownership and generation quota are enforced.
- [x] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 11** (generation pipeline + track-scoped courses).
- **Sprint 7** (progress) for the near-completion signal.
- **Sprint 6** (provider) for chat interpretation.

---

## Status — done

**Backend**
- `CurriculumService.extend_course(course_id, user_id, focus=None, count=None)`:
  appends `count` lessons (bounded to `CURRICULUM_EXTEND_MAX`) with the next
  `order_index` and `source="ai"`, via `generate_lesson_batch` with an optional
  `focus`. Ownership (`get_owned_course`) and the per-user AI budget are enforced;
  `course_completion` / `can_extend` / `lesson_count` back the hint.
  `_build_lesson_from_data` now returns the created lesson so callers can report
  what was added.
- `CourseChatService.send(..., count=None)`: ownership + quota check, persists the
  learner message, builds a short **transcript of the recent conversation** and
  passes it as the `focus` (so "I need more" continues the last topic), calls
  `extend_course`, persists an assistant summary, returns
  `(assistant_message, added_lessons)`.
- `CourseChatMessage` model + entity + repo; migration `0012_course_chat`.
- Endpoints (all ownership-checked): `GET /courses/{id}/extension`,
  `POST /courses/{id}/extend` (optional `topic`, `count`), `GET /courses/{id}/chat`,
  `POST /courses/{id}/chat` (`message`, optional `count`). Config:
  `CURRICULUM_EXTEND_COUNT` (2), `CURRICULUM_EXTEND_MAX` (5),
  `CURRICULUM_EXTEND_THRESHOLD` (0.8).
- `tests/test_course_chat.py` (extend order, targeted chat + persistence,
  ownership 404s, extension/completion hint, quota) — 93 tests total, DB-free.

**Frontend**
- `features/curriculum/hooks.ts`: `useCourseExtension`, `useExtendCourse`,
  `useCourseChat`, `useSendCourseChat` (invalidate course + extension + chat);
  extend/chat take an optional lesson count.
- `components/LessonCountSelect.tsx`: reusable 1–5 lesson-count dropdown.
- `components/CourseChatPanel.tsx`: message list + input + count select; new
  lessons appear after the list refreshes.
- `Course` page: "Learn more" button + count select (shown when `can_extend`) +
  the chat panel.

### Verification

- Backend: `ruff` clean, `pytest` 96/96 pass. Frontend: `lint` clean, `build` ok.
- Live (Docker stack): migration `0011 → 0012` applied (`course_chat_messages`
  created). A **real** chat "I need lessons about pygame" then "I need more"
  (count 2) appended *Pygame* lessons (event loops, sprite animation) — the
  follow-up stayed on topic instead of reverting to generic Python — stored the
  `user`/`assistant` messages, and returned a summary; ownership + completion +
  count-bounding verified.

### Notes / follow-ups

- Extend runs synchronously in the request (one AI call for the batch), unlike the
  initial background generation — fast enough and simpler for a single click.
- Chat is **context-aware without an extra AI call**: the recent conversation is
  passed as the generation `focus`, so the model infers the concrete subject and
  resolves vague follow-ups ("more") itself — conserving quota.
- Plan-limit refinement + admin AI-review is **Sprint 13**.
