import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useStreamingAnswer } from "@/features/ai/hooks";
import { renderMarkdown } from "@/lib/markdown";

const inputClass =
  "min-h-[72px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

/** "Ask AI Teacher" panel — streams an explanation of the current lesson. */
export function AiTeacherPanel({ lessonId }: { lessonId: string | undefined }) {
  const teacher = useStreamingAnswer("/ai/teacher");
  const [question, setQuestion] = useState("");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Ask the AI Teacher</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <textarea
          className={inputClass}
          placeholder="Ask for a simpler explanation, an example, or a deeper dive…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button
          size="sm"
          disabled={teacher.isPending}
          onClick={() => teacher.ask({ lesson_id: lessonId ?? null, question })}
        >
          {teacher.isPending ? "Answering…" : "Ask"}
        </Button>

        {teacher.error != null && (
          <p className="text-sm text-destructive">
            {teacher.error instanceof Error ? teacher.error.message : "Request failed"}
          </p>
        )}
        {teacher.answer && (
          <div
            className="prose-sm max-w-none rounded-md bg-muted p-3 [&_code]:rounded [&_code]:bg-background [&_code]:px-1 [&_p]:my-2 [&_pre]:overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(teacher.answer) }}
          />
        )}
      </CardContent>
    </Card>
  );
}
