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
  weak: "bg-[#9a5f5a]",
  ok: "bg-[#94754c]",
  strong: "bg-[#557665]",
};

function TopicRow({ topic, language }: { topic: import("@/features/mastery/hooks").TopicMastery; language: string }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2 text-sm">
        {topic.lesson_id ? (
          <Link
            to={`/lessons/${topic.lesson_id}`}
            className="truncate font-medium hover:underline"
            title="Open the lesson"
          >
            {topic.topic}
          </Link>
        ) : (
          <span className="truncate font-medium">{topic.topic}</span>
        )}
        <span className="flex shrink-0 items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {topic.correct}/{topic.attempts} · {Math.round(topic.correct_rate * 100)}%
          </span>
          <Button asChild variant="ghost" size="sm">
            <Link to={`/practice?language=${language}&topic=${encodeURIComponent(topic.topic)}`}>
              Practice
            </Link>
          </Button>
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full", LEVEL_STYLE[topic.level])}
          style={{ width: `${Math.max(6, Math.round(topic.correct_rate * 100))}%` }}
          role="progressbar"
          aria-label={`${topic.topic} mastery`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(topic.correct_rate * 100)}
        />
      </div>
    </div>
  );
}

function MasteryPanel() {
  const { data: tracks = [] } = useTracks();
  const [language, setLanguage] = useState("");
  useEffect(() => {
    if (!language && tracks.length) setLanguage(tracks[0].language_slug);
  }, [tracks, language]);
  const { data } = useMastery(language || undefined);
  const topics = data?.topics ?? [];
  const assessment = data?.assessment;
  // Course topics (taught in a lesson) vs. topics you drilled yourself.
  const courseTopics = topics.filter((t) => t.lesson_id);
  const drillTopics = topics.filter((t) => !t.lesson_id);

  if (tracks.length === 0) return null;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Topic mastery</h2>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Language</span>
          <select
            className="min-h-10 rounded-md border border-input bg-background px-2 py-1 text-foreground"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            {tracks.map((t) => (
              <option key={t.id} value={t.language_slug}>
                {t.language_name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {assessment && (
        <Card>
          <CardContent className="space-y-4 py-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">AI-assessed level</p>
                <p className="mt-1 text-2xl font-semibold capitalize">
                  {assessment.current_level}
                </p>
              </div>
              <div className="rounded-lg bg-secondary/60 px-3 py-2 text-right">
                <p className="text-xs text-muted-foreground">Recent performance</p>
                <p className="mt-0.5 text-sm font-semibold">
                  {assessment.accuracy === null
                    ? "Waiting for course answers"
                    : `${assessment.correct}/${assessment.attempts} · ${assessment.accuracy}%`}
                </p>
              </div>
            </div>
            {assessment.attempts > 0 && (
              <p className="text-sm leading-6 text-muted-foreground">
                Your recent work currently points to{" "}
                <span className="font-semibold capitalize text-foreground">
                  {assessment.evidence_level}
                </span>
                . This is evidence for the next assessment, not a setting you need to manage.
              </p>
            )}
            <details className="group rounded-lg border bg-background/40 px-3 py-2.5">
              <summary className="cursor-pointer text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                How the level is decided
              </summary>
              <div className="mt-2 space-y-2 text-sm leading-6 text-muted-foreground">
                <p>
                  Exercises and quiz questions are counted as evidence. Below 60% maps to
                  Beginner, 60–84% to Intermediate, and 85% or higher to Advanced.
                </p>
                <p>{assessment.next_evaluation}</p>
              </div>
            </details>
          </CardContent>
        </Card>
      )}
      {topics.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No history yet — answer quizzes and solve exercises to build your mastery picture.
        </p>
      ) : (
        <>
          {courseTopics.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Course topics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pb-4">
                {courseTopics.map((t) => (
                  <TopicRow key={t.topic} topic={t} language={language} />
                ))}
              </CardContent>
            </Card>
          )}
          {drillTopics.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">My practice topics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pb-4">
                {drillTopics.map((t) => (
                  <TopicRow key={t.topic} topic={t} language={language} />
                ))}
              </CardContent>
            </Card>
          )}
        </>
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
        <p className="page-kicker">Learning record</p>
        <h1 className="page-heading">Your progress</h1>
        <p className="mt-2 text-muted-foreground">A practical view of what’s solid and what needs work.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="flex min-h-44 flex-col justify-center space-y-3 py-6">
            <p className="text-sm font-medium text-muted-foreground">Overall</p>
            <div className="text-2xl font-bold">{data.percent}%</div>
            <ProgressBar percent={data.percent} />
            <p className="text-xs text-muted-foreground">
              {data.completed} / {data.total} items
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex min-h-44 flex-col justify-center py-6">
            <p className="mb-3 text-sm font-medium text-muted-foreground">Streak</p>
            <div className="text-2xl font-bold">🔥 {data.streak}</div>
            <p className="mt-2 text-xs text-muted-foreground">
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
              <CardContent className="flex min-h-20 flex-col justify-center space-y-3 py-4">
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
