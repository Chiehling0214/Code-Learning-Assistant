import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminContent, useAdminUsage, useSetLessonReview } from "@/features/admin/hooks";
import { useSessionStore } from "@/store/session";

const STATUS_STYLES: Record<string, string> = {
  approved: "text-green-600",
  pending: "text-amber-600",
  hidden: "text-muted-foreground line-through",
};

function UsageSummary() {
  const { data: usage } = useAdminUsage();
  if (!usage) return null;
  const stat = (label: string, value: number) => (
    <div className="rounded-md border px-3 py-2 text-center">
      <div className="text-xl font-semibold">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
  return (
    <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
      {stat("AI lessons", usage.ai_lessons)}
      {stat("Pending", usage.pending)}
      {stat("Approved", usage.approved)}
      {stat("Hidden", usage.hidden)}
      {stat("Exercises", usage.ai_exercises)}
      {stat("Quizzes", usage.ai_quizzes)}
    </div>
  );
}

function ReviewList() {
  const { data: items = [], isLoading } = useAdminContent("ai");
  const setReview = useSetLessonReview();

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No AI-generated content yet.</p>;
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.lesson_id}
          className="flex items-center justify-between gap-3 rounded-md border p-3"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{item.title}</p>
            <p className="truncate text-xs text-muted-foreground">
              {item.course_title} · {item.exercise_count} exercises · {item.quiz_count} quizzes ·{" "}
              <span className={STATUS_STYLES[item.review_status] ?? ""}>{item.review_status}</span>
            </p>
          </div>
          <div className="flex shrink-0 gap-1">
            {item.review_status !== "hidden" ? (
              <Button
                variant="ghost"
                size="sm"
                disabled={setReview.isPending}
                onClick={() => setReview.mutate({ lessonId: item.lesson_id, action: "hide" })}
              >
                Hide
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                disabled={setReview.isPending}
                onClick={() => setReview.mutate({ lessonId: item.lesson_id, action: "approve" })}
              >
                Restore
              </Button>
            )}
            {item.review_status === "pending" && (
              <Button
                size="sm"
                disabled={setReview.isPending}
                onClick={() => setReview.mutate({ lessonId: item.lesson_id, action: "approve" })}
              >
                Approve
              </Button>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function AdminPage() {
  const user = useSessionStore((s) => s.user);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Content review</h1>
        <p className="text-muted-foreground">
          Review AI-generated lessons. Hidden lessons are not served to learners.
        </p>
      </div>

      {!user?.isAdmin && (
        <Card className="border-amber-500/40">
          <CardContent className="py-4 text-sm text-muted-foreground">
            Your account is not an admin, so these actions will return 403. Grant admin with{" "}
            <code className="rounded bg-muted px-1">python -m scripts.set_admin {user?.email}</code>{" "}
            in the backend container, then sign out and back in.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Usage</CardTitle>
        </CardHeader>
        <CardContent>
          <UsageSummary />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">AI content</CardTitle>
        </CardHeader>
        <CardContent>
          <ReviewList />
        </CardContent>
      </Card>
    </div>
  );
}
