# 01 — Product Requirements (PRD)

## Summary

CodePath AI delivers a personalized, hands-on programming curriculum. Learners
sign in, pick a programming language/course, and receive a daily plan of
lessons, coding exercises, and quizzes. AI assists with teaching and tutoring;
Judge0 runs and grades code.

## User Stories

### Learner

- As a learner, I can sign up / sign in with Firebase so my progress is saved.
- As a learner, I can choose a programming language and course.
- As a learner, I see a **Today** plan with the next items to complete.
- As a learner, I can read a **Lesson** taught by the AI Teacher.
- As a learner, I can solve a **Coding Exercise** in an in-browser editor and
  run it against test cases.
- As a learner, I can take a **Quiz** and see my score.
- As a learner, I can ask the **AI Tutor** for help on an exercise.
- As a learner, I can view my **Progress** over time.
- As a learner, I can manage my **Subscription**.

### Admin

- As an admin, I can create and edit courses, lessons, and languages.
- As an admin, I can view platform usage.

## Feature Matrix (by sprint)

Sprint numbers follow the detailed [Sprint_01…08](Sprint_01.md) plan.

| Feature | Sprint | Status |
|---------|--------|--------|
| Project scaffold & infra | 0 | ✅ done |
| Firebase auth (real verification) | 1 | ✅ done |
| User / StudentProfile + provisioning | 1 | ✅ done |
| Profile view/edit | 1 | ✅ done |
| Languages, Courses & Lessons + admin CRUD | 2 | ✅ done |
| Coding exercises (model & submissions) | 3 | ✅ done |
| Judge0 execution & grading | 4 | ✅ done |
| Quizzes & auto-grading | 5 | ✅ done |
| AI Teacher / AI Tutor + content generation | 6 | ✅ done |
| Recommendation ("Today") + progress | 7 | ✅ done |
| Subscriptions & hardening | 8 | ✅ done |
| Onboarding & language tracks | 9 | ✅ done |
| Placement test → assessed level | 10 | ✅ done |
| AI curriculum generation (full courses) | 11 | ✅ done |
| Continuous learning: extend + in-course chat | 12 | ⬜ planned |
| Entitlements (plan limits) & admin AI review | 13 | ⬜ planned |

> **Direction change (Sprint 9+):** content becomes AI-generated and personalized
> per learner. First login → pick a language → placement test → the AI builds a
> full course for the assessed level. Manual authoring is deprecated; admin is
> repurposed to review AI content. Plan limits: free users get **2 languages** and
> bounded AI Tutor / generation usage; subscribers get more.

## Functional Requirements

1. Authentication via Firebase; backend verifies ID tokens.
2. Persistent learner profile and progress in PostgreSQL.
3. Code execution sandboxed via Judge0 (later sprint).
4. AI features powered by Google Gemini (free tier; later sprint).

## Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| Performance | API p95 < 300ms for non-AI endpoints. |
| Portability | One-command local startup via Docker Compose. |
| Security | No secrets in source; tokens verified server-side. |
| Observability | Structured JSON logs; `/health` endpoint. |
| Testability | Layers decoupled via clean architecture. |

## Success Metrics

- Daily plan completion rate.
- Exercise pass rate on first attempt.
- 7-day learner retention.
