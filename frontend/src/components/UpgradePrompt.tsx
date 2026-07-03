import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

/**
 * Prompts an upgrade when a plan limit is hit. Pass `message` to always render a
 * static prompt, or `error` to render only when it is a 402 (using its message).
 */
export function UpgradePrompt({ message, error }: { message?: string; error?: unknown }) {
  if (error !== undefined && !(error instanceof ApiError && error.status === 402)) return null;
  const text =
    message ?? (error instanceof ApiError ? error.message : "This is a premium feature.");
  return (
    <div className="space-y-2 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
      <p>{text}</p>
      <Button asChild size="sm">
        <Link to="/subscription">Upgrade</Link>
      </Button>
    </div>
  );
}
