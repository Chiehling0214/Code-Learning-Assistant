import { ProgressBar } from "@/components/ProgressBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useProgress } from "@/features/progress/hooks";

export function ProgressPage() {
  const { data, isLoading, isError } = useProgress();

  if (isLoading) return <p className="text-muted-foreground">Loading progress…</p>;
  if (isError || !data) return <p className="text-destructive">Could not load progress.</p>;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Progress</h1>
        <p className="text-muted-foreground">Your completion across courses.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Overall</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-2xl font-bold">{data.percent}%</div>
            <ProgressBar percent={data.percent} />
            <p className="text-xs text-muted-foreground">
              {data.completed} / {data.total} items
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Streak</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">🔥 {data.streak}</div>
            <p className="text-xs text-muted-foreground">
              {data.streak === 1 ? "day" : "days"} in a row
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">By course</h2>
        {data.courses.length === 0 ? (
          <p className="text-sm text-muted-foreground">No courses yet.</p>
        ) : (
          data.courses.map((course) => (
            <Card key={course.course_id}>
              <CardContent className="space-y-2 py-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{course.title}</span>
                  <span className="text-muted-foreground">
                    {course.completed} / {course.total} ({course.percent}%)
                  </span>
                </div>
                <ProgressBar percent={course.percent} />
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
