import Editor from "@monaco-editor/react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { SubmissionList } from "@/components/SubmissionList";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useExercise, useSubmissions, useSubmit } from "@/features/exercises/hooks";

export function CodingExercisePage() {
  const { id } = useParams<{ id: string }>();
  const { data: exercise, isLoading, isError } = useExercise(id);
  const { data: submissions = [] } = useSubmissions(id);
  const submit = useSubmit(id);

  const [code, setCode] = useState("");

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{exercise.title}</h1>
          <p className="text-muted-foreground">{exercise.prompt}</p>
        </div>
        <div className="flex gap-2">
          {/* Execution is wired in Sprint 4 (Judge0); the button stays disabled until then. */}
          <Button variant="outline" disabled title="Code execution arrives in Sprint 4">
            Run (Sprint 4)
          </Button>
          <Button
            onClick={() => submit.mutate(code)}
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
              height="380px"
              language={exercise.language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value ?? "")}
              options={{ minimap: { enabled: false }, fontSize: 14 }}
            />
          </div>
          {submit.isError && (
            <p className="mt-2 text-sm text-destructive">
              {submit.error instanceof Error ? submit.error.message : "Submission failed"}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Submissions</CardTitle>
          <CardDescription>Grading is added in Sprint 4 — new submissions are pending.</CardDescription>
        </CardHeader>
        <CardContent>
          <SubmissionList submissions={submissions} />
        </CardContent>
      </Card>
    </div>
  );
}
