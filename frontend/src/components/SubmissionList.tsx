import type { Submission, SubmissionStatus } from "@/features/exercises/hooks";

const STATUS_STYLES: Record<SubmissionStatus, string> = {
  pending: "bg-amber-500/15 text-amber-600",
  passed: "bg-emerald-500/15 text-emerald-600",
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

export function SubmissionList({ submissions }: { submissions: Submission[] }) {
  if (submissions.length === 0) {
    return <p className="text-sm text-muted-foreground">No submissions yet.</p>;
  }
  return (
    <ul className="space-y-2">
      {submissions.map((submission) => (
        <li
          key={submission.id}
          className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
        >
          <span className="text-muted-foreground">
            {new Date(submission.created_at).toLocaleString()}
          </span>
          <StatusBadge status={submission.status} />
        </li>
      ))}
    </ul>
  );
}
