# 00 — Project Overview

## What is CodePath AI??

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

Detailed per-sprint plans live in [Sprint_01.md](Sprint_01.md) …
[Sprint_08.md](Sprint_08.md).

| Sprint | Theme | Status |
|--------|-------|--------|
| **0** | Project bootstrap — scaffold, docs, infra. | ✅ done |
| **1** | Authentication & user/profile (provisioning, profile edit). | ✅ done |
| **2** | Content: languages, courses & lessons + admin CRUD. | ✅ done |
| **3** | Coding exercises (model & submissions). | ✅ done |
| **4** | Judge0 code execution & grading. | ✅ done |
| **5** | Quizzes & auto-grading. | ✅ done |
| **6** | AI Teacher & AI Tutor (Gemini) + content generation. | ✅ done |
| **7** | Recommendation ("Today") & progress analytics. | ✅ done |
| **8** | Subscriptions, billing & hardening. | ✅ done |
| **9** | Onboarding & language tracks (pick a language on first login). | ✅ done |
| **10** | Placement test (MCQ + coding) → assessed level. | ✅ done |
| **11** | AI curriculum generation (full personalized courses). | ✅ done |
| **12** | Continuous learning: extend course + in-course chat. | ✅ done |
| **13** | Entitlements (plan limits) & admin AI-content review. | ✅ done |
| 14 | Production launch: GCP deployment & CI/CD. | ⬜ planned |
| **15** | Review & retention: mistakes notebook + spaced review. | ✅ done |
| **16** | Practice arena: on-demand drills + topic mastery. | ✅ done |
| **17** | Polish & quality: streaming AI, account settings, mobile. | ✅ done (E2E → 14) |

> **Direction change from Sprint 9.** The product pivots to **AI-generated,
> personalized curricula**: on first login the learner picks a language, takes a
> short placement test, and the AI builds a full course tuned to their level.
> Manual content authoring (Sprints 2–3 CRUD/seed) is **deprecated** in favor of
> generation, and the admin surface is repurposed for reviewing AI content. See
> [Sprint_09.md](Sprint_09.md)–[Sprint_13.md](Sprint_13.md).

See [01_PRD.md](01_PRD.md) for product requirements and the rest of the `docs/`
folder for technical detail.
