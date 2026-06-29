import { useMemo } from "react";
import { useParams } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { useLesson } from "@/features/content/hooks";
import { renderMarkdown } from "@/lib/markdown";

export function LessonPage() {
  const { id } = useParams<{ id: string }>();
  const { data: lesson, isLoading, isError } = useLesson(id);

  const html = useMemo(() => (lesson ? renderMarkdown(lesson.content) : ""), [lesson]);

  if (isLoading) {
    return <p className="text-muted-foreground">Loading lesson…</p>;
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
    </div>
  );
}
