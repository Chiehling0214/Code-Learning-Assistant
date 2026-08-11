import { ChevronDown, GitCompareArrows } from "lucide-react";
import { useState } from "react";

import { GradingPanel } from "@/components/ResultPanel";
import { Button } from "@/components/ui/button";
import type { Submission, SubmissionStatus } from "@/features/exercises/hooks";

const STATUS_STYLES: Record<SubmissionStatus, string> = {
  pending: "bg-amber-500/15 text-amber-700",
  passed: "bg-emerald-500/15 text-emerald-700",
  failed: "bg-destructive/15 text-destructive",
  error: "bg-destructive/15 text-destructive",
};

function StatusBadge({ status }: { status: SubmissionStatus }) {
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[status]}`}>
      {status}
    </span>
  );
}

function CodePane({
  title,
  code,
  otherCode,
}: {
  title: string;
  code: string;
  otherCode?: string;
}) {
  const lines = code.split("\n");
  const otherLines = otherCode?.split("\n");

  return (
    <div className="min-w-0">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
        {title}
      </p>
      <pre className="dark-code-selection max-h-80 overflow-auto rounded-lg border bg-[#18201c] py-3 text-xs leading-5 text-[#e4e9e5]">
        <code>
          {lines.map((line, index) => (
            <span
              key={`${index}-${line}`}
              className={`block min-w-max px-3 ${
                otherLines && line !== otherLines[index] ? "bg-amber-300/10" : ""
              }`}
            >
              <span className="mr-4 inline-block w-6 select-none text-right text-[#89958e]">
                {index + 1}
              </span>
              {line || " "}
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}

export function SubmissionList({ submissions }: { submissions: Submission[] }) {
  const [selectedId, setSelectedId] = useState<string>();
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const compared = compareIds
    .map((id) => submissions.find((submission) => submission.id === id))
    .filter((submission): submission is Submission => Boolean(submission));

  function toggleCompare(id: string) {
    setCompareIds((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id);
      return [...current.slice(-1), id];
    });
  }

  if (submissions.length === 0) {
    return <p className="text-sm text-muted-foreground">No submissions yet.</p>;
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Select an attempt to read its code and test result. Choose two attempts to compare them.
      </p>
      <ul className="space-y-2">
        {submissions.map((submission, index) => {
          const isSelected = selectedId === submission.id;
          const submittedAt = new Date(submission.created_at).toLocaleString();

          return (
            <li
              key={submission.id}
              className={`grid grid-cols-[1fr_auto] items-center overflow-hidden rounded-lg border transition-colors ${
                isSelected ? "border-primary/40 bg-muted/35" : "hover:bg-muted/25"
              }`}
            >
              <button
                type="button"
                className="flex min-w-0 items-center gap-3 px-3 py-3 text-left"
                onClick={() => setSelectedId(isSelected ? undefined : submission.id)}
                aria-expanded={isSelected}
                aria-controls={`submission-${submission.id}`}
              >
                <span className="w-8 shrink-0 font-mono text-xs text-muted-foreground">
                  {String(submissions.length - index).padStart(2, "0")}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium">{submittedAt}</span>
                  <span className="mt-0.5 block text-xs text-muted-foreground">
                    {submission.result?.total != null
                      ? `${submission.result.passed ?? 0}/${submission.result.total} tests passed`
                      : "Open submitted code"}
                  </span>
                </span>
                <StatusBadge status={submission.status} />
                <ChevronDown
                  className={`size-4 shrink-0 text-muted-foreground transition-transform ${
                    isSelected ? "rotate-180" : ""
                  }`}
                  aria-hidden="true"
                />
              </button>

              <label className="mr-3 inline-flex min-h-9 items-center gap-2 border-l pl-3 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={compareIds.includes(submission.id)}
                  onChange={() => toggleCompare(submission.id)}
                  aria-label={`Compare submission from ${submittedAt}`}
                />
                Compare
              </label>

              {isSelected && (
                <div
                  id={`submission-${submission.id}`}
                  className="col-span-2 space-y-5 border-t bg-background/70 p-4"
                >
                  <CodePane title="Submitted code" code={submission.code} />
                  <div>
                    <p className="mb-3 text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                      Test result
                    </p>
                    <GradingPanel status={submission.status} result={submission.result} />
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>

      {compared.length === 2 && (
        <div className="rounded-xl border bg-card p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-start gap-2">
              <GitCompareArrows className="mt-0.5 size-4 text-muted-foreground" aria-hidden="true" />
              <div>
                <p className="font-semibold">Attempt comparison</p>
                <p className="text-xs text-muted-foreground">Changed lines are highlighted.</p>
              </div>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setCompareIds([])}>
              Clear
            </Button>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <CodePane
              title={new Date(compared[0].created_at).toLocaleString()}
              code={compared[0].code}
              otherCode={compared[1].code}
            />
            <CodePane
              title={new Date(compared[1].created_at).toLocaleString()}
              code={compared[1].code}
              otherCode={compared[0].code}
            />
          </div>
        </div>
      )}
    </div>
  );
}
