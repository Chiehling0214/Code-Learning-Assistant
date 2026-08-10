import { RotateCcw, SearchCode } from "lucide-react";
import { useState } from "react";

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
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}>
      {status}
    </span>
  );
}

function VersionPane({
  title,
  code,
  otherCode,
}: {
  title: string;
  code: string;
  otherCode: string;
}) {
  const lines = code.split("\n");
  const otherLines = otherCode.split("\n");
  return (
    <div className="min-w-0">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">{title}</p>
      <pre className="max-h-72 overflow-auto rounded-lg border bg-muted/50 p-2 text-xs leading-5">
        {lines.map((line, index) => (
          <span
            key={`${index}-${line}`}
            className={`block px-1 ${line !== otherLines[index] ? "bg-amber-500/15" : ""}`}
          >
            <span className="mr-3 inline-block w-6 select-none text-right text-muted-foreground/60">{index + 1}</span>
            {line || " "}
          </span>
        ))}
      </pre>
    </div>
  );
}

export function SubmissionList({
  submissions,
  onView,
  onRestore,
}: {
  submissions: Submission[];
  onView: (submission: Submission) => void;
  onRestore: (submission: Submission) => void;
}) {
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
      <p className="text-xs text-muted-foreground">
        Select two versions to compare changed lines. Restoring a version only updates the editor.
      </p>
      <ul className="space-y-2">
        {submissions.map((submission) => (
          <li
            key={submission.id}
            className="flex flex-wrap items-center gap-3 rounded-lg border px-3 py-3 text-sm"
          >
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input
                type="checkbox"
                checked={compareIds.includes(submission.id)}
                onChange={() => toggleCompare(submission.id)}
                aria-label={`Compare submission from ${new Date(submission.created_at).toLocaleString()}`}
              />
              Compare
            </label>
            <div className="min-w-[11rem] flex-1">
              <p>{new Date(submission.created_at).toLocaleString()}</p>
              {submission.result?.total != null && (
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {submission.result.passed ?? 0}/{submission.result.total} tests passed
                </p>
              )}
            </div>
            <StatusBadge status={submission.status} />
            <Button size="sm" variant="ghost" onClick={() => onView(submission)}>
              <SearchCode className="size-4" /> Result
            </Button>
            <Button size="sm" variant="outline" onClick={() => onRestore(submission)}>
              <RotateCcw className="size-4" /> Restore
            </Button>
          </li>
        ))}
      </ul>

      {compared.length === 2 && (
        <div className="rounded-xl border bg-card p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <p className="font-semibold">Version comparison</p>
              <p className="text-xs text-muted-foreground">Changed lines are highlighted.</p>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setCompareIds([])}>Clear</Button>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <VersionPane
              title={new Date(compared[0].created_at).toLocaleString()}
              code={compared[0].code}
              otherCode={compared[1].code}
            />
            <VersionPane
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
