import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

/** Shown when a free user hits a premium feature (402). */
export function UpgradePrompt({ message }: { message?: string }) {
  return (
    <div className="space-y-2 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
      <p>{message ?? "This is a premium feature."}</p>
      <Button asChild size="sm">
        <Link to="/subscription">Upgrade</Link>
      </Button>
    </div>
  );
}
