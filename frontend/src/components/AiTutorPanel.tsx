import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAskTutor } from "@/features/ai/hooks";
import { renderMarkdown } from "@/lib/markdown";

const inputClass =
  "min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

/** AI Tutor panel — sends the current editor code and returns a hint, not the answer. */
export function AiTutorPanel({
  exerciseId,
  code,
}: {
  exerciseId: string | undefined;
  code: string;
}) {
  const ask = useAskTutor(exerciseId);
  const [question, setQuestion] = useState("");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">AI Tutor</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <textarea
          className={inputClass}
          placeholder="Stuck? Ask for a hint (your current code is sent automatically)…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button
          size="sm"
          variant="outline"
          disabled={ask.isPending || code.trim().length === 0}
          onClick={() => ask.mutate({ code, question })}
        >
          {ask.isPending ? "Thinking…" : "Get a hint"}
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
