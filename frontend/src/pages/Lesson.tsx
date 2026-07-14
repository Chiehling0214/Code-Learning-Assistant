import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";

import { AiTeacherPanel } from "@/components/AiTeacherPanel";
import { SkeletonCards } from "@/components/Skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useLesson } from "@/features/content/hooks";
import { useMarkLessonComplete } from "@/features/progress/hooks";
import { useLessonExercises } from "@/features/exercises/hooks";
import { useLessonQuizzes } from "@/features/quizzes/hooks";
import { renderMarkdown } from "@/lib/markdown";

export function LessonPage() {
  const { id } = useParams<{ id: string }>();
  const { data: lesson, isLoading, isError } = useLesson(id);
  const { data: exercises = [] } = useLessonExercises(id);
  const { data: quizzes = [] } = useLessonQuizzes(id);
  const markComplete = useMarkLessonComplete();

  const html = useMemo(() => (lesson ? renderMarkdown(lesson.content) : ""), [lesson]);

  if (isLoading) {
    return <SkeletonCards count={3} />;
  }
  if (isError || !lesson) {
    return <p className="text-destructive">Lesson not found.</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">{lesson.title}</h1>
      <Card>
        <CardContent className="py-6">
          <div
            className="prose-sm max-w-none [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_h1]:mb-3 [&_h1]:text-2xl [&_h1]:font-bold [&_h2]:mb-2 [&_h2]:mt-4 [&_h2]:text-xl [&_h2]:font-semibold [&_p]:my-2 [&_pre]:my-3 [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:bg-muted [&_pre]:p-3"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          disabled={!id || markComplete.isPending || markComplete.isSuccess}
          onClick={() => id && markComplete.mutate(id)}
        >
          {markComplete.isSuccess ? "Completed ✓" : "Mark lesson complete"}
        </Button>
        {markComplete.isError && (
          <span className="text-sm text-destructive">Could not save. Try again.</span>
        )}
      </div>

      <AiTeacherPanel lessonId={id} />

      {exercises.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Exercises</h2>
          {exercises.map((exercise) => (
            <Card key={exercise.id} className="transition-colors hover:bg-accent">
              <Link to={`/exercises/${exercise.id}`}>
                <CardContent className="flex items-center justify-between py-4">
                  <span className="font-medium">{exercise.title}</span>
                  <span className="font-mono text-xs text-muted-foreground">
                    {exercise.language}
                  </span>
                </CardContent>
              </Link>
            </Card>
          ))}
        </div>
      )}

      {quizzes.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Quizzes</h2>
          {quizzes.map((quiz) => (
            <Card key={quiz.id} className="transition-colors hover:bg-accent">
              <Link to={`/quizzes/${quiz.id}`}>
                <CardContent className="flex items-center justify-between py-4">
                  <span className="font-medium">{quiz.title}</span>
                  <span className="text-xs text-muted-foreground">Quiz</span>
                </CardContent>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
