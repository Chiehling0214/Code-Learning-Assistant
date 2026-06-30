import Editor from "@monaco-editor/react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { GradingPanel, RunOutput } from "@/components/ResultPanel";
import { SubmissionList } from "@/components/SubmissionList";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useExercise,
  useRun,
  useSubmission,
  useSubmissions,
  useSubmit,
} from "@/features/exercises/hooks";

export function CodingExercisePage() {
  const { id } = useParams<{ id: string }>();
  const { data: exercise, isLoading, isError } = useExercise(id);
  const { data: submissions = [] } = useSubmissions(id);
  const submit = useSubmit(id);
  const run = useRun(id);

  const [code, setCode] = useState("");
  const [activeSubmissionId, setActiveSubmissionId] = useState<string>();
  const { data: activeSubmission } = useSubmission(activeSubmissionId, id);

  // Seed the editor with the exercise's starter code once it loads.
  useEffect(() => {
    if (exercise) setCode(exercise.starter_code);
  }, [exercise]);

  if (isLoading) {
    return <p className="text-muted-foreground">Loading exercise…</p>;
  }
  if (isError || !exercise) {
    return <p className="text-destructive">Exercise not found.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{exercise.title}</h1>
          <p className="text-muted-foreground">{exercise.prompt}</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="outline"
            onClick={() => run.mutate({ code })}
            disabled={run.isPending || code.trim().length === 0}
          >
            {run.isPending ? "Running…" : "Run"}
          </Button>
          <Button
            onClick={() =>
              submit.mutate(code, { onSuccess: (s) => setActiveSubmissionId(s.id) })
            }
            disabled={submit.isPending || code.trim().length === 0}
          >
            {submit.isPending ? "Submitting…" : "Submit"}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Editor</CardTitle>
          <CardDescription>
            Language: <span className="font-mono">{exercise.language}</span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-md border">
            <Editor
              height="360px"
              language={exercise.language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value ?? "")}
              options={{ minimap: { enabled: false }, fontSize: 14 }}
            />
          </div>
        </CardContent>
      </Card>

      {run.data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Run output</CardTitle>
          </CardHeader>
          <CardContent>
            <RunOutput result={run.data} />
          </CardContent>
        </Card>
      )}

      {activeSubmission && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Result</CardTitle>
          </CardHeader>
          <CardContent>
            <GradingPanel status={activeSubmission.status} result={activeSubmission.result} />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Submissions</CardTitle>
        </CardHeader>
        <CardContent>
          <SubmissionList submissions={submissions} />
        </CardContent>
      </Card>
    </div>
  );
}
