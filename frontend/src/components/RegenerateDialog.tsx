import { useEffect, useState } from "react";

import { ConfirmDialog } from "@/components/ConfirmDialog";

type ItemType = "lesson" | "exercise" | "quiz";

export function RegenerateDialog({
  open,
  itemType,
  itemTitle,
  pending,
  confirmLabel = "Regenerate",
  onCancel,
  onConfirm,
}: {
  open: boolean;
  itemType: ItemType;
  itemTitle: string;
  pending: boolean;
  confirmLabel?: string;
  onCancel: () => void;
  onConfirm: (instructions: string) => void;
}) {
  const [instructions, setInstructions] = useState("");

  useEffect(() => {
    if (open) setInstructions("");
  }, [itemTitle, open]);

  return (
    <ConfirmDialog
      open={open}
      title={`Regenerate this ${itemType}?`}
      description={`This will replace “${itemTitle}” with new AI content and use AI quota. The original topic will stay the same, and the current version will be saved first.`}
      confirmLabel={confirmLabel}
      pending={pending}
      destructive
      onCancel={onCancel}
      onConfirm={() => onConfirm(instructions.trim())}
    >
      <label className="block" htmlFor="regeneration-instructions">
        <span className="text-sm font-medium">Adjustment instructions</span>
        <span className="ml-1 text-xs text-muted-foreground">Optional</span>
      </label>
      <textarea
        id="regeneration-instructions"
        value={instructions}
        maxLength={1000}
        rows={4}
        disabled={pending}
        onChange={(event) => setInstructions(event.target.value)}
        placeholder="For example: use a simpler analogy, emphasize edge cases, or make the distractors less obvious."
        className="mt-2 w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm leading-5 outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:ring-2 focus:ring-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
      />
      <div className="mt-1 flex items-start justify-between gap-3 text-xs text-muted-foreground">
        <p>The AI may adjust details, but it must preserve the existing topic.</p>
        <span className="shrink-0">{instructions.length}/1000</span>
      </div>
    </ConfirmDialog>
  );
}
