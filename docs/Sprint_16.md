# Sprint 16 — Practice Arena: On-Demand Drills + Topic Mastery

**Duration:** ~4 days
**Theme:** Give learners unlimited (plan-capped) practice beyond the course:
generate a drill on any topic — or on their measured weaknesses — and show a
per-topic **mastery** picture that drives what to practice next.

## Goal

A **Practice** page where the learner picks a language + topic (or hits "train
my weak spots") and the AI generates a standalone exercise to solve immediately
— graded like course exercises but not part of course progress. Aggregate quiz/
exercise/review history into **per-topic mastery** shown on the Progress page,
and use the weakest topics to power the one-click drill.

## User Story

- As a learner, I can say "give me a recursion exercise in Python" and get one
  now, without touching my course.
- As a learner, one click drills whatever I'm currently worst at.
- As a learner, Progress shows which topics I'm strong/weak in per language.

## Tasks

### Backend
1. `practice_exercises` reuse: generate via the existing
   `AIProvider.generate_exercise` into the `exercises` table under a hidden
   per-user "Practice — {language}" course/lesson container (`source="ai"`,
   excluded from Today/course progress), so run/submit/tutor all work unchanged.
2. `PracticeService.generate(user, language, topic|None, difficulty)`:
   topic=None → pick the weakest topic from mastery. Counted as `generate`
   usage (entitlement-capped, 402 over limit). Self-contained ownership checks.
3. **Mastery**: derive per-topic scores from history — quiz attempts (by lesson
   title/topic), exercise verdicts, review lapses. `MasteryService.snapshot(user,
   language)` → `[{topic, attempts, correct_rate, level: weak|ok|strong}]`.
   Topic key = the lesson title the item belongs to (practice items carry their
   requested topic).
4. Endpoints: `POST /practice/generate`, `GET /practice/history`,
   `GET /me/mastery?language=…`.
5. Tests: generation capped by plan, weakest-topic selection, mastery math,
   practice excluded from course progress/Today.

### Frontend
1. **Practice page** (`/practice`): language + topic pickers, difficulty,
   "Generate" → routes to the standard exercise page; "Train my weak spots"
   button; history list of past drills with verdicts.
2. **Mastery panel** on Progress: per-language topic bars (weak → strong),
   each with a "practice this" shortcut.
3. `features/practice/hooks.ts`, `features/mastery/hooks.ts`; nav entry.

## Expected Files

```text
backend/
  app/application/services/practice_service.py      (new)
  app/application/services/mastery_service.py       (new)
  app/api/v1/routes/practice.py                      (new)
  app/api/deps.py                                    # wiring
  tests/test_practice.py                             (new)
frontend/
  src/pages/Practice.tsx                             (new)
  src/features/practice/hooks.ts                     (new)
  src/features/mastery/hooks.ts                      (new)
  src/pages/Progress.tsx                             # mastery panel
```

## Acceptance Criteria

- [ ] A learner can generate and solve a topic drill end-to-end (run, submit,
      tutor hint) outside any course.
- [ ] "Train my weak spots" picks a genuinely weak topic from real history.
- [ ] Practice drills respect the daily generation entitlement (402 over cap).
- [ ] Practice items never pollute course progress or the Today plan.
- [ ] Mastery view shows per-topic strength per language.
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 6** (`generate_exercise`), **Sprint 4** (grading), **Sprint 13**
  (entitlements), **Sprint 15** (review history enriches mastery — soft dep).
