import { expect, test, type Page, type Route } from "@playwright/test";

const user = {
  id: "00000000-0000-0000-0000-000000000001",
  uid: "visual-user",
  email: "learner@example.com",
  display_name: "Alex",
  is_admin: false,
  onboarded: true,
};

const courses = [
  {
    id: "00000000-0000-0000-0000-000000000101",
    language_id: "00000000-0000-0000-0000-000000000201",
    title: "Java — Intermediate",
    slug: "java-intermediate",
    description: "Build confidence with collections, control flow, and practical exercises.",
    prerequisite_course_id: null,
    sequence_index: 0,
    recommendation_reason: "Start here based on your current ability",
  },
  {
    id: "00000000-0000-0000-0000-000000000102",
    language_id: "00000000-0000-0000-0000-000000000202",
    title: "C++ — Beginner",
    slug: "cpp-beginner",
    description: "Learn core C++ syntax through short, focused lessons.",
    prerequisite_course_id: "00000000-0000-0000-0000-000000000101",
    sequence_index: 1,
    recommendation_reason: "Continue after Java — Intermediate",
  },
];

const progress = {
  total: 18,
  completed: 7,
  percent: 39,
  streak: 3,
  resume: {
    course_id: courses[0].id,
    course_title: courses[0].title,
    course_slug: courses[0].slug,
    item_type: "lesson",
    item_id: "lesson-1",
    title: "Collections and Lists",
    path: "/lessons/lesson-1",
    updated_at: "2026-08-10T08:00:00Z",
  },
  courses: [
    {
      course_id: courses[0].id,
      title: courses[0].title,
      slug: courses[0].slug,
      total: 9,
      completed: 5,
      percent: 56,
      completed_items: [
        { item_type: "lesson", item_id: "lesson-1" },
        { item_type: "exercise", item_id: "exercise-1" },
        { item_type: "quiz", item_id: "quiz-1" },
      ],
      next_item: {
        item_type: "lesson",
        item_id: "lesson-2",
        title: "Maps and Sets",
        path: "/lessons/lesson-2",
      },
    },
    {
      course_id: courses[1].id,
      title: courses[1].title,
      slug: courses[1].slug,
      total: 9,
      completed: 2,
      percent: 22,
      completed_items: [],
      next_item: {
        item_type: "exercise",
        item_id: "exercise-1",
        title: "Even or Odd",
        path: "/exercises/exercise-1",
      },
    },
  ],
};

const quiz = {
  id: "quiz-1",
  lesson_id: "lesson-1",
  title: "Java Collections Check",
  slug: "collections-check",
  description: "Check your understanding before continuing.",
  questions: [
    {
      id: "question-1",
      prompt: "Which collection stores unique values?",
      type: "single",
      order_index: 0,
      choices: [
        { id: "choice-1", text: "ArrayList", order_index: 0 },
        { id: "choice-2", text: "HashSet", order_index: 1 },
      ],
    },
    {
      id: "question-2",
      prompt: "Which interface represents a key-value mapping?",
      type: "single",
      order_index: 1,
      choices: [
        { id: "choice-3", text: "Map", order_index: 0 },
        { id: "choice-4", text: "Queue", order_index: 1 },
      ],
    },
  ],
};

