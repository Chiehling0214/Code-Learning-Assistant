import {
  Bell,
  CheckCircle2,
  LoaderCircle,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  useGenerationNotifications,
  useMarkGenerationSeen,
} from "@/features/curriculum/hooks";
import { useTracks } from "@/features/tracks/hooks";
import { cn } from "@/lib/utils";

function relativeTime(value: string) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export function GenerationNotifications({
  align = "right",
  side = "bottom",
}: {
  align?: "left" | "right";
  side?: "top" | "bottom";
}) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const { data } = useGenerationNotifications();
  const { data: tracks = [] } = useTracks();
  const markSeen = useMarkGenerationSeen();
  const jobs = data?.jobs ?? [];
  const unread = data?.unread_count ?? 0;

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  const openMenu = () => {
    const next = !open;
    setOpen(next);
    if (next) {
      jobs
        .filter((job) => (job.status === "done" || job.status === "error") && !job.seen_at)
        .forEach((job) => markSeen.mutate(job.id));
    }
  };

  return (
    <div className="relative" ref={root}>
      <button
        type="button"
        className="relative flex size-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-label={unread ? `Generation notifications, ${unread} unread` : "Generation notifications"}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={openMenu}
      >
        <Bell className="size-[18px]" aria-hidden="true" />
        {unread > 0 && (
          <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-destructive ring-2 ring-card" />
        )}
      </button>

      <span className="sr-only" aria-live="polite">
        {unread ? `${unread} course generation notifications unread` : ""}
      </span>

      {open && (
        <div
          role="menu"
          aria-label="Course generation updates"
          className={cn(
            "absolute z-50 w-[min(22rem,calc(100vw-2rem))] overflow-hidden rounded-xl border bg-card shadow-card",
            align === "left" ? "left-0" : "right-0",
            side === "top" ? "bottom-full mb-2" : "mt-2",
          )}
        >
          <div className="border-b px-4 py-3">
            <p className="text-sm font-semibold">Course updates</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              New course generation continues while you learn.
            </p>
          </div>
          <div className="max-h-80 overflow-y-auto p-2">
            {jobs.length === 0 ? (
              <p className="px-3 py-5 text-sm text-muted-foreground">No generation activity yet.</p>
            ) : (
              jobs.map((job) => {
                const language = tracks.find((track) => track.id === job.track_id)?.language_name;
                const active = job.status === "pending" || job.status === "running";
                const Icon = active
                  ? LoaderCircle
                  : job.status === "done"
                    ? CheckCircle2
                    : TriangleAlert;
                const body = (
                  <div className="flex min-h-16 gap-3 rounded-lg px-3 py-2.5 hover:bg-accent/65">
                    <Icon
                      className={cn(
                        "mt-0.5 size-4 shrink-0",
                        active && "animate-spin text-primary",
                        job.status === "done" && "text-emerald-700",
                        job.status === "error" && "text-destructive",
                      )}
                      aria-hidden="true"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">
                        {active
                          ? `Building ${language ?? "your"} courses`
                          : job.status === "done"
                            ? `${language ?? "New"} courses are ready`
                            : `Could not build ${language ?? "your"} courses`}
                      </p>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {active
                          ? `${job.completed} of ${job.total} lessons prepared`
                          : job.status === "error"
                            ? "Open the course to try again."
                            : "Open your library to see what’s next."}
                        {` · ${relativeTime(job.updated_at)}`}
                      </p>
                    </div>
                  </div>
                );
                return job.status === "done" ? (
                  <Link key={job.id} to="/library" role="menuitem" onClick={() => setOpen(false)}>
                    {body}
                  </Link>
                ) : (
                  <div key={job.id} role="menuitem">
                    {body}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
