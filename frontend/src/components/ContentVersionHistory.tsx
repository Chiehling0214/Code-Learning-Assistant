import { GitCompareArrows, History, RotateCcw } from "lucide-react";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { VersionCompareDialog } from "@/components/VersionCompareDialog";
import {
  useContentVersions,
  useRestoreContentVersion,
  type ContentVersion,
} from "@/features/admin/hooks";

type ItemType = "lesson" | "exercise" | "quiz";

export function ContentVersionHistory({
  itemType,
  itemId,
}: {
  itemType: ItemType;
  itemId: string;
}) {
  const history = useContentVersions(itemType, itemId);
  const restore = useRestoreContentVersion();
  const [compareVersion, setCompareVersion] = useState<ContentVersion | null>(null);
  const [restoreVersion, setRestoreVersion] = useState<ContentVersion | null>(null);

  return (
    <section className="rounded-lg border bg-card p-3">
      <div className="flex items-center gap-2">
        <History className="size-4 text-muted-foreground" />
        <p className="text-sm font-medium">Version history</p>
      </div>
      {restore.isSuccess && (
        <p role="status" className="mt-2 text-xs font-medium text-green-700">
          Previous version restored. The related lesson is pending review again.
        </p>
      )}
      {restore.isError && (
        <p role="alert" className="mt-2 text-xs text-destructive">
          {restore.error instanceof Error
            ? restore.error.message
            : "Could not restore this version."}
        </p>
      )}
      {history.isLoading ? (
        <p className="mt-2 text-xs text-muted-foreground">Loading versions…</p>
      ) : history.isError ? (
        <p className="mt-2 text-xs text-destructive">Could not load version history.</p>
      ) : !history.data?.versions.length ? (
        <p className="mt-2 text-xs text-muted-foreground">
          No saved versions yet. The current content will be saved before regeneration.
        </p>
      ) : (
        <ul className="mt-2 divide-y">
          {history.data.versions.slice(0, 8).map((version, index) => (
            <li key={version.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <div>
                <p className="text-xs font-medium">
                  Version {history.data.versions.length - index}
                </p>
                <p className="text-xs text-muted-foreground">
                  Saved {new Date(version.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    setCompareVersion(compareVersion?.id === version.id ? null : version)
                  }
                >
                  <GitCompareArrows className="size-3.5" />
                  {compareVersion?.id === version.id ? "Close comparison" : "Compare"}
                </Button>
                <Button variant="outline" size="sm" onClick={() => setRestoreVersion(version)}>
                  <RotateCcw className="size-3.5" /> Restore
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <VersionCompareDialog
        open={Boolean(compareVersion)}
        title={`${itemType[0].toUpperCase()}${itemType.slice(1)} version comparison`}
        savedAt={compareVersion ? new Date(compareVersion.created_at).toLocaleString() : ""}
        itemType={itemType}
        currentSnapshot={history.data?.current_snapshot ?? {}}
        savedSnapshot={compareVersion?.snapshot ?? {}}
        onClose={() => setCompareVersion(null)}
      />
      <ConfirmDialog
        open={Boolean(restoreVersion)}
        title="Restore this version?"
        description="The current content will be saved first, so this restore can be undone. The related lesson will return to Pending."
        confirmLabel="Restore version"
        pending={restore.isPending}
        onCancel={() => setRestoreVersion(null)}
        onConfirm={() => {
          if (!restoreVersion) return;
          restore.mutate(restoreVersion.id, {
            onSuccess: () => {
              setRestoreVersion(null);
              setCompareVersion(null);
            },
          });
        }}
      />
    </section>
  );
}