async function fulfill(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function mockApi(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("codepath.devSession", "1");
    Date.now = () => Date.parse("2026-08-10T10:00:00Z");
  });
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace("/api/v1", "");
    const method = request.method();

    if (path === "/me") return fulfill(route, user);
    if (path === "/me/courses") return fulfill(route, courses);
    if (path === "/me/tracks") {
      return fulfill(route, [
        {
          id: "track-java",
          language_id: courses[0].language_id,
          language_name: "Java",
          language_slug: "java",
          level: "intermediate",
          status: "active",
        },
        {
          id: "track-cpp",
          language_id: courses[1].language_id,
          language_name: "C++",
          language_slug: "cpp",
          level: "beginner",
          status: "active",
        },
      ]);
    }
    if (path === "/me/generation-jobs") {
      return fulfill(route, { unread_count: 0, jobs: [] });
    }
    if (path === "/admin/usage") {
      return fulfill(route, {
        ai_lessons: 8, pending: 2, approved: 5, hidden: 1,
        ai_exercises: 14, ai_quizzes: 8,
      });
    }
    if (path === "/admin/content") {
      return fulfill(route, {
        items: [{
          lesson_id: "lesson-1", title: "Collections and Lists",
          course_id: courses[0].id, course_title: courses[0].title,
          source: "ai", review_status: "pending", exercise_count: 2, quiz_count: 1,
        }],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });
    }
    if (path === "/admin/content/courses") {
      return fulfill(route, [{
        course_id: courses[0].id,
        title: courses[0].title,
        total: 1,
        pending: 1,
      }]);
    }
    if (path === "/admin/content/users") {
      return fulfill(route, [{
        user_id: user.id,
        email: user.email,
        display_name: user.display_name,
        course_count: 2,
        lesson_count: 8,
        pending: 2,
      }]);
    }
    if (path === "/admin/content/lessons/lesson-1/preview") {
      return fulfill(route, {
        lesson_id: "lesson-1",
        title: "Collections and Lists",
        content: "Java collections provide reusable data structures.",
        exercises: [{
          id: "exercise-1",
          title: "Deduplicate values",
          language: "java",
          prompt: "Return unique values in their original order.",
          starter_code: "class Main { }",
          test_spec: { cases: [{ input: "1 1 2", expected: "1 2" }] },
        }],
        quizzes: [{
          id: "quiz-1",
          title: "Collections check",
          questions: [{
            prompt: "Which type stores unique values?",
            explanation: "A Set stores unique values.",
            choices: [
              { text: "Set", is_correct: true },
              { text: "List", is_correct: false },
            ],
          }],
        }],
      });
    }
    if (/^\/admin\/content\/(lesson|exercise|quiz)\/[^/]+\/regenerate$/.test(path) && method === "POST") {
      return fulfill(route, null);
    }
    if (/^\/admin\/content\/(lesson|exercise|quiz)\/[^/]+\/versions$/.test(path)) {
      const itemType = path.split("/")[3];
      const itemId = path.split("/")[4];
      return fulfill(route, {
        current_snapshot: itemType === "lesson"
          ? { title: "Collections and Lists", content: "Current lesson content" }
          : { title: "Current item", prompt: "Current prompt" },
        versions: [{
          id: `version-${itemType}`,
          item_type: itemType,
          item_id: itemId,
          created_by: user.id,
          created_at: "2026-08-10T08:00:00Z",
          snapshot: itemType === "lesson"
            ? { title: "Collections and Lists", content: "Saved lesson content" }
            : { title: "Saved item", prompt: "Saved prompt" },
        }],
      });
    }
    if (path === "/admin/content-reports") {
      return fulfill(route, [{
        id: "report-1", user_id: user.id, item_type: "exercise",
        item_id: "exercise-1", reason: "broken",
        details: "The sample output and hidden test disagree.", status: "open",
        created_at: "2026-08-10T08:00:00Z", updated_at: "2026-08-10T08:00:00Z",
      }]);
    }
    if (path === "/admin/generation-jobs") {
      return fulfill(route, [{
        id: "job-1", user_email: "learner@example.com", language: "Java",
        kind: "course_set", status: "running", completed: 7, total: 18,
        attempt_count: 1, max_attempts: 3, error: null,
        cancel_requested: false, created_at: "2026-08-10T08:00:00Z",
        updated_at: "2026-08-10T08:05:00Z",
      }]);
    }
    if (path === "/admin/monitoring") {
      return fulfill(route, {
        window_hours: 24,
        counts: {
          frontend_error: 1,
          api_5xx: 2,
          ai_generation_failure: 1,
          worker_retry: 1,
        },
        recent: [{
          id: "event-1",
          category: "worker_retry",
          level: "warning",
          message: "Generation job scheduled for retry in 5 seconds",
          details: { job_id: "job-1" },
          created_at: "2026-08-10T08:10:00Z",
        }],
      });
    }
    if (/^\/me\/generation-jobs\/[^/]+\/seen$/.test(path)) {
      return fulfill(route, {
        id: path.split("/")[3],
        track_id: "track-java",
        status: "done",
        total: 9,
        completed: 9,
        course_id: courses[0].id,
        error: null,
        created_at: "2026-08-10T09:00:00Z",
        updated_at: "2026-08-10T10:00:00Z",
        seen_at: "2026-08-10T10:05:00Z",
      });
    }
    if (path === "/languages") {
      return fulfill(route, [
        { id: courses[0].language_id, name: "Java", slug: "java" },
        { id: courses[1].language_id, name: "C++", slug: "cpp" },
      ]);
    }
    if (path === "/progress" && method === "GET") return fulfill(route, progress);
    if (path === "/progress/activity") return fulfill(route, progress.resume);
    if (path === "/me/mastery") {
      return fulfill(route, {
        language: "java",
        assessment: {
          current_level: "intermediate",
          evidence_level: "intermediate",
          attempts: 12,
          correct: 9,
          accuracy: 75,
          source: "course performance",
          next_evaluation:
            "Your level is recalculated after every current course is completed; the next three courses use that result.",
        },
        topics: [
          {
            topic: "Collections and Lists",
            attempts: 7,
            correct: 6,
            correct_rate: 0.86,
            level: "strong",
            lesson_id: "lesson-1",
          },
          {
            topic: "Maps and Sets",
            attempts: 5,
            correct: 3,
            correct_rate: 0.6,
            level: "ok",
            lesson_id: "lesson-2",
          },
        ],
      });
    }
    if (path === "/today") {
      return fulfill(route, {
        reviews_due: 1,
        items: [
          { type: "lesson", id: "lesson-1", title: "Collections and Lists", course_slug: "java-intermediate" },
          { type: "exercise", id: "exercise-1", title: "Even or Odd", course_slug: "cpp-beginner" },
          { type: "quiz", id: "quiz-1", title: "Java Collections Check", course_slug: "java-intermediate" },
        ],
      });
    }
    if (path === "/lessons/lesson-1") {
      return fulfill(route, {
        id: "lesson-1",
        course_id: courses[0].id,
        title: "Collections and Lists",
        slug: "collections-and-lists",
        order_index: 1,
        content: "Java collections provide reusable data structures.\n\n```java\nList<String> names = new ArrayList<>();\nnames.add(\"Ada\");\n```",
      });
    }
    if (path === "/lessons/lesson-1/adjustments/preview" && method === "POST") {
      return fulfill(route, {
        adjustment_id: "adjustment-1",
        lesson_id: "lesson-1",
        title: "Collections and Lists",
        content: "## A practical view\n\nUse a shopping cart to understand the same collection topic.\n\n```java\nList<String> cart = new ArrayList<>();\n```",
      });
    }
    if (path === "/lessons/lesson-1/adjustments/adjustment-1/apply" && method === "POST") {
      return fulfill(route, {
        id: "lesson-1",
        course_id: courses[0].id,
        title: "Collections and Lists",
        slug: "collections-and-lists",
        order_index: 1,
        content: "## A practical view\n\nUse a shopping cart to understand the same collection topic.\n\n```java\nList<String> cart = new ArrayList<>();\n```",
      });
    }
    if (path === "/lessons/lesson-1/exercises" || path === "/lessons/lesson-1/quizzes") {
      return fulfill(route, []);
    }
    if (path === "/courses/java-intermediate") {
      return fulfill(route, {
        ...courses[0],
        lessons: [
          {
            id: "lesson-1",
            title: "Collections and Lists",
            slug: "collections-and-lists",
            order_index: 0,
            exercises: [
              { id: "exercise-1", title: "Deduplicate values", slug: "deduplicate-values" },
            ],
            quizzes: [{ id: "quiz-1", title: "Collections check", slug: "collections-check" }],
          },
          {
            id: "lesson-2",
            title: "Maps and Sets",
            slug: "maps-and-sets",
            order_index: 1,
            exercises: [{ id: "exercise-2", title: "Word frequencies", slug: "word-frequencies" }],
            quizzes: [{ id: "quiz-2", title: "Maps check", slug: "maps-check" }],
          },
        ],
      });
    }
    if (path === `/courses/${courses[0].id}/extension`) {
      return fulfill(route, { course_id: courses[0].id, lesson_count: 2, completion_percent: 56, can_extend: false });
    }
    if (path === `/courses/${courses[0].id}/chat`) return fulfill(route, { messages: [] });
    if (path === "/exercises/exercise-1" && method === "GET") {
      return fulfill(route, {
        id: "exercise-1",
        lesson_id: "lesson-1",
        language: "java",
        title: "Deduplicate values",
        slug: "deduplicate-values",
        prompt: "Return the unique values while preserving their first-seen order.",
        starter_code: "import java.util.*;\n\nclass Main {\n  public static void main(String[] args) {\n    // your code\n  }\n}",
        sample_cases: [{ input: "1 2 1 3", expected: "1 2 3" }],
      });
    }
    if (path === "/exercises/exercise-1/draft" && method === "GET") {
      return fulfill(route, {
        exercise_id: "exercise-1",
        code: "import java.util.*;\n\nclass Main {\n  public static void main(String[] args) {\n    // synced draft\n  }\n}",
        updated_at: "2026-08-10T10:00:00Z",
      });
    }
    if (path === "/exercises/exercise-1/draft" && method === "PUT") {
      const body = request.postDataJSON() as { code: string };
      return fulfill(route, {
        exercise_id: "exercise-1",
        code: body.code,
        updated_at: "2026-08-10T10:01:00Z",
      });
    }
    if (path === "/exercises/exercise-1/submissions") {
      return fulfill(route, [
        {
          id: "submission-2",
          exercise_id: "exercise-1",
          code: "class Main { /* second attempt */ }",
          status: "passed",
          result: { verdict: "passed", passed: 2, total: 2, tests: [] },
          created_at: "2026-08-10T09:15:00Z",
        },
        {
          id: "submission-1",
          exercise_id: "exercise-1",
          code: "class Main { /* first attempt */ }",
          status: "failed",
          result: {
            verdict: "failed",
            passed: 1,
            total: 2,
            tests: [
              { index: 0, passed: true, status: "Accepted", input: "1 2 1", expected: "1 2", actual: "1 2", stderr: "" },
              { index: 1, passed: false, status: "Wrong Answer", input: "3 3 2", expected: "3 2", actual: "3 3 2", stderr: "" },
            ],
          },
          created_at: "2026-08-10T09:00:00Z",
        },
      ]);
    }
    if (path === "/submissions/submission-1") {
      return fulfill(route, {
        id: "submission-1",
        exercise_id: "exercise-1",
        code: "class Main { /* first attempt */ }",
        status: "failed",
        result: {
          verdict: "failed",
          passed: 1,
          total: 2,
          tests: [
            { index: 0, passed: true, status: "Accepted", input: "1 2 1", expected: "1 2", actual: "1 2", stderr: "" },
            { index: 1, passed: false, status: "Wrong Answer", input: "3 3 2", expected: "3 2", actual: "3 3 2", stderr: "" },
          ],
        },
        created_at: "2026-08-10T09:00:00Z",
      });
    }
    if (path === "/quizzes/quiz-1" && method === "GET") return fulfill(route, quiz);
    if (path === "/quizzes/quiz-1/submit") {
      return fulfill(route, {
        attempt_id: "attempt-1",
        score: 1,
        total: 2,
        results: [
          { question_id: "question-1", correct: false, selected_choice_id: "choice-1", correct_choice_id: "choice-2", explanation: "A HashSet stores each value at most once." },
          { question_id: "question-2", correct: true, selected_choice_id: "choice-3", correct_choice_id: "choice-3", explanation: "Map is Java's key-value interface." },
        ],
      });
    }
    if (path === "/me/review") {
      return fulfill(route, {
        due_count: 1,
        items: [{
          id: "review-1",
          source: "quiz",
          payload: {
            kind: "mcq",
            prompt: "Which collection stores unique values?",
            quiz_title: "Java Collections Check",
            explanation: "A HashSet stores each value at most once.",
            choices: [
              { id: "choice-1", text: "ArrayList", is_correct: false },
              { id: "choice-2", text: "HashSet", is_correct: true },
            ],
          },
          interval_days: 1,
          due_at: "2026-08-10T08:00:00Z",
          lapses: 1,
          passes: 0,
          retired: false,
          note: "",
        }],
      });
    }
    if (path === "/me/review/review-1/answer") return fulfill(route, { ok: true });
    if (path === "/me/review/all") {
      return fulfill(route, {
        items: [{
          id: "review-1",
          source: "quiz",
          payload: {
            kind: "mcq",
            prompt: "Which collection stores unique values?",
            quiz_title: "Java Collections Check",
            explanation: "A HashSet stores each value at most once.",
            choices: [
              { id: "choice-1", text: "ArrayList", is_correct: false },
              { id: "choice-2", text: "HashSet", is_correct: true },
            ],
          },
          interval_days: 1,
          due_at: "2026-08-11T08:00:00Z",
          lapses: 1,
          passes: 0,
          retired: false,
          note: "Sets keep one copy of each value.",
        }],
      });
    }
    return fulfill(route, { detail: `Unhandled mock route: ${method} ${path}` }, 404);
  });
}

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("dashboard visual", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Good to see you, Alex." })).toBeVisible();
  await expect(page.getByRole("link", { name: /Resume learning/ })).toHaveAttribute(
    "href",
    "/lessons/lesson-1",
  );
  await expect(page.getByRole("link", { name: "View course" }).first()).toHaveAttribute(
    "href",
    "/courses/java-intermediate",
  );
  await expect(page).toHaveScreenshot("dashboard.png", { animations: "disabled", fullPage: true });
});

