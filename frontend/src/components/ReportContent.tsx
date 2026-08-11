import { Flag } from "lucide-react";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

export function ReportContent({
  itemType,
  itemId,
}: {
  itemType: "lesson" | "exercise" | "quiz";
  itemId: string;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("incorrect");
  const [details, setDetails] = useState("");
  const [sent, setSent] = useState(false);
  const report = useMutation({
    mutationFn: () => apiFetch("/content/reports", {
      method: "POST",
      body: JSON.stringify({ item_type: itemType, item_id: itemId, reason, details }),
    }),
    onSuccess: () => {
      setDetails("");
      setOpen(false);
      setSent(true);
    },
  });

  if (!open) {
    return (
      <Button variant="ghost" size="sm" className="text-muted-foreground" disabled={sent} onClick={() => setOpen(true)}>
        <Flag className="size-3.5" /> {sent ? "Report sent" : `Report this ${itemType}`}
      </Button>
    );
  }
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-sm font-medium">What should we fix?</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-[12rem_1fr]">
        <select aria-label="Report reason" value={reason} onChange={(event) => setReason(event.target.value)} className="h-10 rounded-md border border-input bg-background px-3 text-sm">
          <option value="incorrect">Incorrect information</option>
          <option value="unclear">Unclear explanation</option>
          <option value="broken">Broken question or code</option>
          <option value="other">Other</option>
        </select>
        <textarea aria-label="Report details" value={details} onChange={(event) => setDetails(event.target.value)} maxLength={1000} placeholder="Add a short note so the reviewer can reproduce it" className="min-h-20 rounded-md border border-input bg-background px-3 py-2 text-sm" />
      </div>
      <div className="mt-3 flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>Cancel</Button>
        <Button size="sm" disabled={report.isPending} onClick={() => report.mutate()}>{report.isPending ? "Sending…" : "Send report"}</Button>
      </div>
      {report.isError && <p className="mt-2 text-xs text-destructive">Could not send the report. Try again.</p>}
    </div>
  );
}
