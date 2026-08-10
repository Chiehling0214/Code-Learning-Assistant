import { expect, test } from "@playwright/test";

/**
 * Sprint 8 smoke test: sign in → dashboard → open a course.
 *
 * Assumes the stack runs with Firebase unconfigured on the frontend, so the
 * Login page offers "Continue (development mode)". With real Firebase, replace
 * the sign-in step with credentials. Seed content first: `docker compose exec
 * backend python -m scripts.seed`.
 */
test("learner can sign in and open a course", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Learn by building, not by watching." })).toBeVisible();

  await page.goto("/login");
  await page.getByRole("button", { name: /continue \(development mode\)/i }).click();

  // Lands on the dashboard once the session is established.
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole("heading", { name: /Good to see you/ })).toBeVisible();

  // Open the seeded course.
  await page.getByRole("link", { name: /COURSE 01/i }).click();
  await expect(page.getByRole("heading", { name: "Course outline" })).toBeVisible();
});
