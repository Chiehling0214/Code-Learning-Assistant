import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAskTeacher } from "@/features/ai/hooks";
import { renderMarkdown } from "@/lib/markdown";

const inputClass =
  "min-h-[72px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

/** "Ask AI Teacher" panel — explains/expands the current lesson for the learner. */
export function AiTeacherPanel({ lessonId }: { lessonId: string | undefined }) {
  const ask = useAskTeacher();
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
          disabled={ask.isPending}
          onClick={() => ask.mutate({ lesson_id: lessonId, question })}
        >
          {ask.isPending ? "Thinking…" : "Ask"}
        </Button>

        {ask.isError && (
          <p className="text-sm text-destructive">
            {ask.error instanceof Error ? ask.error.message : "Request failed"}
          </p>
        )}
        {ask.data && (
          <div
            className="prose-sm max-w-none rounded-md bg-muted p-3 [&_code]:rounded [&_code]:bg-background [&_code]:px-1 [&_p]:my-2 [&_pre]:overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(ask.data.answer) }}
          />
        )}
      </CardContent>
    </Card>
  );
}
