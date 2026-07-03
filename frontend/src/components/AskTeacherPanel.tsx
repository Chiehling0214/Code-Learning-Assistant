import { useState } from "react";

import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAskTeacher } from "@/features/ai/hooks";

/**
 * A lightweight "ask the AI Teacher" panel. Optionally seeds a `topic` (e.g. the
 * question being reviewed) so the learner can ask about its details.
 */
export function AskTeacherPanel({
  topic,
  title = "Ask the AI Teacher",
  placeholder = "Ask about any of these questions…",
}: {
  topic?: string;
  title?: string;
  placeholder?: string;
}) {
  const ask = useAskTeacher();
  const [question, setQuestion] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || ask.isPending) return;
    ask.mutate({ topic: topic ?? "", question });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <form onSubmit={submit} className="space-y-2">
          <textarea
            className="min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder={placeholder}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Button size="sm" variant="outline" type="submit" disabled={ask.isPending || !question.trim()}>
            {ask.isPending ? "Thinking…" : "Ask"}
          </Button>
        </form>

        {ask.isError && (
          <p className="text-sm text-destructive">
            {ask.error instanceof Error ? ask.error.message : "Request failed"}
          </p>
        )}
        {ask.data && (
          <Markdown content={ask.data.answer} className="rounded-md bg-muted p-3" />
        )}
      </CardContent>
    </Card>
  );
}
