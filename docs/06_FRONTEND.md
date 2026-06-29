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
│   ├── pages/               # one file per route (placeholders)
│   ├── components/
│   │   ├── ui/              # shadcn primitives (button, card, ...)
│   │   └── layout/         # AppLayout, NavBar
│   ├── lib/
│   │   ├── utils.ts        # cn() helper
│   │   ├── api.ts          # fetch wrapper -> backend
│   │   ├── query-client.ts # TanStack Query client
│   │   └── firebase.ts     # Firebase init (guarded if unconfigured)
│   ├── store/
│   │   └── session.ts      # Zustand session/UI store
│   └── routes.tsx           # route table
├── tailwind.config.js
├── postcss.config.js
├── components.json          # shadcn config
├── vite.config.ts
└── tsconfig.json
```

## Routes / Pages

All pages render and compile. Business content is placeholder.

| Path | Page |
|------|------|
| `/` | Landing |
| `/login` | Login |
| `/dashboard` | Dashboard |
| `/today` | Today |
| `/courses/:slug` | Course |
| `/lessons/:id` | Lesson |
| `/exercises/:id` | Coding Exercise (Monaco editor mounted) |
| `/quizzes/:id` | Quiz |
| `/progress` | Progress |
| `/subscription` | Subscription |
| `/admin` | Admin |

## State Management

- **TanStack Query** owns all server data (queries/mutations against the API).
  A shared `QueryClient` is provided at the root.
- **Zustand** owns lightweight client/UI/session state (e.g. current user,
  theme). Keep it small; prefer Query for anything fetched.

## API Access

`src/lib/api.ts` exposes a typed `apiFetch` that targets `VITE_API_BASE_URL`
and attaches the Firebase ID token when available.

## Firebase

`src/lib/firebase.ts` initializes the Web SDK only when the `VITE_FIREBASE_*`
variables are present; otherwise it exports `null` so the app still runs locally
without credentials (Sprint 0 dev mode).

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
