import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  HeartPulse,
  History,
  RefreshCw,
  Search,
  UserRound,
} from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { ContentVersionHistory } from "@/components/ContentVersionHistory";
import { Markdown } from "@/components/Markdown";
import { RegenerateDialog } from "@/components/RegenerateDialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useAdminContent,
  useAdminContentPreview,
  useAdminGenerationJobs,
  useAdminMonitoring,
  useAdminReviewCourses,
  useAdminReviewUsers,
  useAdminUsage,
  useContentReports,
  useGenerationJobAction,
  useMarkCourseReviewed,
  useRegenerateContent,
  useSetContentReportStatus,
  useSetLessonReview,
  type ReviewItem,
} from "@/features/admin/hooks";
import { useSessionStore } from "@/store/session";

type Tab = "content" | "reports" | "jobs" | "monitoring";
type ReviewFilter = "all" | ReviewItem["review_status"];
type RegenerateTarget = {
  itemType: "lesson" | "exercise" | "quiz";
  itemId: string;
  title: string;
};
const STATUS_STYLES: Record<string, string> = {
  approved: "text-green-700",
  done: "text-green-700",
  pending: "text-amber-700",
  running: "text-blue-700",
  error: "text-destructive",
  cancelled: "text-muted-foreground",
  hidden: "text-muted-foreground line-through",
};

function ReviewStatus({ status }: { status: "approved" | "pending" | "hidden" }) {
  if (status === "approved") {
    return (
      <span className="inline-flex items-center gap-1 text-green-700">
        <CheckCircle2 className="size-3.5" aria-hidden="true" />
        Reviewed
      </span>
    );
  }

  return <span className={STATUS_STYLES[status]}>{status}</span>;
}

function UsageSummary() {
  const { data: usage } = useAdminUsage();
  if (!usage) return null;
  return (
    <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
      {Object.entries({
        "AI lessons": usage.ai_lessons,
        Pending: usage.pending,
        Reviewed: usage.approved,
        Hidden: usage.hidden,
        Exercises: usage.ai_exercises,
        Quizzes: usage.ai_quizzes,
      }).map(([label, value]) => (
        <div key={label} className="rounded-md border px-3 py-2 text-center">
          <div className="text-xl font-semibold">{value}</div>
          <div className="text-xs text-muted-foreground">{label}</div>
        </div>
      ))}
    </div>
  );
}

