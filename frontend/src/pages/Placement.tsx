import Editor from "@monaco-editor/react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { AskTeacherPanel } from "@/components/AskTeacherPanel";
import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { usePlacement, useSubmitPlacement } from "@/features/placement/hooks";

export function PlacementPage() {
  const { id: trackId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: placement, isLoading, isError } = usePlacement(trackId);
  const submit = useSubmitPlacement(trackId);

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [code, setCode] = useState<Record<string, string>>({});

  // Seed the coding editors with the starter code once the test loads.
  useEffect(() => {
    if (placement) {
      const seeded: Record<string, string> = {};
      for (const task of placement.coding) seeded[task.id] = task.starter_code;
      setCode(seeded);
    }
  }, [placement]);

  if (isLoading) return <p className="p-6 text-muted-foreground">Building your placement test…</p>;
  if (isError || !placement) return <p className="p-6 text-destructive">Could not load the test.</p>;

  const result = submit.data;
  const allAnswered = placement.mcqs.every((m) => answers[m.id]);

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Placement test</h1>
        <p className="text-muted-foreground">
          A quick check so we can tailor your course to the right level.
        </p>
      </div>

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Review</CardTitle>
              <p className="text-sm text-muted-foreground">
                You got {result.breakdown.correct_mcqs}/{result.breakdown.total_mcqs} multiple-choice
                questions right
                {result.breakdown.total_coding > 0 &&
                  ` and passed ${result.breakdown.passed_coding}/${result.breakdown.total_coding} coding tasks`}
                . Look over the answers and explanations below.
              </p>
            </CardHeader>
          </Card>

          {result.breakdown.mcqs.map((mcq, i) => (
            <Card key={mcq.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  Question {i + 1}
                  <span className={cn("text-sm", mcq.correct ? "text-green-600" : "text-destructive")}>
                    {mcq.correct ? "✓ Correct" : "✗ Incorrect"}
                  </span>
                </CardTitle>
                <Markdown content={mcq.prompt} />
              </CardHeader>
              <CardContent className="space-y-2">
                {mcq.choices.map((c) => {
                  const isCorrect = c.id === mcq.correct_choice_id;
                  const isWrongPick = c.id === mcq.selected_choice_id && !mcq.correct;
                  return (
                    <div
                      key={c.id}
                      className={cn(
                        "rounded-md border px-3 py-2 text-sm",
                        isCorrect && "border-green-500/60 bg-green-500/10",
                        isWrongPick && "border-destructive/60 bg-destructive/10",
                      )}
                    >
                      {c.text}
                      {isCorrect && <span className="ml-2 text-xs text-green-600">correct answer</span>}
                      {isWrongPick && <span className="ml-2 text-xs text-destructive">your answer</span>}
                    </div>
                  );
                })}
                {mcq.explanation && (
                  <div className="rounded-md bg-muted p-3 text-sm">
                    <span className="font-medium">Explanation. </span>
                    {mcq.explanation}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}

          {result.breakdown.coding.map((task, i) => (
            <Card key={task.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  Coding task {i + 1}
                  <span
                    className={cn(
                      "text-sm",
                      task.passed ? "text-green-600" : "text-muted-foreground",
                    )}
                  >
                    {task.passed_cases}/{task.total_cases} tests passed
                  </span>
                </CardTitle>
                <Markdown content={task.prompt} />
              </CardHeader>
            </Card>
          ))}

          <AskTeacherPanel
            title="Ask about a question"
            placeholder="e.g. Why is the answer to question 2 correct?"
          />

          <Card className="border-primary/40">
            <CardContent className="space-y-3 py-4">
              <p className="text-lg font-semibold">
                Your level: <span className="capitalize">{result.level}</span> ({result.percent}%)
              </p>
              <p className="text-sm text-muted-foreground">
                Next, we'll build a {result.level} course tailored to you.
              </p>
              <Button onClick={() => navigate(`/tracks/${trackId}/generating`, { replace: true })}>
                Build my course
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {!result && (
        <>
          {placement.mcqs.map((mcq, i) => (
            <Card key={mcq.id}>
              <CardHeader>
                <CardTitle className="text-base">Question {i + 1}</CardTitle>
                <Markdown content={mcq.prompt} />
              </CardHeader>
              <CardContent className="space-y-2">
                {mcq.choices.map((choice) => (
                  <label
                    key={choice.id}
                    className={cn(
                      "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm",
                      answers[mcq.id] === choice.id && "border-primary",
                    )}
                  >
                    <input
                      type="radio"
                      name={mcq.id}
                      checked={answers[mcq.id] === choice.id}
                      onChange={() => setAnswers((p) => ({ ...p, [mcq.id]: choice.id }))}
                    />
                    <span>{choice.text}</span>
                  </label>
                ))}
              </CardContent>
            </Card>
          ))}

          {placement.coding.map((task) => (
            <Card key={task.id}>
              <CardHeader>
                <CardTitle className="text-base">Coding task</CardTitle>
                <Markdown content={task.prompt} />
              </CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-md border">
                  <Editor
                    height="220px"
                    language={task.language}
                    theme="vs-dark"
                    value={code[task.id] ?? ""}
                    onChange={(v) => setCode((p) => ({ ...p, [task.id]: v ?? "" }))}
                    options={{ minimap: { enabled: false }, fontSize: 14 }}
                  />
                </div>
              </CardContent>
            </Card>
          ))}

          {submit.isError && (
            <p className="text-sm text-destructive">
              {submit.error instanceof Error ? submit.error.message : "Submission failed"}
            </p>
          )}

          <Button
            disabled={!allAnswered || submit.isPending}
            onClick={() => submit.mutate({ mcq_answers: answers, code })}
          >
            {submit.isPending ? "Grading…" : "Submit"}
          </Button>
        </>
      )}
    </div>
  );
}
