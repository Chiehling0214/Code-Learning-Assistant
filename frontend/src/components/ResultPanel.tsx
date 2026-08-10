import { CheckCircle2, LockKeyhole, XCircle } from "lucide-react";

import type { GradingResult, RunResult, SubmissionStatus } from "@/features/exercises/hooks";

function Console({ label, text }: { label: string; text: string }) {
  if (!text) return null;
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">{text}</pre>
    </div>
  );
}

function TestValue({ label, value }: { label: string; value: string | undefined }) {
  if (value === undefined) return null;
  return (
    <div className="min-w-0 space-y-1">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.08em] text-muted-foreground">{label}</p>
      <pre className="max-h-32 overflow-auto rounded-md bg-muted/70 p-2 text-xs leading-5">
        {value || "(empty)"}
      </pre>
    </div>
  );
}

/** Output of a one-off Run (stdout/stderr or an unavailable message). */
export function RunOutput({ result }: { result: RunResult }) {
  if (result.error) {
    return <p className="text-sm text-amber-600">{result.error}</p>;
  }
  return (
    <div className="space-y-3">
      {result.status && (
        <p className="text-xs text-muted-foreground">
          Status: <span className="font-mono">{result.status}</span>
        </p>
      )}
      <Console label="stdout" text={result.stdout} />
      <Console label="stderr" text={result.stderr} />
      <Console label="compile output" text={result.compile_output ?? ""} />
      {!result.stdout && !result.stderr && <p className="text-sm text-muted-foreground">No output.</p>}
    </div>
  );
}

const VERDICT_TEXT: Record<SubmissionStatus, string> = {
  pending: "Grading…",
  passed: "All tests passed 🎉",
  failed: "Some tests failed",
  error: "Execution error",
};

const VERDICT_STYLE: Record<SubmissionStatus, string> = {
  pending: "text-amber-600",
  passed: "text-emerald-600",
  failed: "text-destructive",
  error: "text-destructive",
};

/** Verdict + per-test breakdown for a graded submission. */
export function GradingPanel({
  status,
  result,
}: {
  status: SubmissionStatus;
  result: GradingResult | null;
}) {
  return (
    <div className="space-y-3">
      <p className={`text-sm font-medium ${VERDICT_STYLE[status]}`}>
        {VERDICT_TEXT[status]}
        {result?.total != null && status !== "pending" && (
          <span className="ml-2 font-mono text-xs text-muted-foreground">
            {result.passed ?? 0}/{result.total}
          </span>
        )}
      </p>

      {result?.error && <p className="text-sm text-destructive">{result.error}</p>}
      <Console label="compile output" text={result?.compile_output ?? ""} />

      {result?.tests && result.tests.length > 0 && (
        <div className="space-y-3">
          {result.tests.map((test) => {
            const hidden = test.input === undefined && test.expected === undefined;
            return (
              <div key={test.index} className="rounded-lg border p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="inline-flex items-center gap-2 font-medium">
                    {test.passed ? (
                      <CheckCircle2 className="size-4 text-emerald-600" />
                    ) : (
                      <XCircle className="size-4 text-destructive" />
                    )}
                    Test {test.index + 1}
                    {hidden && (
                      <span className="inline-flex items-center gap-1 text-xs font-normal text-muted-foreground">
                        <LockKeyhole className="size-3" /> Hidden
                      </span>
                    )}
                  </span>
                  <span className={test.passed ? "text-emerald-600" : "text-destructive"}>
                    {test.passed ? "Passed" : (test.status ?? "Failed")}
                  </span>
                </div>
                {hidden ? (
                  <p className="mt-2 text-xs text-muted-foreground">
                    Input and expected output stay hidden for this grading case.
                  </p>
                ) : (
                  <div className="mt-3 grid gap-3 sm:grid-cols-3">
                    <TestValue label="Input" value={test.input} />
                    <TestValue label="Expected" value={test.expected} />
                    <TestValue label="Your output" value={test.actual} />
                  </div>
                )}
                {test.stderr && (
                  <div className="mt-3">
                    <TestValue label="Runtime error" value={test.stderr} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
