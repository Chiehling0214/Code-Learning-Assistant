import { useState } from "react";

import { UpgradePrompt } from "@/components/UpgradePrompt";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useStreamingAnswer } from "@/features/ai/hooks";
import { ApiError } from "@/lib/api";
import { renderMarkdown } from "@/lib/markdown";

const inputClass =
  "min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

/** AI Tutor panel — streams a hint on the current editor code (never the answer). */
export function AiTutorPanel({
  exerciseId,
  code,
}: {
  exerciseId: string | undefined;
  code: string;
}) {
  const tutor = useStreamingAnswer("/ai/tutor");
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
          disabled={tutor.isPending || code.trim().length === 0}
          onClick={() => tutor.ask({ exercise_id: exerciseId, code, question })}
        >
          {tutor.isPending ? "Thinking…" : "Get a hint"}
        </Button>

        {tutor.error != null &&
          (tutor.error instanceof ApiError && tutor.error.status === 402 ? (
            <UpgradePrompt error={tutor.error} />
          ) : (
            <p className="text-sm text-destructive">
              {tutor.error instanceof Error ? tutor.error.message : "Request failed"}
            </p>
          ))}
        {tutor.answer && (
          <div
            className="prose-sm max-w-none rounded-md bg-muted p-3 [&_code]:rounded [&_code]:bg-background [&_code]:px-1 [&_p]:my-2 [&_pre]:overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(tutor.answer) }}
          />
        )}
      </CardContent>
    </Card>
  );
}
