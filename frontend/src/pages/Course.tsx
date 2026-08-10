import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Circle,
  Code2,
  ListChecks,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CourseChatPanel } from "@/components/CourseChatPanel";
import { SkeletonCards } from "@/components/Skeleton";
import { LessonCountSelect } from "@/components/LessonCountSelect";
import { useCourse } from "@/features/content/hooks";
import {
  useAdvanceCurriculum,
  useCourseExtension,
  useExtendCourse,
  useGenerationStatus,
} from "@/features/curriculum/hooks";
import { useProgress } from "@/features/progress/hooks";
import { ProgressBar } from "@/components/ProgressBar";

type CurriculumItemType = "lesson" | "exercise" | "quiz";

function CurriculumStatusIcon({ status }: { status: "complete" | "current" | "upcoming" }) {
  if (status === "complete") return <CheckCircle2 className="size-4 text-emerald-600" />;
  if (status === "current") return <Circle className="size-4 fill-primary/15 text-primary" />;
  return <Circle className="size-4 text-muted-foreground/45" />;
}

export function CoursePage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: course, isLoading, isError } = useCourse(slug);
  const courseId = course?.id;
  const { data: progress } = useProgress();

  const { data: extension } = useCourseExtension(courseId);
  const extend = useExtendCourse(courseId, slug);
  const advance = useAdvanceCurriculum(courseId);
  const generation = useGenerationStatus(advance.data?.track_id, Boolean(advance.data));
  const queryClient = useQueryClient();
  const advanceChecked = useRef(false);
  const [count, setCount] = useState(2);

  useEffect(() => {
    if (extension?.completion_percent === 100 && courseId && !advanceChecked.current) {
      advanceChecked.current = true;
      advance.mutate();
    }
  }, [advance, courseId, extension?.completion_percent]);

  useEffect(() => {
    if (generation.data?.status === "done") {
      queryClient.invalidateQueries({ queryKey: ["my-courses"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    }
  }, [generation.data?.status, queryClient]);

  if (isLoading) {
    return <SkeletonCards count={4} />;
  }
  if (isError || !course) {
    return <p className="text-destructive">Course not found.</p>;
  }

  const courseProgress = progress?.courses.find((item) => item.course_id === course.id);
  const nextItem = courseProgress?.next_item;
  const completedItems = new Set(
    (courseProgress?.completed_items ?? []).map((item) => `${item.item_type}:${item.item_id}`),
  );
  const nextKey = nextItem ? `${nextItem.item_type}:${nextItem.item_id}` : null;
  const generationJob = generation.data ?? advance.data ?? null;
  const generationPercent = generationJob?.total
    ? Math.round((generationJob.completed / generationJob.total) * 100)
    : 0;

  function itemStatus(itemType: CurriculumItemType, itemId: string) {
    const key = `${itemType}:${itemId}`;
    if (completedItems.has(key)) return "complete" as const;
    if (key === nextKey) return "current" as const;
    return "upcoming" as const;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-9">
      <div className="space-y-2 border-b pb-8">
        <p className="page-kicker">Course</p>
        <h1 className="page-heading max-w-3xl">{course.title}</h1>
        {course.description && <p className="max-w-2xl leading-7 text-muted-foreground">{course.description}</p>}
        <div className="flex items-center gap-2 pt-3 text-sm text-muted-foreground"><BookOpen className="size-4" /> {course.lessons.length} lessons</div>
        {courseProgress && (
          <div className="max-w-xl space-y-2 pt-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{courseProgress.completed} of {courseProgress.total} items complete</span>
              <span>{courseProgress.percent}%</span>
            </div>
            <ProgressBar percent={courseProgress.percent} />
          </div>
        )}
      </div>

      {nextItem ? (
        <Card className="border-primary/25">
          <CardContent className="flex flex-wrap items-center justify-between gap-4 py-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">Next step</p>
              <p className="mt-1 font-semibold">{nextItem.title}</p>
              <p className="mt-1 text-sm capitalize text-muted-foreground">{nextItem.item_type}</p>
            </div>
            <Button asChild>
              <Link to={nextItem.path}>Continue <ArrowRight className="size-4" /></Link>
            </Button>
          </CardContent>
        </Card>
      ) : courseProgress?.percent === 100 ? (
        <Card className="border-primary/25">
          <CardContent className="py-5">
            <p className="font-semibold">Course complete</p>
            <p className="mt-1 text-sm text-muted-foreground">Your next curriculum will be prepared from your results.</p>
          </CardContent>
        </Card>
      ) : null}

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="section-heading">Course outline</h2>
          {extension?.can_extend && (
            <div className="flex items-center gap-2">
              <LessonCountSelect value={count} onChange={setCount} disabled={extend.isPending} />
              <Button
                variant="outline"
                size="sm"
                onClick={() => extend.mutate({ count })}
                disabled={extend.isPending}
              >
                {extend.isPending ? "Adding…" : `Learn more (${count})`}
              </Button>
            </div>
          )}
        </div>
        {course.lessons.length === 0 ? (
          <p className="text-sm text-muted-foreground">No lessons yet.</p>
        ) : (
          course.lessons.map((lesson, index) => {
            const exercises = lesson.exercises ?? [];
            const quizzes = lesson.quizzes ?? [];
            const items = [
              { type: "lesson" as const, id: lesson.id },
              ...exercises.map((item) => ({ type: "exercise" as const, id: item.id })),
              ...quizzes.map((item) => ({ type: "quiz" as const, id: item.id })),
            ];
            const lessonCompleted = items.filter((item) =>
              completedItems.has(`${item.type}:${item.id}`),
            ).length;
            const containsNext = items.some((item) => `${item.type}:${item.id}` === nextKey);

            return (
              <Card key={lesson.id} className={containsNext ? "border-primary/30" : ""}>
                <details open={containsNext || index === 0 ? true : undefined}>
                  <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
                    <CardHeader className="flex-row items-center gap-4 space-y-0 py-4">
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary font-mono text-xs text-primary">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <div className="min-w-0 flex-1">
                        <CardTitle className="truncate text-base font-medium">{lesson.title}</CardTitle>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {lessonCompleted} of {items.length} items complete
                        </p>
                      </div>
                      {lessonCompleted === items.length ? (
                        <CheckCircle2 className="size-5 text-emerald-600" />
                      ) : containsNext ? (
                        <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">In progress</span>
                      ) : (
                        <span className="text-xs text-muted-foreground">View</span>
                      )}
                    </CardHeader>
                  </summary>
                  <CardContent className="space-y-2 border-t py-4">
                    <Link
                      to={`/lessons/${lesson.id}`}
                      className="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-accent"
                    >
                      <CurriculumStatusIcon status={itemStatus("lesson", lesson.id)} />
                      <BookOpen className="size-4 text-muted-foreground" />
                      <span className="min-w-0 flex-1 truncate text-sm font-medium">Read lesson</span>
                      <ArrowRight className="size-4 text-muted-foreground" />
                    </Link>
                    {exercises.map((exercise) => (
                      <Link
                        key={exercise.id}
                        to={`/exercises/${exercise.id}`}
                        className="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-accent"
                      >
                        <CurriculumStatusIcon status={itemStatus("exercise", exercise.id)} />
                        <Code2 className="size-4 text-muted-foreground" />
                        <span className="min-w-0 flex-1 truncate text-sm">{exercise.title}</span>
                        <span className="text-xs text-muted-foreground">Exercise</span>
                      </Link>
                    ))}
                    {quizzes.map((quiz) => (
                      <Link
                        key={quiz.id}
                        to={`/quizzes/${quiz.id}`}
                        className="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-accent"
                      >
                        <CurriculumStatusIcon status={itemStatus("quiz", quiz.id)} />
                        <ListChecks className="size-4 text-muted-foreground" />
                        <span className="min-w-0 flex-1 truncate text-sm">{quiz.title}</span>
                        <span className="text-xs text-muted-foreground">Quiz</span>
                      </Link>
                    ))}
                  </CardContent>
                </details>
              </Card>
            );
          })
        )}
        {extend.isError && (
          <p className="text-sm text-destructive">
            Couldn’t add more lessons just now — please try again shortly.
          </p>
        )}
      </div>

      {(advance.isPending || generationJob) && (
        <Card className="border-primary/25 bg-primary/[0.035]">
          <CardContent className="space-y-4 py-5">
            <div className="flex items-start gap-3">
              {generationJob?.status === "error" ? (
                <AlertCircle className="mt-0.5 size-5 text-destructive" />
              ) : generationJob?.status === "done" ? (
                <CheckCircle2 className="mt-0.5 size-5 text-emerald-600" />
              ) : (
                <LoaderCircle className="mt-0.5 size-5 animate-spin text-primary" />
              )}
              <div className="min-w-0 flex-1">
                <p className="font-semibold">
                  {generationJob?.status === "done"
                    ? "Your next three courses are ready."
                    : generationJob?.status === "error"
                      ? "We couldn’t build the next courses."
                      : "Building your next three courses"}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {generationJob?.status === "done"
                    ? "They’re based on your latest quiz and exercise performance and are now in Library."
                    : generationJob?.status === "error"
                      ? "Your completed work is safe. Retry when you’re ready."
                      : "AI is reassessing your results, choosing three directions, and creating the lessons."}
                </p>
              </div>
            </div>
            {generationJob && generationJob.status !== "done" && generationJob.status !== "error" && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{generationJob.completed} of {generationJob.total} lessons prepared</span>
                  <span>{generationPercent}%</span>
                </div>
                <ProgressBar percent={generationPercent} />
              </div>
            )}
            {generationJob?.status === "error" && (
              <Button size="sm" variant="outline" onClick={() => advance.mutate()} disabled={advance.isPending}>
                <RotateCcw className="size-4" /> Retry generation
              </Button>
            )}
            {generationJob?.status === "done" && (
              <Button size="sm" asChild>
                <Link to="/library">Open Library <ArrowRight className="size-4" /></Link>
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {courseId && <CourseChatPanel courseId={courseId} courseSlug={slug} />}
    </div>
  );
}