function ReviewPreviewPanel({ lessonId }: { lessonId: string }) {
  const preview = useAdminContentPreview(lessonId);
  const regenerate = useRegenerateContent();
  const [regenerateTarget, setRegenerateTarget] = useState<RegenerateTarget | null>(null);
  if (preview.isLoading) {
    return <p className="border-t px-3 py-4 text-sm text-muted-foreground">Loading preview…</p>;
  }
  if (preview.isError || !preview.data) {
    return (
      <p role="alert" className="border-t px-3 py-4 text-sm text-destructive">
        Could not load this content preview.
      </p>
    );
  }

  return (
    <div className="max-h-[34rem] space-y-5 overflow-y-auto border-t bg-background/45 p-4">
      {regenerate.isSuccess && (
        <p role="status" className="rounded-md bg-green-700/10 px-3 py-2 text-sm text-green-800">
          Content regenerated successfully and returned to Pending review.
        </p>
      )}
      {regenerate.isError && (
        <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {regenerate.error instanceof Error
            ? regenerate.error.message
            : "Could not regenerate this content."}
        </p>
      )}
      <ContentVersionHistory itemType="lesson" itemId={lessonId} />
      <section>
        <p className="page-kicker mb-2">Lesson content</p>
        <Markdown content={preview.data.content} />
      </section>
      {preview.data.exercises.length > 0 && (
        <section className="space-y-3">
          <p className="page-kicker">Exercises</p>
          {preview.data.exercises.map((exercise) => (
            <div key={exercise.id} className="rounded-lg border bg-card p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-medium">{exercise.title}</p>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={regenerate.isPending}
                  onClick={() => setRegenerateTarget({
                    itemType: "exercise",
                    itemId: exercise.id,
                    title: exercise.title,
                  })}
                >
                  <RefreshCw className="size-3.5" />
                  Regenerate exercise
                </Button>
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                {exercise.prompt}
              </p>
              {exercise.starter_code && (
                <pre className="mt-3 overflow-x-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">
                  <code>{exercise.starter_code}</code>
                </pre>
              )}
              <details className="mt-3 text-xs text-muted-foreground">
                <summary className="cursor-pointer font-medium">Test specification</summary>
                <pre className="mt-2 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(exercise.test_spec, null, 2)}
                </pre>
              </details>
              <details className="mt-3">
                <summary className="cursor-pointer text-xs font-medium text-muted-foreground">
                  Version history
                </summary>
                <div className="mt-2">
                  <ContentVersionHistory itemType="exercise" itemId={exercise.id} />
                </div>
              </details>
            </div>
          ))}
        </section>
      )}
      {preview.data.quizzes.length > 0 && (
        <section className="space-y-3">
          <p className="page-kicker">Quizzes</p>
          {preview.data.quizzes.map((quiz) => (
            <div key={quiz.id} className="rounded-lg border bg-card p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-medium">{quiz.title}</p>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={regenerate.isPending}
                  onClick={() => setRegenerateTarget({
                    itemType: "quiz",
                    itemId: quiz.id,
                    title: quiz.title,
                  })}
                >
                  <RefreshCw className="size-3.5" />
                  Regenerate quiz
                </Button>
              </div>
              <div className="mt-3 space-y-4">
                {quiz.questions.map((question, questionIndex) => (
                  <div key={`${quiz.id}-${questionIndex}`} className="text-sm">
                    <p className="font-medium">
                      {questionIndex + 1}. {question.prompt}
                    </p>
                    <ul className="mt-2 space-y-1 text-muted-foreground">
                      {question.choices.map((choice, choiceIndex) => (
                        <li
                          key={`${quiz.id}-${questionIndex}-${choiceIndex}`}
                          className={choice.is_correct ? "flex items-center gap-1.5 text-green-700" : ""}
                        >
                          {choice.is_correct && <CheckCircle2 className="size-3.5 shrink-0" />}
                          {choice.text}
                        </li>
                      ))}
                    </ul>
                    {question.explanation && (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Explanation: {question.explanation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
              <details className="mt-3">
                <summary className="cursor-pointer text-xs font-medium text-muted-foreground">
                  Version history
                </summary>
                <div className="mt-2">
                  <ContentVersionHistory itemType="quiz" itemId={quiz.id} />
                </div>
              </details>
            </div>
          ))}
        </section>
      )}
      <RegenerateDialog
        open={Boolean(regenerateTarget)}
        itemType={regenerateTarget?.itemType ?? "lesson"}
        itemTitle={regenerateTarget?.title ?? "this content"}
        pending={regenerate.isPending}
        onCancel={() => setRegenerateTarget(null)}
        onConfirm={(instructions) => {
          if (!regenerateTarget) return;
          regenerate.mutate(
            {
              itemType: regenerateTarget.itemType,
              itemId: regenerateTarget.itemId,
              instructions,
            },
            { onSuccess: () => setRegenerateTarget(null) },
          );
        }}
      />
    </div>
  );
}

function ReviewList() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [userQuery, setUserQuery] = useState("");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<ReviewFilter>("pending");
  const [courseFilter, setCourseFilter] = useState("all");
  const [page, setPage] = useState(1);
  const deferredQuery = useDeferredValue(query);
  const content = useAdminContent({
    status: statusFilter === "all" ? undefined : statusFilter,
    query: deferredQuery,
    courseId: courseFilter === "all" ? undefined : courseFilter,
    userId: selectedUserId ?? undefined,
    page,
    enabled: Boolean(selectedUserId),
  });
  const usersQuery = useAdminReviewUsers();
  const users = useMemo(() => usersQuery.data ?? [], [usersQuery.data]);
  const { data: courses = [] } = useAdminReviewCourses("ai", selectedUserId ?? undefined);
  const items = useMemo(() => content.data?.items ?? [], [content.data?.items]);
  const selectedUser = users.find((user) => user.user_id === selectedUserId);
  const filteredUsers = useMemo(() => {
    const normalized = userQuery.trim().toLocaleLowerCase();
    if (!normalized) return users;
    return users.filter(
      (user) =>
        (user.display_name ?? "").toLocaleLowerCase().includes(normalized) ||
        user.email.toLocaleLowerCase().includes(normalized),
    );
  }, [userQuery, users]);
  const setReview = useSetLessonReview();
  const regenerate = useRegenerateContent();
  const markCourseReviewed = useMarkCourseReviewed();
  const [expandedLessonId, setExpandedLessonId] = useState<string | null>(null);
  const [regenerateTarget, setRegenerateTarget] = useState<RegenerateTarget | null>(null);
  const [bulkReviewTarget, setBulkReviewTarget] = useState<{
    courseId: string;
    title: string;
    count: number;
  } | null>(null);
  useEffect(() => {
    if (content.data && page > content.data.total_pages) {
      setPage(content.data.total_pages);
    }
  }, [content.data, page]);
  const groupedItems = useMemo(() => {
    const groups = new Map<string, { title: string; items: ReviewItem[] }>();
    for (const item of items) {
      const group = groups.get(item.course_id) ?? { title: item.course_title, items: [] };
      group.items.push(item);
      groups.set(item.course_id, group);
    }
    return [...groups.entries()].map(([courseId, group]) => ({ courseId, ...group }));
  }, [items]);

  if (usersQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading learners…</p>;
  }
  if (!selectedUserId) {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-base font-semibold">Choose a learner</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Review one learner&apos;s personalized courses at a time.
          </p>
        </div>
        <label className="relative block max-w-lg">
          <span className="sr-only">Search learners</span>
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={userQuery}
            onChange={(event) => setUserQuery(event.target.value)}
            placeholder="Search by name or email"
            className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
          />
        </label>
        {filteredUsers.length === 0 ? (
          <p className="rounded-md border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
            {userQuery.trim() ? "No users match your search." : "No users found."}
          </p>
        ) : (
          <div className="grid gap-2 lg:grid-cols-2">
            {filteredUsers.map((user) => (
              <button
                key={user.user_id}
                type="button"
                onClick={() => {
                  setSelectedUserId(user.user_id);
                  setPage(1);
                }}
                className="flex items-center gap-3 rounded-lg border bg-card p-4 text-left transition-colors hover:border-primary/30 hover:bg-muted/40"
              >
                <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                  <UserRound className="size-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold">
                    {user.display_name || "Unnamed learner"}
                  </span>
                  <span className="block truncate text-xs text-muted-foreground">{user.email}</span>
                </span>
                <span className="shrink-0 text-right text-xs text-muted-foreground">
                  <span className="block">{user.course_count} courses</span>
                  <span className="block">{user.pending} pending</span>
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (content.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/25 p-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-background text-muted-foreground">
            <UserRound className="size-4" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">
              {selectedUser?.display_name || "Unnamed learner"}
            </p>
            <p className="truncate text-xs text-muted-foreground">{selectedUser?.email}</p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setSelectedUserId(null);
            setCourseFilter("all");
            setQuery("");
            setPage(1);
            setExpandedLessonId(null);
          }}
        >
          <ArrowLeft className="size-3.5" />
          Change learner
        </Button>
      </div>
      <div className="grid gap-2 md:grid-cols-[minmax(14rem,1fr)_12rem_14rem]">
        <label className="relative">
          <span className="sr-only">Search review content</span>
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder="Search lessons or courses"
            className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
          />
        </label>
        <select
          value={statusFilter}
          onChange={(event) => {
            setStatusFilter(event.target.value as ReviewFilter);
            setPage(1);
          }}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          aria-label="Filter by review status"
        >
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Reviewed</option>
          <option value="hidden">Hidden</option>
        </select>
        <select
          value={courseFilter}
          onChange={(event) => {
            setCourseFilter(event.target.value);
            setPage(1);
          }}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          aria-label="Filter by course"
        >
          <option value="all">All courses</option>
          {courses.map((course) => (
            <option key={course.course_id} value={course.course_id}>
              {course.title} · {course.course_id.slice(0, 6).toUpperCase()} · {course.total} lesson(s)
            </option>
          ))}
        </select>
      </div>
      {regenerate.isSuccess && (
        <p role="status" className="rounded-md bg-green-700/10 px-3 py-2 text-sm text-green-800">
          Content regenerated successfully. It is pending review again.
        </p>
      )}
      {regenerate.isError && (
        <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {regenerate.error instanceof Error
            ? regenerate.error.message
            : "Could not regenerate this content. Please try again."}
        </p>
      )}
      {markCourseReviewed.isSuccess && (
        <p role="status" className="rounded-md bg-green-700/10 px-3 py-2 text-sm text-green-800">
          Marked {markCourseReviewed.data.reviewed} pending lesson(s) as reviewed.
        </p>
      )}
      {markCourseReviewed.isError && (
        <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {markCourseReviewed.error instanceof Error
            ? markCourseReviewed.error.message
            : "Could not review this course. Please try again."}
        </p>
      )}
      {groupedItems.length === 0 ? (
        <p className="rounded-md border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
          No content matches these filters.
        </p>
      ) : (
        <div className="space-y-5">
          {groupedItems.map((group) => {
            const course = courses.find((option) => option.course_id === group.courseId);
            const pendingCount = course?.pending ?? group.items.filter(
              (item) => item.review_status === "pending",
            ).length;
            const reviewingThisCourse =
              markCourseReviewed.isPending && markCourseReviewed.variables === group.courseId;
            return (
              <section key={group.courseId} className="space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold">{group.title}</h3>
                    <p className="text-xs text-muted-foreground">
                      ID {group.courseId.slice(0, 6).toUpperCase()} · {group.items.length} lesson(s) shown
                      {pendingCount > 0 ? ` · ${pendingCount} pending` : ""}
                    </p>
                  </div>
                  {pendingCount > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={markCourseReviewed.isPending}
                      onClick={() => setBulkReviewTarget({
                        courseId: group.courseId,
                        title: group.title,
                        count: pendingCount,
                      })}
                    >
                      <CheckCircle2 className="size-3.5" />
                      {reviewingThisCourse ? "Reviewing…" : "Mark all reviewed"}
                    </Button>
                  )}
                </div>
                <ul className="space-y-2">
                  {group.items.map((item) => {
                    const expanded = expandedLessonId === item.lesson_id;
                    const regeneratingThisItem =
                      regenerate.isPending && regenerate.variables?.itemId === item.lesson_id;
                    return (
                      <li key={item.lesson_id} className="overflow-hidden rounded-md border">
                        <div className="flex flex-wrap items-center justify-between gap-3 p-3">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium">{item.title}</p>
                            <p className="truncate text-xs text-muted-foreground">
                              {item.exercise_count} exercises · {item.quiz_count} quizzes ·{" "}
                              <ReviewStatus status={item.review_status} />
                            </p>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              aria-expanded={expanded}
                              onClick={() =>
                                setExpandedLessonId(expanded ? null : item.lesson_id)
                              }
                            >
                              {expanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
                              {expanded ? "Close preview" : "Preview"}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={regenerate.isPending}
                              onClick={() => setRegenerateTarget({
                                itemType: "lesson",
                                itemId: item.lesson_id,
                                title: item.title,
                              })}
                            >
                              <RefreshCw className={`size-3.5 ${regeneratingThisItem ? "animate-spin" : ""}`} />
                              {regeneratingThisItem ? "Regenerating…" : "Regenerate"}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={setReview.isPending}
                              onClick={() => setReview.mutate({
                                lessonId: item.lesson_id,
                                action: item.review_status === "hidden" ? "approve" : "hide",
                              })}
                            >
                              {item.review_status === "hidden" ? "Restore" : "Hide"}
                            </Button>
                            {item.review_status === "pending" && (
                              <Button
                                size="sm"
                                disabled={setReview.isPending}
                                onClick={() => setReview.mutate({ lessonId: item.lesson_id, action: "approve" })}
                              >
                                <CheckCircle2 className="size-3.5" aria-hidden="true" />
                                Mark reviewed
                              </Button>
                            )}
                          </div>
                        </div>
                        {expanded && <ReviewPreviewPanel lessonId={item.lesson_id} />}
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>
      )}
      {(content.data?.total ?? 0) > 0 && (
        <nav className="flex items-center justify-between gap-3 border-t pt-4" aria-label="Review pages">
          <p className="text-xs text-muted-foreground">
            {content.data?.total ?? 0} result(s) · Page {content.data?.page ?? page} of {content.data?.total_pages ?? 1}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1 || content.isFetching}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= (content.data?.total_pages ?? 1) || content.isFetching}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </Button>
          </div>
        </nav>
      )}
      <RegenerateDialog
        open={Boolean(regenerateTarget)}
        itemType={regenerateTarget?.itemType ?? "lesson"}
        itemTitle={regenerateTarget?.title ?? "this lesson"}
        pending={regenerate.isPending}
        onCancel={() => setRegenerateTarget(null)}
        onConfirm={(instructions) => {
          if (!regenerateTarget) return;
          regenerate.mutate(
            {
              itemType: regenerateTarget.itemType,
              itemId: regenerateTarget.itemId,
              instructions,
            },
            { onSuccess: () => setRegenerateTarget(null) },
          );
        }}
      />
      <ConfirmDialog
        open={Boolean(bulkReviewTarget)}
        title="Mark this course as reviewed?"
        description={`This will mark ${bulkReviewTarget?.count ?? 0} pending lesson(s) in “${bulkReviewTarget?.title ?? "this course"}” as reviewed. Hidden lessons will not change.`}
        confirmLabel="Mark all reviewed"
        pending={markCourseReviewed.isPending}
        onCancel={() => setBulkReviewTarget(null)}
        onConfirm={() => {
          if (!bulkReviewTarget) return;
          markCourseReviewed.mutate(bulkReviewTarget.courseId, {
            onSuccess: () => setBulkReviewTarget(null),
          });
        }}
      />
    </div>
  );
}

function ReportsList() {
  const { data: reports = [], isLoading } = useContentReports();
  const update = useSetContentReportStatus();
  const regenerate = useRegenerateContent();
  const [expandedReportId, setExpandedReportId] = useState<string | null>(null);
  const [regenerateTarget, setRegenerateTarget] = useState<RegenerateTarget | null>(null);
  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (!reports.length) return <p className="text-sm text-muted-foreground">No learner reports.</p>;
  return (
    <div className="space-y-3">
      {regenerate.isSuccess && (
        <p role="status" className="rounded-md bg-green-700/10 px-3 py-2 text-sm text-green-800">
          Reported content regenerated successfully. It is pending review again.
        </p>
      )}
      {regenerate.isError && (
        <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {regenerate.error instanceof Error
            ? regenerate.error.message
            : "Could not regenerate this content. Please try again."}
        </p>
      )}
      <ul className="space-y-2">
      {reports.map((report) => (
        <li key={report.id} className="overflow-hidden rounded-md border">
          <div className="flex flex-wrap items-start justify-between gap-3 p-3">
            <div>
              <p className="text-sm font-medium capitalize">{report.item_type} · {report.reason}</p>
              <p className="mt-1 text-xs text-muted-foreground">{report.details || "No extra details"}</p>
              <p className="mt-1 text-xs text-muted-foreground">Status: {report.status}</p>
            </div>
            <div className="flex flex-wrap gap-1">
              <Button
                variant="ghost"
                size="sm"
                aria-expanded={expandedReportId === report.id}
                onClick={() => setExpandedReportId(
                  expandedReportId === report.id ? null : report.id,
                )}
              >
                <History className="size-3.5" />
                {expandedReportId === report.id ? "Close versions" : "Versions"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={regenerate.isPending}
                onClick={() => setRegenerateTarget({
                  itemType: report.item_type,
                  itemId: report.item_id,
                  title: `${report.item_type} report`,
                })}
              >
                {regenerate.isPending && regenerate.variables?.itemId === report.item_id
                  ? "Regenerating…"
                  : "Regenerate item"}
              </Button>
              {report.status === "open" && <Button size="sm" disabled={update.isPending} onClick={() => update.mutate({ id: report.id, status: "resolved" })}>Resolve</Button>}
            </div>
          </div>
          {expandedReportId === report.id && (
            <div className="border-t bg-background/45 p-3">
              <ContentVersionHistory itemType={report.item_type} itemId={report.item_id} />
            </div>
          )}
        </li>
      ))}
      </ul>
      <RegenerateDialog
        open={Boolean(regenerateTarget)}
        itemType={regenerateTarget?.itemType ?? "lesson"}
        itemTitle={regenerateTarget?.title ?? "this reported item"}
        confirmLabel="Regenerate item"
        pending={regenerate.isPending}
        onCancel={() => setRegenerateTarget(null)}
        onConfirm={(instructions) => {
          if (!regenerateTarget) return;
          regenerate.mutate(
            {
              itemType: regenerateTarget.itemType,
              itemId: regenerateTarget.itemId,
              instructions,
            },
            { onSuccess: () => setRegenerateTarget(null) },
          );
        }}
      />
    </div>
  );
}

function GenerationJobs() {
  const { data: jobs = [], isLoading } = useAdminGenerationJobs();
  const action = useGenerationJobAction();
  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (!jobs.length) return <p className="text-sm text-muted-foreground">No generation jobs.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b text-xs text-muted-foreground"><tr><th className="pb-2">Learner</th><th>Language</th><th>Status</th><th>Progress</th><th>Attempts</th><th className="text-right">Actions</th></tr></thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className="border-b last:border-0">
              <td className="py-3">{job.user_email}<p className="text-xs text-muted-foreground">{job.kind === "course_set" ? "Next course set" : "Initial course"}</p></td>
              <td>{job.language}</td>
              <td className={STATUS_STYLES[job.status] ?? ""}>{job.status}{job.error && <p className="max-w-48 truncate text-xs text-destructive" title={job.error}>{job.error}</p>}</td>
              <td>{job.completed}/{job.total}</td><td>{job.attempt_count}/{job.max_attempts}</td>
              <td><div className="flex justify-end gap-1">
                {(["error", "cancelled"].includes(job.status)) && <Button size="sm" variant="outline" disabled={action.isPending} onClick={() => action.mutate({ id: job.id, action: "retry" })}>Retry</Button>}
                {(["pending", "running"].includes(job.status)) && <Button size="sm" variant="ghost" disabled={action.isPending} onClick={() => action.mutate({ id: job.id, action: "cancel" })}>Cancel</Button>}
              </div></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const MONITORING_CATEGORIES = [
  { key: "frontend_error", label: "Frontend errors" },
  { key: "api_5xx", label: "API 5xx" },
  { key: "ai_generation_failure", label: "AI generation failures" },
  { key: "worker_retry", label: "Worker retries" },
] as const;

function MonitoringPanel() {
  const [hours, setHours] = useState(24);
  const monitoring = useAdminMonitoring(hours);
  if (monitoring.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading monitoring data…</p>;
  }
  if (monitoring.isError || !monitoring.data) {
    return <p className="text-sm text-destructive">Could not load monitoring data.</p>;
  }
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">Operational health</p>
          <p className="text-xs text-muted-foreground">Automatically refreshes every 15 seconds.</p>
        </div>
        <select
          value={hours}
          onChange={(event) => setHours(Number(event.target.value))}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          aria-label="Monitoring time range"
        >
          <option value={24}>Last 24 hours</option>
          <option value={168}>Last 7 days</option>
          <option value={720}>Last 30 days</option>
        </select>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {MONITORING_CATEGORIES.map((category) => (
          <div key={category.key} className="rounded-lg border bg-muted/20 p-4">
            <p className="text-2xl font-semibold">
              {(monitoring.data.counts[category.key] ?? 0) +
                (category.key === "frontend_error"
                  ? monitoring.data.counts.unhandled_rejection ?? 0
                  : 0)}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">{category.label}</p>
          </div>
        ))}
      </div>
      <div>
        <h3 className="text-sm font-semibold">Recent events</h3>
        {monitoring.data.recent.length === 0 ? (
          <p className="mt-2 rounded-md border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
            No operational errors in this time range.
          </p>
        ) : (
          <div className="mt-2 overflow-x-auto rounded-lg border">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b bg-muted/30 text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">Time</th>
                  <th className="px-3 py-2">Category</th>
                  <th className="px-3 py-2">Message</th>
                  <th className="px-3 py-2">Context</th>
                </tr>
              </thead>
              <tbody>
                {monitoring.data.recent.map((event) => {
                  const context = event.details.path ?? event.details.job_id ?? "—";
                  return (
                    <tr key={event.id} className="border-b last:border-0">
                      <td className="whitespace-nowrap px-3 py-3 text-xs text-muted-foreground">
                        {new Date(event.created_at).toLocaleString()}
                      </td>
                      <td className="px-3 py-3 text-xs font-medium">{event.category}</td>
                      <td className="max-w-sm px-3 py-3">
                        <p className="line-clamp-2" title={event.message}>{event.message}</p>
                      </td>
                      <td className="max-w-xs truncate px-3 py-3 text-xs text-muted-foreground">
                        {String(context)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export function AdminPage() {
  const user = useSessionStore((state) => state.user);
  const [tab, setTab] = useState<Tab>("content");
  if (!user?.isAdmin) return <Navigate to="/dashboard" replace />;
  const tabs = [
    { id: "content" as const, label: "Content review", icon: FileCheck2 },
    { id: "reports" as const, label: "Learner reports", icon: AlertTriangle },
    { id: "jobs" as const, label: "Generation jobs", icon: Activity },
    { id: "monitoring" as const, label: "Monitoring", icon: HeartPulse },
  ];
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <header><p className="page-kicker">Administration</p><h1 className="page-heading">AI operations</h1><p className="mt-2 text-muted-foreground">Review content, fix reported items, and monitor recoverable generation jobs.</p></header>
      <div className="flex flex-wrap gap-2" role="tablist">
        {tabs.map(({ id, label, icon: Icon }) => <Button key={id} variant={tab === id ? "default" : "outline"} onClick={() => setTab(id)}><Icon className="size-4" />{label}</Button>)}
      </div>
      {tab === "content" && <><Card><CardHeader><CardTitle className="text-lg">Usage</CardTitle></CardHeader><CardContent><UsageSummary /></CardContent></Card><Card><CardHeader><CardTitle className="text-lg">AI content</CardTitle></CardHeader><CardContent><ReviewList /></CardContent></Card></>}
      {tab === "reports" && <Card><CardHeader><CardTitle className="text-lg">Learner reports</CardTitle></CardHeader><CardContent><ReportsList /></CardContent></Card>}
      {tab === "jobs" && <Card><CardHeader><CardTitle className="text-lg">Generation jobs</CardTitle></CardHeader><CardContent><GenerationJobs /></CardContent></Card>}
      {tab === "monitoring" && <Card><CardHeader><CardTitle className="text-lg">Production monitoring</CardTitle></CardHeader><CardContent><MonitoringPanel /></CardContent></Card>}
    </div>
  );
}
