# 06 — Frontend

## Stack

| Concern | Choice |
|---------|--------|
| Framework | React 18 + TypeScript |
| Build | Vite 5 |
| Styling | TailwindCSS 3 |
| Components | shadcn/ui (Radix + Tailwind) |
| Server state | TanStack Query v5 |
| Client state | Zustand |
| Routing | React Router v6 |
| Code editor | Monaco (`@monaco-editor/react`) |
| Auth | Firebase Web SDK |

## Structure

```text
frontend/
├── index.html
├── src/
│   ├── main.tsx              # app entry, providers
│   ├── App.tsx              # router + layout
│   ├── index.css            # tailwind layers + theme tokens
│   ├── pages/               # one file per route (Dashboard/Course/Lesson/Admin/Profile live)
│   ├── features/
│   │   ├── content/        # content query/mutation hooks (Sprint 2)
│   │   └── exercises/      # exercise + submission hooks (Sprint 3)
│   ├── components/
│   │   ├── ui/              # shadcn primitives (button, card, ...)
│   │   ├── layout/         # AppLayout (nav + sign out)
│   │   └── ProtectedRoute.tsx  # auth guard for private routes
│   ├── lib/
│   │   ├── utils.ts        # cn() helper
│   │   ├── api.ts          # fetch wrapper -> backend
│   │   ├── query-client.ts # TanStack Query client
│   │   ├── firebase.ts     # Firebase init (guarded if unconfigured)
│   │   ├── markdown.ts     # markdown -> sanitized HTML (marked + DOMPurify)
│   │   └── auth.tsx        # AuthProvider + useAuth (sign in/out, session sync)
│   ├── store/
│   │   └── session.ts      # Zustand session store (current user)
│   └── routes.tsx           # route table
├── tailwind.config.js
├── postcss.config.js
├── components.json          # shadcn config
├── vite.config.ts
└── tsconfig.json
```

## Routes / Pages

`/` and `/login` are public. Everything below is wrapped in `ProtectedRoute`
(redirects to `/login` when unauthenticated) and rendered inside `AppLayout`.
Dashboard, Course, Lesson, Admin, and Profile are live; the remaining private
pages are placeholders.

| Path | Page | Access |
|------|------|--------|
| `/` | Landing | public |
| `/login` | Login (Google / email, or dev mode) | public |
| `/dashboard` | Dashboard (lists courses) | private |
| `/today` | Today | private |
| `/courses/:slug` | Course (header + ordered lessons) | private |
| `/lessons/:id` | Lesson (rendered markdown + exercise links) | private |
| `/exercises/:id` | Coding Exercise (Monaco + submit + history) | private |
| `/quizzes/:id` | Quiz | private |
| `/progress` | Progress | private |
| `/subscription` | Subscription | private |
| `/admin` | Admin (languages/courses/lessons CRUD) | private (admin) |
| `/profile` | Profile (view/edit display name & skill level) | private |

## Content (Sprint 2)

- `features/content/hooks.ts` holds the TanStack Query hooks: `useLanguages`,
  `useCourses`, `useCourse`, `useLesson`, plus admin create/delete mutations.
- Lesson markdown is rendered via `lib/markdown.ts` (`marked` + `DOMPurify`).
- The Admin page calls the admin endpoints; non-admin users get `403` and a
  banner explaining how to be promoted (`scripts.set_admin`).

## Exercises (Sprint 3–4)

- `features/exercises/hooks.ts`: `useExercise`, `useLessonExercises`,
  `useSubmissions`, `useSubmit`, `useRun`, and `useSubmission` (polls a single
  submission until grading finishes).
- The Coding Exercise page loads the exercise, seeds Monaco with its starter
  code and language, and offers **Run** (one-off execution, shows stdout/stderr)
  and **Submit** (graded in the background; the page polls for the verdict and
  shows a per-test breakdown via `components/ResultPanel.tsx`). A submission
  history is shown via `components/SubmissionList.tsx`.
- The Lesson page links to its exercises.

## Authentication (Sprint 1)

- `lib/auth.tsx` provides `AuthProvider` + `useAuth`. It subscribes to Firebase
  `onAuthStateChanged`, and on sign-in fetches `/me` to populate the session.
- When Firebase is **not** configured, a dev sign-in path is available
  (persisted in `localStorage`) so the app works against the backend's stub
  auth mode locally.
- `ProtectedRoute` shows a loader while auth resolves, then redirects
  unauthenticated users to `/login`.

## State Management

- **TanStack Query** owns all server data (queries/mutations against the API).
  A shared `QueryClient` is provided at the root.
- **Zustand** (`store/session.ts`) holds the current `SessionUser`, populated by
  the `AuthProvider`. Keep it small; prefer Query for anything fetched.

## API Access

`src/lib/api.ts` exposes a typed `apiFetch` that targets `VITE_API_BASE_URL`
and attaches the Firebase ID token when available.

## Firebase

`src/lib/firebase.ts` initializes the Web SDK only when the `VITE_FIREBASE_*`
variables are present; otherwise it exports `null` so the app still runs locally
without credentials (dev mode).

## Conventions

- Path alias `@/` → `src/`.
- Tailwind utility-first; shadcn components in `components/ui`.
- One component per file; PascalCase component names.

## Commands

```bash
npm install
npm run dev       # vite dev server on :5173
npm run build     # type-check + production build
npm run preview   # preview built output
npm run lint      # eslint
```
