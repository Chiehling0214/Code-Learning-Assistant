# 00 — Project Overview

## What is CodePath AI?

CodePath AI is an AI-powered, personalized programming learning platform. It
guides each learner through a structured path of lessons, coding exercises, and
quizzes, adapting the daily plan to the learner's progress.

The platform combines:

- **An AI Teacher** that explains concepts and delivers lessons.
- **An AI Tutor** that gives feedback on code and answers questions.
- **A code execution engine** (Judge0) for running and grading exercises.
- **A recommendation engine** that builds a personalized daily plan ("Today").

> **Sprint 0 scope:** this repository currently contains the *foundation* only —
> project structure, documentation, configuration, and runnable scaffolds.
> The AI, judging, quiz, exercise, learning, and recommendation features are
> intentionally **not implemented** and are scheduled for later sprints.

## Goals

| Goal | Description |
|------|-------------|
| Personalized | A daily plan tailored to each learner's level and history. |
| Hands-on | Learn by writing and running real code, not just reading. |
| Adaptive | Difficulty and topics adjust based on performance. |
| Accessible | Runs locally with a single `docker compose up`. |

## Non-Goals (for now)

- Native mobile applications.
- Multi-tenant / organization billing.
- Real-time collaborative editing.

## Personas

- **Learner** — follows a daily plan, completes lessons/exercises/quizzes.
- **Admin** — manages courses, languages, and content.

## Roadmap (high level)

| Sprint | Theme |
|--------|-------|
| **0** | Project bootstrap (this sprint) — scaffold, docs, infra. |
| 1 | Auth + user/profile domain, course & lesson CRUD. |
| 2 | Coding exercises + Judge0 integration. |
| 3 | Quizzes + grading. |
| 4 | AI Teacher & AI Tutor. |
| 5 | Recommendation engine ("Today") + progress analytics. |
| 6 | Subscriptions & billing. |

See [01_PRD.md](01_PRD.md) for product requirements and the rest of the `docs/`
folder for technical detail.
