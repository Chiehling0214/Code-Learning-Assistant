import Editor from "@monaco-editor/react";
import { Cloud, CloudOff, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import { AiTutorPanel } from "@/components/AiTutorPanel";
import { Markdown } from "@/components/Markdown";
import { GradingPanel, RunOutput } from "@/components/ResultPanel";
import { SubmissionList } from "@/components/SubmissionList";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useExercise,
  useExerciseDraft,
  useRun,
  useSaveExerciseDraft,
  useSubmission,
  useSubmissions,
  useSubmit,
} from "@/features/exercises/hooks";
import { useRecordLearningActivity } from "@/features/progress/hooks";

export function CodingExercisePage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const isPractice = searchParams.get("practice") === "1";
  const { data: exercise, isLoading, isError } = useExercise(id);
  const { data: submissions = [] } = useSubmissions(id);
  const draftQuery = useExerciseDraft(id);
  const saveDraftMutation = useSaveExerciseDraft(id);
  const { mutate: saveDraft } = saveDraftMutation;
  const submit = useSubmit(id);
  const run = useRun(id);
  const { mutate: recordActivity } = useRecordLearningActivity();
  const recordedActivity = useRef<string>();
  const loadedExercise = useRef<string>();

  const [code, setCode] = useState("");
  const [stdin, setStdin] = useState("");
  const [draftSavedAt, setDraftSavedAt] = useState<number>();
  const [activeSubmissionId, setActiveSubmissionId] = useState<string>();
  const { data: activeSubmission } = useSubmission(activeSubmissionId, id);

  // Prefer the newest copy between this browser and the signed-in account.
  useEffect(() => {
    if (!exercise || !draftQuery.isFetched || loadedExercise.current === exercise.id) return;
    loadedExercise.current = exercise.id;
    try {
      const rawDraft = localStorage.getItem(`cla:exercise-draft:${exercise.id}`);
      const draft = rawDraft ? JSON.parse(rawDraft) as { code?: string; savedAt?: number } : null;
      const localSavedAt = draft?.savedAt ?? 0;
      const accountSavedAt = draftQuery.data
        ? new Date(draftQuery.data.updated_at).getTime()
        : 0;
      if (typeof draft?.code === "string" && localSavedAt > accountSavedAt) {
        setCode(draft.code);
        setDraftSavedAt(localSavedAt);
      } else if (draftQuery.data) {
        setCode(draftQuery.data.code);
        setDraftSavedAt(accountSavedAt);
        localStorage.setItem(
          `cla:exercise-draft:${exercise.id}`,
          JSON.stringify({ code: draftQuery.data.code, savedAt: accountSavedAt }),
        );
      } else {
        setCode(exercise.starter_code);
        setDraftSavedAt(undefined);
      }
    } catch {
      setCode(draftQuery.data?.code ?? exercise.starter_code);
      setDraftSavedAt(undefined);
    }
  }, [draftQuery.data, draftQuery.isFetched, exercise]);

  useEffect(() => {
    if (!exercise || loadedExercise.current !== exercise.id) return;
    const timer = window.setTimeout(() => {
      const savedAt = Date.now();
      localStorage.setItem(
        `cla:exercise-draft:${exercise.id}`,
        JSON.stringify({ code, savedAt }),
      );
      setDraftSavedAt(savedAt);
      saveDraft(code);
    }, 600);
    return () => window.clearTimeout(timer);
  }, [code, exercise, saveDraft]);

  useEffect(() => {
    if (!isPractice && exercise?.id && recordedActivity.current !== exercise.id) {
      recordedActivity.current = exercise.id;
      recordActivity({ item_type: "exercise", item_id: exercise.id });
    }
  }, [exercise?.id, isPractice, recordActivity]);

  if (isLoading) {
    return <p className="text-muted-foreground">Loading exercise…</p>;
  }
  if (isError || !exercise) {
    return <p className="text-destructive">Exercise not found.</p>;
  }

  const resetStarterCode = () => {
    localStorage.removeItem(`cla:exercise-draft:${exercise.id}`);
    setCode(exercise.starter_code);
    setDraftSavedAt(undefined);
    saveDraft(exercise.starter_code);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="page-kicker">Coding exercise</p>
          <h1 className="page-heading">{exercise.title}</h1>
          <Markdown content={exercise.prompt} className="text-muted-foreground" />
        </div>
        <div className="grid w-full shrink-0 grid-cols-2 gap-2 sm:w-auto">
          <Button
            variant="outline"
            onClick={() => run.mutate({ code, stdin })}
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

      {exercise.sample_cases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sample tests</CardTitle>
            <CardDescription>
              Your program reads from stdin and must print exactly the expected output.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {exercise.sample_cases.map((sample, i) => (
              <div key={i} className="space-y-2 rounded-md border p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Example {i + 1}</span>
                  {sample.input.trim() && (
                    <Button variant="ghost" size="sm" onClick={() => setStdin(sample.input)}>
                      Use as input
                    </Button>
                  )}
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Input</p>
                  <pre className="overflow-x-auto rounded bg-muted p-2 text-xs">
                    <code>{sample.input || "(no input)"}</code>
                  </pre>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Expected output</p>
                  <pre className="overflow-x-auto rounded bg-muted p-2 text-xs">
                    <code>{sample.expected}</code>
                  </pre>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="text-lg">Editor</CardTitle>
              <CardDescription className="mt-1">
                Language: <span className="font-mono">{exercise.language}</span>
              </CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <span
                className="inline-flex items-center gap-1.5 text-xs text-muted-foreground"
                role="status"
                aria-live="polite"
              >
                {saveDraftMutation.isError
                  ? <CloudOff className="size-3.5" aria-hidden="true" />
                  : <Cloud className="size-3.5" aria-hidden="true" />}
                {saveDraftMutation.isPending
                  ? "Syncing…"
                  : saveDraftMutation.isError
                    ? "Saved on this device"
                    : draftSavedAt
                      ? "Saved to account"
                      : "Autosave on"}
              </span>
              <Button
                size="sm"
                variant="ghost"
                onClick={resetStarterCode}
                disabled={code === exercise.starter_code}
              >
                <RotateCcw className="size-4" /> Reset starter
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="overflow-hidden rounded-md border">
            <Editor
              height="min(55vh, 420px)"
              language={exercise.language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value ?? "")}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                automaticLayout: true,
                accessibilitySupport: "auto",
              }}
            />
          </div>
          <div>
            <p className="mb-1 text-sm font-medium">
              Input (stdin) <span className="font-normal text-muted-foreground">— sent to your program on Run</span>
            </p>
            <textarea
              aria-label="Program input"
              className="min-h-[64px] w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Type the input your program should read…"
              value={stdin}
              onChange={(e) => setStdin(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <AiTutorPanel exerciseId={id} code={code} />

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
          <SubmissionList
            submissions={submissions}
            onView={(submission) => setActiveSubmissionId(submission.id)}
            onRestore={(submission) => setCode(submission.code)}
          />
        </CardContent>
      </Card>
    </div>
  );
}
