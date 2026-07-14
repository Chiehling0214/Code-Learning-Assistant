import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ProgressBar } from "@/components/ProgressBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMastery } from "@/features/mastery/hooks";
import { useProgress } from "@/features/progress/hooks";
import { useTracks } from "@/features/tracks/hooks";
import { cn } from "@/lib/utils";

const LEVEL_STYLE: Record<string, string> = {
  weak: "bg-destructive/70",
  ok: "bg-amber-500/70",
  strong: "bg-green-500/70",
};

function MasteryPanel() {
  const { data: tracks = [] } = useTracks();
  const [language, setLanguage] = useState("");
  useEffect(() => {
    if (!language && tracks.length) setLanguage(tracks[0].language_slug);
  }, [tracks, language]);
  const { data } = useMastery(language || undefined);
  const topics = data?.topics ?? [];

  if (tracks.length === 0) return null;
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Topic mastery</h2>
        <select
          className="rounded-md border border-input bg-background px-2 py-1 text-sm"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          {tracks.map((t) => (
            <option key={t.id} value={t.language_slug}>
              {t.language_name}
            </option>
          ))}
        </select>
      </div>
      {topics.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No history yet — answer quizzes and solve exercises to build your mastery picture.
        </p>
      ) : (
        <Card>
          <CardContent className="space-y-3 py-4">
            {topics.map((t) => (
              <div key={t.topic} className="space-y-1">
                <div className="flex items-center justify-between gap-2 text-sm">
                  <span className="truncate font-medium">{t.topic}</span>
                  <span className="flex shrink-0 items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {t.correct}/{t.attempts} · {Math.round(t.correct_rate * 100)}%
                    </span>
                    <Button asChild variant="ghost" size="sm">
                      <Link to={`/practice?language=${language}&topic=${encodeURIComponent(t.topic)}`}>
                        Practice
                      </Link>
                    </Button>
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn("h-full rounded-full", LEVEL_STYLE[t.level])}
                    style={{ width: `${Math.max(6, Math.round(t.correct_rate * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

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

      <MasteryPanel />
    </div>
  );
}
