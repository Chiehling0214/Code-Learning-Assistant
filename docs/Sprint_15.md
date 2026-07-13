# Sprint 15 — Review & Retention: Mistakes Notebook + Spaced Review

**Duration:** ~4 days
**Theme:** Close the forgetting curve. Everything the learner gets wrong (quiz
questions, placement questions, failed exercises) lands in a **mistakes
notebook** and comes back for review on a spaced schedule, folded into "Today".

## Goal

Capture every miss as a reviewable item, schedule it with a simple spaced-
repetition rule (wrong → review tomorrow; correct on review → interval doubles;
after ~3 clean passes → retired), and surface due reviews in the Today plan and
a dedicated Review page. This turns one-shot lessons into retained knowledge —
the core pedagogical gap right now.

## User Story

- As a learner, questions I got wrong come back to me the next day, then with
  growing gaps, until I've mastered them.
- As a learner, "Today" tells me how many reviews are due before new material.
- As a learner, I can open my mistakes notebook anytime and see what I keep
  getting wrong, with the explanations.

## Tasks

### Backend
1. `review_items` table + migration `0015_review_items`: id, user_id,
   `source` (quiz|placement|exercise), `item_ref` (question/exercise id),
   `payload` JSONB (a **snapshot**: prompt, choices, correct answer,
   explanation — so reviews survive content edits/hiding), `interval_days`,
   `due_at`, `lapses`, `passes`, `retired`.
2. Capture hooks (no new AI calls):
   - Quiz grading (`QuizService.grade`): each wrong question → upsert item.
   - Placement submit: wrong MCQs → items (payload from the breakdown).
   - Exercise submissions: a `failed` graded submission → item linking the
     exercise (review = "retry this exercise").
3. `ReviewService`: `list_due(user)`, `answer(item_id, correct)` applying the
   schedule (1 → 2 → 4 → 8 days; 3 consecutive passes retires the item; wrong
   resets to 1 day). Ownership-checked.
4. Endpoints: `GET /me/review` (due + counts), `POST /me/review/{id}/answer`,
   `GET /me/review/all` (the notebook, paged).
5. Today plan: prepend a `review` entry ("N reviews due") when any are due.
6. Tests: capture on wrong-only, schedule math, retirement, ownership, Today
   integration.

### Frontend
1. **Review page** (`/review`): flashcard-style loop — show the question, pick
   an answer, reveal correct + explanation, self-advance; failed exercises link
   to the exercise page.
2. **Mistakes notebook** tab on the same page: everything captured, filter by
   language/source, retired items greyed out.
3. Today card shows "🔁 N reviews due" first; dashboard badge with the count.
4. `features/review/hooks.ts` (`useDueReviews`, `useAnswerReview`, `useNotebook`).

## Expected Files

```text
backend/
  alembic/versions/0015_review_items.py            (new)
  app/infrastructure/models/models.py              # + ReviewItem
  app/application/services/review_service.py        (new)
  app/api/v1/routes/review.py                       (new)
  app/application/services/quiz_service.py          # capture hook
  app/application/services/placement_service.py     # capture hook
  app/infrastructure/grading.py                     # capture hook
  tests/test_review.py                              (new)
frontend/
  src/pages/Review.tsx                              (new)
  src/features/review/hooks.ts                      (new)
  src/pages/Today.tsx / Dashboard.tsx               # due-review surfacing
```

## Acceptance Criteria

- [x] Wrong quiz/placement answers and failed exercises appear as review items;
      correct ones never do.
- [x] The schedule works: wrong → due next day; passes double the interval;
      3 passes retire the item.
- [x] "Today" surfaces due reviews before new content.
- [x] The notebook page lists all captured mistakes with explanations.
- [x] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprints 5/10** grading paths (quiz results, placement breakdown, submission
  verdicts) — all already emit the needed data.
- **Sprint 7** (Today) for surfacing.

---

## Status — done

**Backend**
- `review_items` table (migration `0015`; unique per `(user_id, item_ref)`),
  `ReviewItem` entity + repo (SQLAlchemy + fake).
- `ReviewService`: `capture_miss` (create or lapse-reset, snapshot refreshed),
  `record_pass`, `answer` (1 → 2 → 4 days; 3 consecutive passes retire; wrong
  resets + counts a lapse), `list_due` / `due_count` / `notebook`.
- Capture hooks: `QuizService.grade` (wrong questions), `PlacementService.submit`
  (wrong MCQs), and `grading.sync_exercise_review` — a **failed** submission
  captures the exercise, a later **passed** one auto-advances the review.
- Endpoints: `GET /me/review`, `GET /me/review/all`,
  `POST /me/review/{id}/answer`. `GET /today` now returns `reviews_due`.
- `tests/test_review.py` (capture, schedule math, retire/reactivate, ownership
  404, Today integration) — 117 tests total, DB-free.

**Frontend**
- `/review` page: **Due now** flashcard loop (MCQs re-answered in place with the
  correct answer + explanation revealed; exercises link out with "I solved it /
  still stuck") and a **Mistakes notebook** tab (retired items shown as
  mastered). Nav entry added.
- Today shows a "🔁 N reviews due — clear these first" card linking to /review.
- `features/review/hooks.ts` (`useDueReviews`, `useNotebook`, `useAnswerReview`).

### Verification

- Backend `ruff` + `pytest` 117/117; frontend `lint` + `build` pass.
- Live (Docker): migration `0014 → 0015` applied on startup; the three review
  endpoints registered; `review_items` present.

### Notes

- Answering is self-reported for exercises (Anki-style) but automatic for MCQs
  (the card knows its answer key from the snapshot).
- Payloads are snapshots, so reviews keep working if the source lesson is later
  edited or hidden by admin review.
