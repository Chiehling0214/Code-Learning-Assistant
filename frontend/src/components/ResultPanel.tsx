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
        <ul className="space-y-2">
          {result.tests.map((test) => (
            <li key={test.index} className="rounded-md border px-3 py-2 text-sm">
              <div className="flex items-center justify-between">
                <span>Test {test.index + 1}</span>
                <span className={test.passed ? "text-emerald-600" : "text-destructive"}>
                  {test.passed ? "passed" : (test.status ?? "failed")}
                </span>
              </div>
              {test.expected !== undefined && !test.passed && (
                <div className="mt-1 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <div>
                    expected: <span className="font-mono">{test.expected}</span>
                  </div>
                  <div>
                    got: <span className="font-mono">{test.actual}</span>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
