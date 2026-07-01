# End-to-end smoke test (Playwright)

An opt-in browser smoke test for the critical path: sign in → dashboard → open a
course. It runs against an **already-running** stack, so it is kept out of the
default CI job (which has no browser or live stack).

## Run

```bash
# 1. Start the stack and seed content
docker compose up -d --build
docker compose exec backend python -m scripts.seed

# 2. Install and run
cd e2e
npm install
npm run install-browsers
npm test           # or: BASE_URL=http://localhost:5173 npm test
```

## Notes

- The test uses the frontend's **development-mode** sign-in (shown when Firebase
  is not configured on the frontend). With real Firebase, swap the sign-in step
  for credentials or a stored auth state.
- See [../docs/09_TESTING.md](../docs/09_TESTING.md) for the overall test strategy.
