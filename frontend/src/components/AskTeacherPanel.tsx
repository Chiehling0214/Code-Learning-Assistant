import { useState } from "react";

import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useStreamingAnswer } from "@/features/ai/hooks";

/**
 * A lightweight "ask the AI Teacher" panel (streams the answer). Pass `context`
 * (e.g. the questions being reviewed, the learner's answers/code) so the AI
 * knows exactly what the learner is referring to — no copy-pasting needed.
 */
export function AskTeacherPanel({
  topic,
  context,
  title = "Ask the AI Teacher",
  placeholder = "Ask about any of these questions…",
}: {
  topic?: string;
  context?: string;
  title?: string;
  placeholder?: string;
}) {
  const teacher = useStreamingAnswer("/ai/teacher");
  const [question, setQuestion] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || teacher.isPending) return;
    teacher.ask({ topic: topic ?? "", question, context: context ?? "" });
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
          <Button
            size="sm"
            variant="outline"
            type="submit"
            disabled={teacher.isPending || !question.trim()}
          >
            {teacher.isPending ? "Answering…" : "Ask"}
          </Button>
        </form>

        {teacher.error != null && (
          <p className="text-sm text-destructive">
            {teacher.error instanceof Error ? teacher.error.message : "Request failed"}
          </p>
        )}
        {teacher.answer && <Markdown content={teacher.answer} className="rounded-md bg-muted p-3" />}
      </CardContent>
    </Card>
  );
}