test("library search and filters visual", async ({ page }) => {
  await page.goto("/library");
  await expect(page.getByRole("heading", { name: "All courses" })).toBeVisible();
  await expect(page.getByPlaceholder("Search courses or languages")).toBeVisible();
  await expect(page.getByRole("link", { name: "View course" })).toHaveCount(2);
  await expect(page).toHaveScreenshot("library.png", { animations: "disabled", fullPage: true });
});

test("course generation notification visual", async ({ page }) => {
  await page.route("**/api/v1/me/generation-jobs", (route) =>
    fulfill(route, {
      unread_count: 1,
      jobs: [
        {
          id: "job-ready",
          track_id: "track-java",
          status: "done",
          total: 9,
          completed: 9,
          course_id: courses[0].id,
          error: null,
          created_at: "2026-08-10T09:00:00Z",
          updated_at: "2026-08-10T10:00:00Z",
          seen_at: null,
        },
      ],
    }),
  );
  await page.goto("/dashboard");
  await page.getByRole("button", { name: /Generation notifications, 1 unread/ }).click();
  await expect(page.getByText("Java courses are ready")).toBeVisible();
  await expect(page).toHaveScreenshot("generation-notification.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("today visual", async ({ page }) => {
  await page.goto("/today");
  await expect(page.getByRole("heading", { name: "A few good steps for today." })).toBeVisible();
  await expect(page).toHaveScreenshot("today.png", { animations: "disabled", fullPage: true });
});

test("AI level explanation visual", async ({ page }) => {
  await page.goto("/progress");
  await expect(page.getByText("AI-assessed level")).toBeVisible();
  await expect(page.getByText("9/12 · 75%")).toBeVisible();
  await page.getByText("How the level is decided").click();
  await expect(page).toHaveScreenshot("progress-assessment.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("lesson code visual", async ({ page }) => {
  await page.goto("/lessons/lesson-1");
  await expect(page.getByRole("button", { name: "Copy code" })).toBeVisible();
  await expect(page).toHaveScreenshot("lesson-code.png", { animations: "disabled", fullPage: true });

  await page.getByRole("button", { name: "Adjust this lesson" }).click();
  const dialog = page.getByRole("dialog", { name: "Adjust this lesson" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: /Add practical examples/ }).click();
  await dialog.getByLabel("Anything specific?").fill("Use a shopping-cart example.");
  const previewRequestPromise = page.waitForRequest((request) =>
    request.url().endsWith("/lessons/lesson-1/adjustments/preview"),
  );
  await dialog.getByRole("button", { name: "Generate preview" }).click();
  const previewRequest = await previewRequestPromise;
  expect(previewRequest.postDataJSON()).toEqual({
    preset: "examples",
    instructions: "Use a shopping-cart example.",
  });
  await expect(dialog.getByText("Original lesson", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Adjusted preview", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Use a shopping cart to understand the same collection topic.")).toBeVisible();
  await expect(dialog).toHaveScreenshot("lesson-adjustment-preview.png", {
    animations: "disabled",
  });
  await dialog.getByRole("button", { name: "Keep new version" }).click();
  await expect(page.getByText("Your adjusted lesson is now active. The original version was saved.")).toBeVisible();
  await expect(page.getByText("Use a shopping cart to understand the same collection topic.")).toBeVisible();
});

test("course next step visual", async ({ page }) => {
  let activityRequests = 0;
  page.on("request", (request) => {
    if (request.url().includes("/progress/activity")) activityRequests += 1;
  });
  await page.goto("/courses/java-intermediate");
  await expect(page.getByText("Next step")).toBeVisible();
  await expect(page.getByRole("link", { name: /Continue/ })).toBeVisible();
  expect(activityRequests).toBe(0);
  await expect(page).toHaveScreenshot("course-next-step.png", { animations: "disabled", fullPage: true });
});

test("completed course generation visual", async ({ page }) => {
  const completedProgress = {
    ...progress,
    courses: progress.courses.map((item, index) => index === 0 ? {
      ...item,
      completed: item.total,
      percent: 100,
      next_item: null,
      completed_items: [
        { item_type: "lesson", item_id: "lesson-1" },
        { item_type: "exercise", item_id: "exercise-1" },
        { item_type: "quiz", item_id: "quiz-1" },
        { item_type: "lesson", item_id: "lesson-2" },
        { item_type: "exercise", item_id: "exercise-2" },
        { item_type: "quiz", item_id: "quiz-2" },
      ],
    } : item),
  };
  await page.route("**/api/v1/progress", (route) => fulfill(route, completedProgress));
  await page.route(`**/api/v1/courses/${courses[0].id}/extension`, (route) =>
    fulfill(route, { course_id: courses[0].id, lesson_count: 2, completion_percent: 100, can_extend: false }),
  );
  await page.route(`**/api/v1/courses/${courses[0].id}/advance`, (route) =>
    fulfill(route, {
      id: "generation-next",
      track_id: "track-java",
      status: "pending",
      total: 9,
      completed: 0,
      course_id: null,
      error: null,
    }, 202),
  );
  await page.route("**/api/v1/me/tracks/track-java/generation", (route) =>
    fulfill(route, {
      id: "generation-next",
      track_id: "track-java",
      status: "running",
      total: 9,
      completed: 3,
      course_id: null,
      error: null,
    }),
  );
  await page.goto("/courses/java-intermediate");
  await expect(page.getByText("Building your next three courses")).toBeVisible();
  await expect(page.getByText("3 of 9 lessons prepared")).toBeVisible();
  await expect(page).toHaveScreenshot("course-generation.png", { animations: "disabled", fullPage: true });
});

test("exercise workspace and history visual", async ({ page }) => {
  await page.goto("/exercises/exercise-1");
  await expect(page.locator(".monaco-editor")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("Saved to account")).toBeVisible();
  await page.getByRole("button", { name: /1\/2 tests passed/i }).click();
  await expect(page.getByText("Submitted code")).toBeVisible();
  await expect(page.getByText("Wrong Answer")).toBeVisible();
  const selectedCodeStyle = await page.locator(".dark-code-selection code").evaluate((element) => {
    const style = getComputedStyle(element, "::selection");
    return { backgroundColor: style.backgroundColor, color: style.color };
  });
  expect(selectedCodeStyle).toEqual({
    backgroundColor: "rgb(72, 103, 121)",
    color: "rgb(248, 250, 252)",
  });
  const compareBoxes = page.getByRole("checkbox", { name: /Compare submission/ });
  await compareBoxes.nth(0).check();
  await compareBoxes.nth(1).check();
  await expect(page.getByText("Attempt comparison")).toBeVisible();
  await expect(page.locator("main")).toHaveScreenshot("exercise-workspace.png", {
    animations: "disabled",
  });
});

test("quiz feedback visual and manual progression", async ({ page }) => {
  await page.goto("/quizzes/quiz-1");
  await page.getByRole("button", { name: "ArrayList" }).click();
  await page.getByRole("button", { name: "Next question" }).click();
  await expect(page.getByText("Question 2 of 2")).toBeVisible();
  await page.getByRole("button", { name: "Map" }).click();
  await page.getByRole("button", { name: "Submit answers" }).click();
  await expect(page.getByText("Incorrect")).toBeVisible();
  await expect(page.getByRole("button", { name: "Next answer" })).toBeVisible();
  await expect(page).toHaveScreenshot("quiz-feedback.png", { animations: "disabled", fullPage: true });
});

test("review feedback visual waits for Next", async ({ page }) => {
  await page.goto("/review");
  await page.getByRole("button", { name: "ArrayList" }).click();
  await expect(page.getByText(/Not yet/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Next" })).toBeVisible();
  await expect(page).toHaveScreenshot("review-feedback.png", { animations: "disabled", fullPage: true });
});

test("mistakes notebook filters and notes visual", async ({ page }) => {
  await page.goto("/review");
  await page.getByRole("tab", { name: "Mistakes notebook" }).click();
  await expect(page.getByPlaceholder("Search mistakes…")).toBeVisible();
  await page.getByText("Which collection stores unique values?").click();
  await expect(page.getByLabel("My note")).toHaveValue("Sets keep one copy of each value.");
  await expect(page).toHaveScreenshot("mistakes-notebook.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("mobile navigation stays usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/dashboard");
  const navigation = page.getByRole("navigation", { name: "Primary navigation" });
  await expect(navigation).toBeVisible();
  await expect(navigation.getByRole("link", { name: "Library" })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  await expect(page).toHaveScreenshot("dashboard-mobile.png", {
    animations: "disabled",
    fullPage: true,
  });
});

test("admin AI operations visual", async ({ page }) => {
  user.is_admin = true;
  try {
    await page.goto("/admin");
    await expect(page.getByText("AI operations")).toBeVisible();
    await expect(page.getByText("Choose a learner")).toBeVisible();
    await page.getByRole("button", { name: /Alex.*learner@example.com/ }).click();
    await expect(page.getByText("Collections and Lists")).toBeVisible();
    await page.getByRole("button", { name: "Preview" }).click();
    await expect(page.getByRole("button", { name: "Regenerate exercise" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Regenerate quiz" })).toBeVisible();
    await page.getByRole("button", { name: "Regenerate exercise" }).click();
    const regenerateDialog = page.getByRole("alertdialog", { name: "Regenerate this exercise?" });
    await expect(regenerateDialog).toBeVisible();
    const requestPromise = page.waitForRequest((request) =>
      request.url().endsWith("/admin/content/exercise/exercise-1/regenerate"),
    );
    await regenerateDialog.getByLabel("Adjustment instructions").fill(
      "Use a clearer real-world example and emphasize edge cases.",
    );
    await regenerateDialog.getByRole("button", { name: "Regenerate", exact: true }).click();
    const regenerateRequest = await requestPromise;
    expect(regenerateRequest.postDataJSON()).toEqual({
      instructions: "Use a clearer real-world example and emphasize edge cases.",
    });
    await expect(page.getByText("Content regenerated successfully and returned to Pending review.")).toBeVisible();
    await page.getByRole("button", { name: "Compare", exact: true }).first().click();
    const comparison = page.getByRole("dialog", { name: "Lesson version comparison" });
    await expect(comparison).toBeVisible();
    await expect(comparison.getByText("Current version", { exact: true })).toBeVisible();
    await expect(comparison.getByText("Saved version", { exact: true })).toBeVisible();
    await expect(comparison.getByText("Current lesson content")).toBeVisible();
    await expect(comparison.getByText("Saved lesson content")).toBeVisible();
    await expect(comparison).toHaveScreenshot("admin-version-compare.png", {
      animations: "disabled",
    });
    await page.getByRole("button", { name: "Close comparison dialog" }).click();
    await page.getByRole("button", { name: "Learner reports" }).click();
    await expect(page.getByText("The sample output and hidden test disagree.")).toBeVisible();
    await page.getByRole("button", { name: "Generation jobs" }).click();
    await expect(page.getByRole("cell", { name: "learner@example.com" })).toBeVisible();
    await expect(page).toHaveScreenshot("admin-generation-jobs.png", {
      animations: "disabled",
      fullPage: true,
    });
    await page.getByRole("button", { name: "Monitoring" }).click();
    await expect(page.getByText("Generation job scheduled for retry in 5 seconds")).toBeVisible();
  } finally {
    user.is_admin = false;
  }
});
