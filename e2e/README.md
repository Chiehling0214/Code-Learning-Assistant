# Browser tests (Playwright)

The default suite uses deterministic API mocks to check the dashboard, daily plan,
course next step, lesson code blocks, quiz feedback, and review feedback. Each test
also compares the page with a committed screenshot in `__screenshots__`.

## Run

```bash
cd e2e
npm install
npm run install-browsers
npm test

# Accept intentional visual changes after reviewing the output
npm run test:update
```

## Live smoke test

The separate smoke test runs against an already-running stack:

```bash
docker compose up -d --build
docker compose exec backend python -m scripts.seed
cd e2e
npm run test:smoke
```

- The smoke test uses the frontend's **development-mode** sign-in (shown when Firebase
  is not configured on the frontend). With real Firebase, swap the sign-in step
  for credentials or a stored auth state.
- See [../docs/09_TESTING.md](../docs/09_TESTING.md) for the overall test strategy.
